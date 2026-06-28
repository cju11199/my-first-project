#!/usr/bin/env python3
"""
generate_spine_2d.py
Build the 2D/2D **Spine SBRT** case: orthogonal-pair (AP + Lateral) bone-emphasised DRRs of the
thoracic spine, ray-summed from the SAME thoracic-spine planning CT the CBCT Spine SBRT case uses
(`spine3d_data.js`). The vertebral column is the bony landmark the student aligns; this is a plain
flat (tilt:null) orthogonal-pair match, so it rides the existing 2D/2D DRR infrastructure (no
parallax frames) exactly like the Femur case.

Unlike the femur/prostate 2D generators this needs **no network / DICOM** — it reuses the already
committed CBCT spine atlas. The atlas is a tiled PNG of a 0..255 density volume (same format the
trainer decodes in `decodeVol`): for z in 0..Z-1 the tile sits at column (z % tilesPerRow), row
(z // tilesPerRow), each tile is X(cols=LR) by Y(rows=AP). Axes: x = LR (x0 = patient-right),
y = AP (y0 = anterior), z = SI (z0 = inferior). Density→HU uses the trainer's model
`HU = density*(2000/255) - 500`.

Output: appended to image_data.js as
  const SPINE_AP_SRC  = "data:image/png;base64,...";   // rows=z(SI,sup at top), cols=x(LR)
  const SPINE_LAT_SRC = "data:image/png;base64,...";   // rows=z(SI,sup at top), cols=y(AP)
plus prints the iso fractional positions (T7 target) for CASES.spine.

Source: thoracic-spine planning CT in spine3d_data.js (the CBCT Spine SBRT case volume).
Needs numpy / pillow only.
"""
import re, io, base64, json
import numpy as np
from PIL import Image, ImageFilter

# ── Load the committed spine atlas (no network) ───────────────────────────────
with open('spine3d_data.js') as f:
    src = f.read()
META = json.loads(re.search(r'const SPINE3D_VOL=(\{.*?\});', src).group(1))
B64  = re.search(r"SPINE3D_VOL\.atlas='data:image/png;base64,([^']+)'", src).group(1)
X, Y, Z = META['dims']                              # x=LR, y=AP, z=SI
tpr = META['tilesPerRow']
sp = META['spacingMm'][0]                           # 2.2 mm isotropic
print(f'spine atlas {X}x{Y}x{Z}  iso spacing {sp} mm  zRange {META["zRange"]}')

# Decode the tiled atlas → density volume vol[z,y,x] (mirror trainer decodeVol exactly)
atlas = np.asarray(Image.open(io.BytesIO(base64.b64decode(B64))).convert('L'))
vol = np.empty((Z, Y, X), np.float32)
for z in range(Z):
    tc, tr = z % tpr, z // tpr
    vol[z] = atlas[tr*Y:tr*Y+Y, tc*X:tc*X+X]

# Density (0..255) → HU with the trainer's model, then HU → linear attenuation μ.
hu = vol * (2000.0/255.0) - 500.0

# ── Beer–Lambert DRR: integrate μ along each ray (same two-segment bone-emphasis as femur) ──
MU_W = 0.206            # water linear attenuation ~50 keV (1/cm)
BONE_GAIN = 3.2         # steepen HU→μ slope above 0 HU to emphasise cortical bone (spine is the landmark)
mu = np.where(hu < 0.0, MU_W * (1.0 + hu/1000.0),
                        MU_W * (1.0 + (hu/1000.0) * BONE_GAIN))
mu = np.clip(mu, 0.0, None)

def project(axis, dl_mm):
    A = mu.sum(axis=axis) * (dl_mm/10.0)            # ∫μ dl (cm) — Beer–Lambert line integral
    return A[::-1].astype(np.float32)               # flip z → superior at TOP (native res, unquantised)

# The 2.2 mm / 8-bit source caps true detail, so quality comes from how the line integral is
# rendered, not from inventing detail:
#  • upscale the FLOAT path-integral first (LANCZOS in 32-bit 'F'), so the soft-tissue→bone ramp
#    isn't posterised by the source's 8-bit density before we stretch it;
#  • the thoracic projection integrates ~30 cm of overlapping soft tissue (lungs/mediastinum sit
#    mid-grey, vertebrae barely separate), so a per-view PERCENTILE stretch windows the soft-tissue
#    baseline toward black and lets the vertebral column read as the bright bony landmark;
#  • an UNSHARP mask crisps the vertebral end-plates / pedicle edges the SBRT match keys on;
#  • render at a higher target height so the browser isn't re-upscaling a small image.
def render(A, target_h=768):
    h, w = A.shape
    tw = max(1, round(w * target_h / h))
    U = np.asarray(Image.fromarray(A, 'F').resize((tw, target_h), Image.LANCZOS), np.float32)
    lo, hi = np.percentile(U, 38), np.percentile(U, 99.6)
    d = np.clip((U - lo) / (hi - lo + 1e-6), 0, 1) ** 0.85
    im = Image.fromarray((d * 255).astype(np.uint8), 'L')
    im = im.filter(ImageFilter.UnsharpMask(radius=2.4, percent=135, threshold=1))
    buf = io.BytesIO(); im.save(buf, 'PNG', compress_level=9)
    return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode('ascii'), im.size

ap_url, ap_sz   = render(project(1, sp))   # sum over y(AP) → rows=z(SI), cols=x(LR)
lat_url, lat_sz = render(project(2, sp))   # sum over x(LR) → rows=z(SI), cols=y(AP)
print(f'AP png {ap_sz}  LAT png {lat_sz}')

# ── Isocenter = the T7 vertebral target (isoIdx from the spine LABEL volume) ──
with open('spine3d_labels_data.js') as f:
    LMETA = json.loads(re.search(r'const SPINE3D_LABELS=(\{.*?\});', f.read()).group(1))
ix, iy, iz = LMETA['isoIdx']                        # [x,y,z] voxel index of the T7 target
iso = {
  'ap':  {'x': round(ix/X, 3), 'y': round((Z - iz)/Z, 3)},   # AP: cols=x, rows=z(flipped, sup top)
  'lat': {'x': round(iy/Y, 3), 'y': round((Z - iz)/Z, 3)},   # LAT: cols=y, rows=z(flipped)
}
print(f'target {LMETA.get("target")}  isoIdx {LMETA["isoIdx"]}  → CASES.spine iso: {iso}')

# ── Append to image_data.js (idempotent: strip any prior spine block first) ──
with open('image_data.js') as f:
    cur = f.read()
cur = re.sub(r'\n// ── Spine SBRT 2D/2D case .*?const SPINE_LAT_SRC="[^"]*";\n',
             '', cur, flags=re.S)
block = (
    '\n// ── Spine SBRT 2D/2D case ─────────────────────────────────────────────────\n'
    '// AP + Lateral bone-emphasised DRRs ray-summed from the thoracic-spine planning CT\n'
    '// (the same volume as the CBCT Spine SBRT case, spine3d_data.js). Vertebral-body\n'
    '// bony match; iso sits at the T7 target. Built by generate_spine_2d.py.\n'
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
