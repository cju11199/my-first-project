#!/usr/bin/env python3
"""
generate_spine_2d.py
Build the 2D/2D **Spine SBRT** case: orthogonal-pair (AP + Lateral) bone-emphasised DRRs of the
thoracic spine, ray-summed from a **full-resolution diagnostic chest CT** (TCIA NSCLC-Radiogenomics
patient R01-076, the "THINS" series — 423 axial slices, 0.8 mm isotropic, Siemens B31f). The
vertebral column is the bony landmark the student aligns; this is a plain flat (tilt:null)
orthogonal-pair match, so it rides the existing 2D/2D DRR infrastructure (no parallax frames)
exactly like the Femur case.

History: this case originally reused the 2.2 mm / 8-bit CBCT spine atlas (spine3d_data.js); the
DRRs were soft because of that source. It was re-sourced to this ~0.8 mm chest CT for crisp,
diagnostic-quality vertebral detail. The 2D Spine case is therefore a DIFFERENT patient than the
CBCT Spine case — fine, they are independent cases.

Patient axes (HFS, IOP = identity): x = LR in column order, y = AP down the rows, z = SI up the
stack. We mask to the body (drop couch/air), crop in-plane to the torso bbox and z to a thoracic
window centred on the spine, then ray-sum AP (sum over y) and Lateral (sum over x).

Rendering (where DRR quality actually comes from): a true Beer–Lambert path integral (∫μ·dl,
two-segment HU→μ, bone-emphasised), then the float line-integral is LANCZOS-upscaled in 32-bit
BEFORE quantising, a per-view percentile contrast stretch windows the overlapping soft tissue
toward black so the vertebral column reads as the bright landmark, and an unsharp mask crisps the
end-plate/pedicle edges. Renders at 768 px.

Output: appended to image_data.js (idempotent — strips any prior spine block first) as
  const SPINE_AP_SRC  = "data:image/png;base64,...";   // rows=z(SI,sup at top), cols=x(LR)
  const SPINE_LAT_SRC = "data:image/png;base64,...";   // rows=z(SI,sup at top), cols=y(AP)
plus prints the iso fractional positions (mid-thoracic vertebra) for CASES.spine.

Licence: TCIA NSCLC-Radiogenomics, CC BY 3.0 — attribute doi:10.7937/k9/tcia.2017.7hs46erv.
Needs pydicom / numpy / scipy / pillow.
"""
import os, glob, io, base64
import numpy as np
import pydicom
from scipy import ndimage
from PIL import Image, ImageFilter

CTDIR = ('scratchpad/nsclc_spine/nsclc_radiogenomics/R01-076/'
         '1.3.6.1.4.1.14519.5.2.1.4334.1501.137912259338324725690543803674/'
         'CT_1.3.6.1.4.1.14519.5.2.1.4334.1501.201809319317668346803592237989')

# ── Load the CT volume (z,y,x) in HU ──────────────────────────────────────────
sl = [pydicom.dcmread(f) for f in glob.glob(os.path.join(CTDIR, '*.dcm'))]
sl.sort(key=lambda d: float(d.ImagePositionPatient[2]))           # inferior → superior
vol = np.stack([s.pixel_array.astype(np.float32) * float(s.RescaleSlope) + float(s.RescaleIntercept)
                for s in sl])
DZ, DY, DX = vol.shape
psy, psx = [float(v) for v in sl[0].PixelSpacing]                 # row(y), col(x) spacing mm
dz = abs(float(sl[1].ImagePositionPatient[2]) - float(sl[0].ImagePositionPatient[2]))
print(f'CT {DX}x{DY}x{DZ}  spacing x={psx:.3f} y={psy:.3f} z={dz:.3f} mm  HU[{vol.min():.0f},{vol.max():.0f}]')

# ── Body mask: drop the couch + air so the lateral isn't summed through the table ──
body = vol > -350
body = ndimage.binary_fill_holes(body)
lab, n = ndimage.label(body)
sizes = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1))
body = lab == (1 + int(np.argmax(sizes)))                         # largest blob = patient
vol = np.where(body, vol, -1000.0)

# ── Crop: in-plane to the torso bbox (+margin); z to a thoracic window on the spine ──
zz, yy, xx = np.where(body)
MARGIN = 8
x0, x1 = max(0, xx.min()-MARGIN), min(DX, xx.max()+MARGIN)
y0, y1 = max(0, yy.min()-MARGIN), min(DY, yy.max()+MARGIN)
# Thoracic window: trim the lowest/highest ~12% (shoulders/upper-abdomen) to centre on the T-spine.
z0 = int(DZ*0.10); z1 = int(DZ*0.90)
ct = vol[z0:z1, y0:y1, x0:x1].astype(np.float32)
print(f'crop x[{x0}:{x1}] y[{y0}:{y1}] z[{z0}:{z1}] → {ct.shape[::-1]}')

