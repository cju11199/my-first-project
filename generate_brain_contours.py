#!/usr/bin/env python3
"""
generate_brain_contours.py
Read the brain CT atlas from brain3d_data.js, segment key structures by CT
thresholding + morphology, and write brain3d_labels_data.js.

Structures and bit assignments:
  bit 1  (0x01) = GTV  (synthetic sphere, r=8mm,  plan-space centre)
  bit 2  (0x02) = PTV  (synthetic sphere, r=10mm, same centre)
  bit 4  (0x04) = Brainstem (threshold + morphology, posterior-inferior)
  bit 8  (0x08) = Brain (whole-brain mask from CT)
  bit 128(0x80) = Body (external patient contour)

Volume metadata (from brain3d_data.js):
  dims = [157, 183, 141]   x=LR, y=AP, z=SI
  spacingMm = 1.2
  tilesPerRow = 12
  x0=patient-right  y0=anterior  z0=inferior

GTV/PTV centre (from VOLCASE.brain.ptv.c):
  world coords (mm from volume centre): Wx=30, Wy=-20, Wz=22
  → voxel: sx=103, cy=74, az=88  (sagittal/coronal/axial index)
"""

import re, base64, io, math
import numpy as np
from PIL import Image
from scipy import ndimage

# ── 1. Load the brain CT atlas from the JS file ─────────────────────────────

JS_FILE   = 'brain3d_data.js'
OUT_FILE  = 'brain3d_labels_data.js'

with open(JS_FILE, 'r') as f:
    js = f.read()

# Extract metadata from the const line
dims_m     = re.search(r'"dims":\s*\[(\d+),\s*(\d+),\s*(\d+)\]', js)
spacing_m  = re.search(r'"spacingMm":\s*\[([0-9.]+)', js)
tpr_m      = re.search(r'"tilesPerRow":\s*(\d+)', js)
atlas_m    = re.search(r'BRAIN3D_VOL\.atlas\s*=\s*[\'"]data:image/png;base64,([A-Za-z0-9+/=\s]+)[\'"]', js)

if not atlas_m:
    # Try alternate pattern (all on one line)
    atlas_m = re.search(r'"atlas"\s*:\s*"data:image/png;base64,([A-Za-z0-9+/=]+)"', js)

DX, DY, DZ = int(dims_m.group(1)), int(dims_m.group(2)), int(dims_m.group(3))
SP          = float(spacing_m.group(1))
TPR         = int(tpr_m.group(1))

print(f'Volume: {DX}x{DY}x{DZ}  spacing={SP}mm  tilesPerRow={TPR}')

# Decode the PNG atlas -> 3D CT normalised [0,1]
b64data = atlas_m.group(1).replace('\n','').replace(' ','')
png_bytes = base64.b64decode(b64data)
atlas_img = Image.open(io.BytesIO(png_bytes)).convert('L')
atlas = np.array(atlas_img, dtype=np.float32) / 255.0

# Reconstruct volume  data[z, y, x]  (z-major, matching JS decodeVol)
tile_rows_needed = math.ceil(DZ / TPR)
vol = np.zeros((DZ, DY, DX), dtype=np.float32)
for z in range(DZ):
    tc = z % TPR
    tr = z // TPR
    ox = tc * DX
    oy = tr * DY
    vol[z] = atlas[oy:oy+DY, ox:ox+DX]

print(f'CT atlas decoded  min={vol.min():.3f}  max={vol.max():.3f}')

# ── 2. Build label volume ────────────────────────────────────────────────────

labels = np.zeros((DZ, DY, DX), dtype=np.uint8)

# Volume centre in voxel coords
cxv = (DX - 1) / 2.0   # sagittal  (x-axis)
cyv = (DY - 1) / 2.0   # coronal   (y-axis)
czv = (DZ - 1) / 2.0   # axial     (z-axis)

# GTV/PTV world-mm centre (from VOLCASE.brain.ptv.c = [30, -20, 22])
Wx, Wy, Wz = 30.0, -20.0, 22.0
# Convert to voxel indices
iso_sx = round(Wx / SP + cxv)   # sagittal → x  index = 103
iso_cy = round(Wy / SP + cyv)   # coronal  → y  index = 74
iso_az = round(Wz / SP + czv)   # axial    → z  index = 88

print(f'GTV/PTV voxel centre: x={iso_sx} y={iso_cy} z={iso_az}')

# ── 2a. Body: CT > ~5% (any tissue, excludes air background) ────────────────
body_thr = 0.08
body_raw = (vol > body_thr)
# Fill holes then erode slightly for a clean body contour
body_mask = ndimage.binary_fill_holes(body_raw)
# Keep only the largest connected component (removes table/coil artefacts)
lbl_arr, n = ndimage.label(body_mask)
if n > 1:
    sizes = ndimage.sum(body_mask, lbl_arr, range(1, n+1))
    body_mask = (lbl_arr == (np.argmax(sizes) + 1))
labels[body_mask] |= 0x80
print(f'Body:  {body_mask.sum()} voxels')

# ── 2b. Brain: soft-tissue threshold inside the skull ───────────────────────
# Brain tissue typically 0.25-0.55 normalised (HU ~30-80 if bone~255→0.85+)
# Use a generous range and then restrict to the skull cavity
brain_thr_lo, brain_thr_hi = 0.18, 0.62
brain_raw = (vol > brain_thr_lo) & (vol < brain_thr_hi) & body_mask

