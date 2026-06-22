#!/usr/bin/env python3
"""
generate_prostate_2d.py
Build the 2D/2D prostate fiducial-match case: ray-sum the pelvis CT volume into
kV-style AP and Lateral radiographs (bone bright on black, like an OBI kV image),
and emit the planning fiducial-triad geometry the in-app least-squares 6DOF
solver needs. Writes prostate2d_data.js -> PROSTATE2D.

Patient axes from the volume: x = +Left (LR), y = +Posterior (AP), z = +Superior (SI).
"""
import re, base64, io, math
import numpy as np
from PIL import Image

def load_vol(path, var):
    js = open(path).read()
    DX, DY, DZ = [int(v) for v in re.search(r'"dims":\s*\[(\d+),\s*(\d+),\s*(\d+)\]', js).groups()]
    SP  = float(re.search(r'"spacingMm":\s*\[([0-9.]+)', js)[1])
    TPR = int(re.search(r'"tilesPerRow":\s*(\d+)', js)[1])
    b64 = re.search(var + r"\.atlas\s*=\s*'data:image/png;base64,([A-Za-z0-9+/=\s]+)'", js)[1].replace('\n','').replace(' ','')
    atlas = np.array(Image.open(io.BytesIO(base64.b64decode(b64))).convert('L'), np.float32)
    v = np.zeros((DZ, DY, DX), np.float32)
    for z in range(DZ):
        v[z] = atlas[(z//TPR)*DY:(z//TPR)*DY+DY, (z%TPR)*DX:(z%TPR)*DX+DX]
    return v, (DX, DY, DZ), SP

ct, (DX, DY, DZ), SP = load_vol('pelvis3d_data.js', 'PELVIS3D_VOL')
print(f'CT {DX}x{DY}x{DZ} sp={SP}')

# Attenuation ~ density; bone (high density) dominates the ray-sum. Emphasise bone with a
# soft power curve so cortical bone reads bright and bowel gas/soft tissue stay dark — kV look.
mu = np.clip(ct/255.0, 0, 1) ** 1.6

def project(axis):
    s = mu.sum(axis=axis)                 # AP: axis=1(y)->(z,x);  LAT: axis=2(x)->(z,y)
    s = s / (s.max() + 1e-6)
    s = s ** 0.85                          # gentle gamma for radiographic contrast
    img = (np.clip(s, 0, 1) * 255).astype(np.uint8)
    img = img[::-1]                        # flip z so superior is at the TOP of the image
    return img

ap  = project(1)   # rows=z(SI), cols=x(LR)
lat = project(2)   # rows=z(SI), cols=y(AP)

def upscale_png(arr, target_h=512):
    h, w = arr.shape
    im = Image.fromarray(arr, 'L').resize((round(w*target_h/h), target_h), Image.LANCZOS)
    buf = io.BytesIO(); im.save(buf, 'PNG', compress_level=9)
    return base64.b64encode(buf.getvalue()).decode('ascii'), im.size

ap_b64, ap_sz  = upscale_png(ap)
lat_b64, lat_sz = upscale_png(lat)
print(f'AP {ap_sz}  LAT {lat_sz}')

# Planning fiducial triad (3 gold seeds in the prostate) — same voxels as the CBCT case.
ISO = np.array([99, 76, 32], float)                 # iso voxel
# Spread in all 3 axes (base / mid / apex, varying L-R and A-P) so the triad is non-degenerate
# in BOTH projections — required for a well-conditioned 6DOF fit.
SEEDS = np.array([[95,72,37],[104,80,33],[98,74,27]], float)
# patient mm relative to iso: (Lat=+Left=x, AP=+Post=y, SI=+Sup=z)
fid_mm = ((SEEDS - ISO) * SP)
fid_list = [[round(float(c),2) for c in p] for p in fid_mm]
print('fiducials (Lat,AP,SI mm):', fid_list)

# physical extents of each projection (mm): AP = x(LR) x z(SI); LAT = y(AP) x z(SI)
phys = {'ap': [round(DX*SP,1), round(DZ*SP,1)], 'lat': [round(DY*SP,1), round(DZ*SP,1)]}
# iso fractional position within each image (x frac, y frac with y=0 at TOP=superior)
iso_frac = {
  'ap':  [round(float(ISO[0]/DX),4), round(float((DZ-ISO[2])/DZ),4)],
  'lat': [round(float(ISO[1]/DY),4), round(float((DZ-ISO[2])/DZ),4)],
}
print('phys', phys, 'iso_frac', iso_frac)

meta = (f'{{"physMm": {phys}, "isoFrac": {iso_frac}, "fiducials": {fid_list}, '
        f'"spacingMm": {SP}}}'.replace("'", '"'))
with open('prostate2d_data.js', 'w') as f:
    f.write('// 2D/2D prostate fiducial-match case: kV-style AP + Lateral pelvis radiographs (ray-sum of\n')
    f.write('// the pelvis CT) + planning fiducial-triad geometry (patient mm rel. iso) for the 6DOF solve.\n')
    f.write(f'const PROSTATE2D={meta};\n')
    f.write(f"PROSTATE2D.ap='data:image/png;base64,{ap_b64}';\n")
    f.write(f"PROSTATE2D.lat='data:image/png;base64,{lat_b64}';\n")
print('wrote prostate2d_data.js')