# ── Beer–Lambert DRR: integrate linear attenuation along each ray (two-segment HU→μ, bone-bright) ──
MU_W = 0.206            # water linear attenuation ~50 keV (1/cm)
BONE_GAIN = 3.0         # steepen HU→μ slope above 0 HU to emphasise cortical bone (the spine landmark)
hu = ct
mu = np.where(hu < 0.0, MU_W * (1.0 + hu/1000.0),
                        MU_W * (1.0 + (hu/1000.0) * BONE_GAIN))
mu = np.clip(mu, 0.0, None)

def project(axis, dl_mm):
    A = mu.sum(axis=axis) * (dl_mm/10.0)            # ∫μ dl (cm) — Beer–Lambert line integral
    return A[::-1].astype(np.float32)               # flip z → superior at TOP (native res, unquantised)

# Quality is wrung from the render, not invented: float-domain LANCZOS upscale (no posterisation),
# per-view percentile stretch (window soft tissue toward black), unsharp edge crisping, 768 px.
def render(A, target_h=768):
    h, w = A.shape
    tw = max(1, round(w * target_h / h))
    U = np.asarray(Image.fromarray(A, 'F').resize((tw, target_h), Image.LANCZOS), np.float32)
    lo, hi = np.percentile(U, 45), np.percentile(U, 99.7)
    d = np.clip((U - lo) / (hi - lo + 1e-6), 0, 1) ** 0.9
    im = Image.fromarray((d * 255).astype(np.uint8), 'L')
    im = im.filter(ImageFilter.UnsharpMask(radius=2.0, percent=120, threshold=1))
    buf = io.BytesIO(); im.save(buf, 'PNG', compress_level=9)
    return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode('ascii'), im.size

ap_url, ap_sz   = render(project(1, psy))   # sum over y(AP) → rows=z(SI), cols=x(LR)
lat_url, lat_sz = render(project(2, psx))   # sum over x(LR) → rows=z(SI), cols=y(AP)
print(f'AP png {ap_sz}  LAT png {lat_sz}')

# ── Isocenter = a mid-thoracic vertebral body (bone centroid in the posterior-central region) ──
CH, CY, CX = ct.shape
bone = ct > 250
# Restrict to the vertebral column: central 40% in x (LR), posterior 45% in y (AP).
col = np.zeros_like(bone)
col[:, int(CY*0.55):, int(CX*0.30):int(CX*0.70)] = bone[:, int(CY*0.55):, int(CX*0.30):int(CX*0.70)]
bz, by, bx = np.where(col)
iso_x, iso_y, iso_z = bx.mean(), by.mean(), CH/2.0               # mid-z = mid-thoracic level
iso = {
  'ap':  {'x': round(iso_x/CX, 3), 'y': round((CH - iso_z)/CH, 3)},   # AP: cols=x, rows=z(flipped, sup top)
  'lat': {'x': round(iso_y/CY, 3), 'y': round((CH - iso_z)/CH, 3)},   # LAT: cols=y, rows=z(flipped)
}
print(f'iso (mid-thoracic vertebra) → CASES.spine iso: {iso}')

# ── Append to image_data.js (idempotent: strip any prior spine block first) ──
import re
with open('image_data.js') as f:
    cur = f.read()
cur = re.sub(r'\n// ── Spine SBRT 2D/2D case .*?const SPINE_LAT_SRC="[^"]*";\n',
             '', cur, flags=re.S)
block = (
    '\n// ── Spine SBRT 2D/2D case ─────────────────────────────────────────────────\n'
    '// AP + Lateral bone-emphasised DRRs ray-summed from a full-resolution diagnostic chest CT\n'
    '// (TCIA NSCLC-Radiogenomics R01-076, 0.8 mm THINS series). Vertebral-body bony match; iso\n'
    '// sits at a mid-thoracic vertebra. Licence CC BY 3.0 — doi:10.7937/k9/tcia.2017.7hs46erv.\n'
    '// Built by generate_spine_2d.py.\n'
    f'const SPINE_AP_SRC="{ap_url}";\n'
    f'const SPINE_LAT_SRC="{lat_url}";\n'
)
with open('image_data.js', 'w') as f:
    f.write(cur + block)
print('wrote SPINE_AP_SRC / SPINE_LAT_SRC to image_data.js (idempotent)')

# QC stills for review
Image.open(io.BytesIO(base64.b64decode(ap_url.split(',')[1]))).save('/tmp/spine_ap_qc.png')
Image.open(io.BytesIO(base64.b64decode(lat_url.split(',')[1]))).save('/tmp/spine_lat_qc.png')
print('wrote /tmp/spine_ap_qc.png  /tmp/spine_lat_qc.png')
