#!/usr/bin/env python3
"""
generate_femur_2d.py
Build the 2D/2D **Femur** case: orthogonal-pair (AP + Lateral) bone-emphasised DRRs of a
thigh / femur, ray-summed straight from a real extremity CT (TCIA Soft-tissue-Sarcoma
patient STS_004 — the same series the CBCT sarcoma case uses). The femur shaft is the bony
landmark the student aligns; this is a plain flat (tilt:null) orthogonal-pair match, so it
rides the existing 2D/2D DRR infrastructure (no parallax frames).

Patient axes (FFS, IOP = identity): x = +Left→Right in column order (col 0 = +x mm), wait —
ImagePositionPatient[0] is the x of col 0 and PixelSpacing>0, so col index increases with +x.
y = +Posterior down the rows, z = +Superior up the stack. The scan contains BOTH thighs, so
we crop in-plane to the affected limb (the one carrying the GTV) before projecting, otherwise
the Lateral (sum over x) would superimpose both legs.

Output: appended to image_data.js as
  const FEMUR_AP_SRC = "data:image/png;base64,...";   // rows=z(SI,sup at top), cols=x(LR)
  const FEMUR_LAT_SRC = "data:image/png;base64,...";   // rows=z(SI,sup at top), cols=y(AP)
plus prints the iso fractional positions for CASES.femur.

Licence: TCIA Soft-tissue-Sarcoma, CC BY 3.0 — attribute doi:10.7937/K9/TCIA.2015.7GO2GSKS.
Needs pydicom / numpy / scipy / pillow.
"""
import os, glob, io, base64
import numpy as np
import pydicom
from scipy import ndimage
from PIL import Image

SARC = ('/tmp/claude-0/-home-user-my-first-project/87e8f956-6de1-5b37-a5c5-46d435f5ff37/'
        'scratchpad/sts004/soft_tissue_sarcoma/STS_004/'
        '1.3.6.1.4.1.14519.5.2.1.5168.1900.124239320067253523699285035604')
CTDIR = os.path.join(SARC, 'CT_1.3.6.1.4.1.14519.5.2.1.5168.1900.952127023780097934747932279670')
RTDIR_GLOB = os.path.join(SARC, 'RTSTRUCT*', '*')

# ── Load the CT volume (z,y,x) in HU ──────────────────────────────────────────
sl = [pydicom.dcmread(f) for f in glob.glob(os.path.join(CTDIR, '*'))]
sl.sort(key=lambda d: float(d.ImagePositionPatient[2]))
vol = np.stack([s.pixel_array.astype(np.float32) * float(s.RescaleSlope) + float(s.RescaleIntercept)
                for s in sl])
DZ, DY, DX = vol.shape
ipp0 = np.array(sl[0].ImagePositionPatient, float)
psy, psx = [float(v) for v in sl[0].PixelSpacing]          # row(y), col(x) spacing mm
dz = abs(float(sl[1].ImagePositionPatient[2]) - float(sl[0].ImagePositionPatient[2]))
print(f'CT {DX}x{DY}x{DZ}  spacing x={psx:.3f} y={psy:.3f} z={dz:.3f} mm  HU[{vol.min():.0f},{vol.max():.0f}]')

# ── Find the affected limb from the GTV centroid (col index) ──────────────────
ds = pydicom.dcmread(sorted(glob.glob(RTDIR_GLOB))[0])
pts = np.vstack([np.array(c.ContourData, float).reshape(-1, 3)
                 for c in ds.ROIContourSequence[0].ContourSequence])
gtv_x_mm = pts[:, 0].mean()
gtv_col = int(round((gtv_x_mm - ipp0[0]) / psx))           # IOP identity → col = (x-x0)/psx
print(f'GTV centroid x={gtv_x_mm:.1f} mm → col {gtv_col}')

# ── Isolate the AFFECTED limb (single leg) ────────────────────────────────────
# Both thighs are in-frame. The bilateral projection is mirror-symmetric (ambiguous for
# 2D matching) and the Lateral superimposes both legs, so we split the volume at the
# low-density gap between the thighs and keep only the side carrying the GTV.
body = vol > -350
# Column-wise body coverage; the inter-leg gap is the minimum within the central 40% of x.
colcov = body.sum(axis=(0, 1)).astype(np.float32)
c0, c1 = int(DX * 0.30), int(DX * 0.70)
split = c0 + int(np.argmin(colcov[c0:c1]))
print(f'inter-leg split at col {split} (GTV col {gtv_col})')
if gtv_col < split:
    xlo, xhi = 0, split
else:
    xlo, xhi = split, DX