# Dilate slightly then keep the biggest blob (should be the brain parenchyma)
brain_dilated = ndimage.binary_dilation(brain_raw, iterations=2)
lbl_b, nb = ndimage.label(brain_dilated)
if nb > 1:
    sizes_b = ndimage.sum(brain_dilated, lbl_b, range(1, nb+1))
    brain_core = (lbl_b == (np.argmax(sizes_b) + 1))
else:
    brain_core = brain_dilated

# Intersect back with soft-tissue range to avoid bone edges
brain_mask = brain_core & brain_raw
# Fill internal holes (ventricles etc.)
brain_filled = ndimage.binary_fill_holes(brain_mask)
# Moderate erosion to pull away from skull boundary
brain_final = ndimage.binary_erosion(brain_filled, iterations=2)
labels[brain_final] |= 0x08
print(f'Brain: {brain_final.sum()} voxels')

# ── 2c. Brainstem: posterior-inferior, higher density than cortex ────────────
# Restrict to posterior-inferior region of the brain
# y > cyv+15 voxels (posterior), z < czv-8 voxels (inferior)
post_inf = np.zeros((DZ, DY, DX), dtype=bool)
z_max = int(czv - 8)    # inferior portion  (z0=inferior, so smaller z = more inferior)
y_min = int(cyv + 12)   # posterior portion (y0=anterior, so larger y = more posterior)
post_inf[:z_max, y_min:, :] = True

bs_candidate = brain_filled & post_inf
# Keep the largest connected component (brainstem + cerebellum cluster)
lbl_bs, nbs = ndimage.label(bs_candidate)
if nbs > 1:
    sizes_bs = ndimage.sum(bs_candidate, lbl_bs, range(1, nbs+1))
    bs_mask = (lbl_bs == (np.argmax(sizes_bs) + 1))
else:
    bs_mask = bs_candidate

# Restrict brainstem (exclude cerebellum) by further tightening to the central column
# x within ±18mm of centre
x_lo = int(cxv - 18/SP)
x_hi = int(cxv + 18/SP)
bs_column = np.zeros_like(bs_mask)
bs_column[:, :, x_lo:x_hi] = True
bs_mask = bs_mask & bs_column
bs_final = ndimage.binary_erosion(bs_mask, iterations=1)
labels[bs_final] |= 0x04
print(f'Brainstem: {bs_final.sum()} voxels')

# ── 2d. GTV sphere r=8mm ─────────────────────────────────────────────────────
gtv_r_mm  = 8.0
zz, yy, xx = np.mgrid[0:DZ, 0:DY, 0:DX]
dist_mm = np.sqrt(((xx - iso_sx)*SP)**2 + ((yy - iso_cy)*SP)**2 + ((zz - iso_az)*SP)**2)
gtv_mask = dist_mm <= gtv_r_mm
labels[gtv_mask] |= 0x01
print(f'GTV:  {gtv_mask.sum()} voxels  (r={gtv_r_mm}mm)')

# ── 2e. PTV sphere r=10mm ────────────────────────────────────────────────────
ptv_r_mm  = 10.0
ptv_mask  = dist_mm <= ptv_r_mm
labels[ptv_mask] |= 0x02
print(f'PTV:  {ptv_mask.sum()} voxels  (r={ptv_r_mm}mm)')

# ── 3. Encode label volume as PNG atlas ──────────────────────────────────────
# Layout: tilesPerRow=12, each tile is DX × DY
out_tpr     = 12
tile_rows   = math.ceil(DZ / out_tpr)
atlas_w     = out_tpr * DX
atlas_h     = tile_rows * DY

out_atlas   = np.zeros((atlas_h, atlas_w), dtype=np.uint8)
for z in range(DZ):
    tc = z % out_tpr
    tr = z // out_tpr
    ox = tc * DX
    oy = tr * DY
    out_atlas[oy:oy+DY, ox:ox+DX] = labels[z]   # labels[z] is (DY, DX)

out_img = Image.fromarray(out_atlas, mode='L')
buf = io.BytesIO()
out_img.save(buf, format='PNG', compress_level=9)
b64_out = base64.b64encode(buf.getvalue()).decode('ascii')

print(f'Label atlas: {atlas_w}x{atlas_h}  PNG size={len(buf.getvalue())//1024}KB')

# Verify label occupancy
for name, bit in [('Body',0x80),('Brain',0x08),('Brainstem',0x04),('PTV',0x02),('GTV',0x01)]:
    n = int(np.sum((labels & bit) > 0))
    print(f'  {name:12s}: {n:6d} voxels  ({100*n/(DX*DY*DZ):.1f}%)')

# ── 4. Write the JS file ──────────────────────────────────────────────────────
js_out = f"""// Brain structures: body/brain/brainstem from CT thresholding; GTV/PTV synthetic SRS spheres
const BRAIN3D_LABELS={{"dims": [{DX}, {DY}, {DZ}], "spacingMm": [{SP}, {SP}, {SP}], "tilesPerRow": {out_tpr}, "bits": {{"gtv": 1, "ptv": 2, "brainstem": 4, "brain": 8, "body": 128}}, "isoIdx": [{iso_sx}, {iso_cy}, {iso_az}]}};
BRAIN3D_LABELS.atlas='data:image/png;base64,{b64_out}';
"""

with open(OUT_FILE, 'w') as f:
    f.write(js_out)

print(f'\nWrote {OUT_FILE}  ({len(js_out)//1024}KB)')