# Restrict to the affected side, then crop in-plane to that limb's body bbox + margin.
side = body.copy(); side[:, :, :xlo] = False; side[:, :, xhi:] = False
lab, n = ndimage.label(side)
sizes = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1))
limb = lab == (1 + int(np.argmax(sizes)))                  # largest blob on the affected side
zz, yy, xx = np.where(limb)
MARGIN = 12
x0, x1 = max(0, xx.min() - MARGIN), min(DX, xx.max() + MARGIN)
y0, y1 = max(0, yy.min() - MARGIN), min(DY, yy.max() + MARGIN)

# Crop z to the FEMUR / thigh: a generous window centred on the GTV (hip→knee span), so the
# case shows the femoral shaft + lesion region rather than the whole leg down to the foot.
gtv_zsup = int(round((pts[:, 2].max() - ipp0[2]) / dz))    # +z = superior = higher slice idx
gtv_zinf = int(round((pts[:, 2].min() - ipp0[2]) / dz))
PAD = int(round(130 / dz))                                 # ~13 cm beyond the GTV each way
z0, z1 = max(0, gtv_zinf - PAD), min(DZ, gtv_zsup + PAD + 1)

ct = vol[z0:z1, y0:y1, x0:x1].copy()
msk = limb[z0:z1, y0:y1, x0:x1]
ct[~msk] = -1000                                           # blank everything outside the limb
print(f'crop x[{x0}:{x1}] y[{y0}:{y1}] z[{z0}:{z1}] → {ct.shape[::-1]}')

# ── Bone-emphasised attenuation → ray-sum DRRs (cortical bone bright on black) ──
# Soft tissue ~40 HU, cortical bone 300-1500 HU. A windowed power curve makes the femur read
# bright while muscle/fat stay dark — like a kV / DRR bone image.
mu = np.clip((ct + 200.0) / 1700.0, 0, 1) ** 1.8

def project(axis):
    s = mu.sum(axis=axis)                                  # AP: axis=1(y)→(z,x); LAT: axis=2(x)→(z,y)
    s = s / (s.max() + 1e-6)
    s = s ** 0.8                                           # gentle gamma for radiographic contrast
    img = (np.clip(s, 0, 1) * 255).astype(np.uint8)
    return img[::-1]                                       # flip z → superior at TOP

ap  = project(1)   # rows=z(SI), cols=x(LR)
lat = project(2)   # rows=z(SI), cols=y(AP)

def to_png_dataurl(arr, target_h=560):
    h, w = arr.shape
    im = Image.fromarray(arr, 'L').resize((max(1, round(w * target_h / h)), target_h), Image.LANCZOS)
    buf = io.BytesIO(); im.save(buf, 'PNG', compress_level=9)
    return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode('ascii'), im.size

ap_url, ap_sz   = to_png_dataurl(ap)
lat_url, lat_sz = to_png_dataurl(lat)
print(f'AP png {ap_sz}  LAT png {lat_sz}')

# ── Isocenter = femur bone centroid within the crop (fractional, y=0 at TOP=superior) ──
bone = ct > 300
bz, by, bx = np.where(bone)
iso_col, iso_row, iso_slc = bx.mean(), by.mean(), bz.mean()     # within cropped volume
ch, cw = ct.shape[0], ct.shape[2]                              # z, x sizes (cropped)
iso = {
  'ap':  {'x': round(float(iso_col) / ct.shape[2], 3), 'y': round(float((ct.shape[0] - iso_slc) / ct.shape[0]), 3)},
  'lat': {'x': round(float(iso_row) / ct.shape[1], 3), 'y': round(float((ct.shape[0] - iso_slc) / ct.shape[0]), 3)},
}
print('CASES.femur iso:', iso)

# ── Append to image_data.js ───────────────────────────────────────────────────
with open('image_data.js', 'a') as f:
    f.write('\n// ── Femur 2D/2D case ─────────────────────────────────────────────────────\n')
    f.write('// AP + Lateral bone-emphasised DRRs ray-summed from a real thigh CT (TCIA\n')
    f.write('// Soft-tissue-Sarcoma STS_004, the same series as the CBCT sarcoma case).\n')
    f.write('// Licence CC BY 3.0 — attribute doi:10.7937/K9/TCIA.2015.7GO2GSKS.\n')
    f.write(f'const FEMUR_AP_SRC="{ap_url}";\n')
    f.write(f'const FEMUR_LAT_SRC="{lat_url}";\n')
print('appended FEMUR_AP_SRC / FEMUR_LAT_SRC to image_data.js')

# QC stills for review
Image.open(io.BytesIO(base64.b64decode(ap_url.split(',')[1]))).save('/tmp/femur_ap_qc.png')
Image.open(io.BytesIO(base64.b64decode(lat_url.split(',')[1]))).save('/tmp/femur_lat_qc.png')
print('wrote /tmp/femur_ap_qc.png  /tmp/femur_lat_qc.png')
