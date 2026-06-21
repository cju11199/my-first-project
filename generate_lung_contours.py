#!/usr/bin/env python3
"""
generate_lung_contours.py
Build the Lung SBRT CBCT case from the existing thoracic CT (spine3d_data.js):
inject a synthetic peripheral nodule into the right lower lobe and write
  - lung3d_data.js        (CT volume with the nodule baked in)   -> LUNG3D_VOL
  - lung3d_labels_data.js (Body / Lung / GTV / PTV label volume) -> LUNG3D_LABELS

The CT is a stylized atlas: density 0..255, HU = density*(2000/255) - 500.
Lung parenchyma sits near density 0 (air); a solid tumour ~ density 74.
"""
import re, base64, io, math
import numpy as np
from PIL import Image
from scipy import ndimage

SRC = 'spine3d_data.js'
def load_ct(path):
    js = open(path).read()
    dims = re.search(r'"dims":\s*\[(\d+),\s*(\d+),\s*(\d+)\]', js)
    DX, DY, DZ = int(dims[1]), int(dims[2]), int(dims[3])
    SP   = float(re.search(r'"spacingMm":\s*\[([0-9.]+)', js)[1])
    TPR  = int(re.search(r'"tilesPerRow":\s*(\d+)', js)[1])
    phys = re.search(r'"physMm":\s*\[([0-9.]+),\s*([0-9.]+),\s*([0-9.]+)\]', js)
    PHYS = [float(phys[1]), float(phys[2]), float(phys[3])]
    b64  = re.search(r"SPINE3D_VOL\.atlas\s*=\s*'data:image/png;base64,([A-Za-z0-9+/=\s]+)'", js)[1].replace('\n','').replace(' ','')
    atlas = np.array(Image.open(io.BytesIO(base64.b64decode(b64))).convert('L'), np.uint8)
    v = np.zeros((DZ, DY, DX), np.uint8)
    for z in range(DZ):
        tc = z % TPR; tr = z // TPR
        v[z] = atlas[tr*DY:tr*DY+DY, tc*DX:tc*DX+DX]
    return v, (DX, DY, DZ), SP, TPR, PHYS

ct, (DX, DY, DZ), SP, TPR, PHYS = load_ct(SRC)
print(f'CT {DX}x{DY}x{DZ}  sp={SP}  tpr={TPR}')

zz, yy, xx = np.mgrid[0:DZ, 0:DY, 0:DX]
def sph(cx, cy, cz, rmm):
    return ((xx-cx)*SP)**2 + ((yy-cy)*SP)**2 + ((zz-cz)*SP)**2 <= rmm*rmm

# ── peripheral RLL nodule (verified subpleural, air-density lung) ──────────────
CX, CY, CZ = 60, 106, 58
# Irregular spiculated mass (not a smooth sphere): overlapping lobules of varying size/offset,
# plus a few coarse pleural/vascular spicules tapering outward — a malignant-looking nodule.
gtv = np.zeros((DZ, DY, DX), bool)
for dx, dy, dz, r in [(0,0,0,6.6),(2,-1,0,5.2),(-2,2,1,5.4),(1,2,-1,4.6),
                      (-1,-2,2,4.4),(3,1,0,3.8),(-1,3,1,3.4),(2,-2,-2,3.4)]:
    gtv |= sph(CX+dx, CY+dy, CZ+dz, r)
for ux, uy, uz in [(-0.85,0.35,0.0),(0.25,-0.9,0.1),(0.55,0.6,-0.4),(-0.25,-0.5,0.75)]:
    nrm = (ux*ux+uy*uy+uz*uz)**0.5; ux, uy, uz = ux/nrm, uy/nrm, uz/nrm
    for smm, r in [(8,2.4),(11,1.9),(14,1.5)]:
        gtv |= sph(CX+ux*smm/SP, CY+uy*smm/SP, CZ+uz*smm/SP, r)

# Bake the tumour into the CT image, hard-edged (= the GTV mask exactly). The hard
# edge lets the moving CBCT reslice hide the planning-position lesion and redraw it
# at the drifted position cleanly (the "off-bone" differential-motion behaviour).
LESION_HU = 74.0
vol = ct.astype(np.float32)
vol[gtv] = LESION_HU
vol = np.clip(vol, 0, 255).astype(np.uint8)

# ── label structures ──────────────────────────────────────────────────────────
labels = np.zeros((DZ, DY, DX), np.uint8)
# Body: any tissue, filled, largest component
body = ndimage.binary_fill_holes(ct > 30)
lb, n = ndimage.label(body)
if n > 1:
    body = (lb == (np.argmax(ndimage.sum(body, lb, range(1, n+1))) + 1))
labels[body] |= 0x80

# Lungs: air (<40) inside the body, per-slice (airways connect to outside in 3D)
lung = np.zeros_like(body)
for z in range(DZ):
    bod = ndimage.binary_erosion(ndimage.binary_fill_holes(ct[z] > 30), iterations=3)
    dk  = ndimage.binary_opening((ct[z] < 40) & bod, iterations=1)
    lung[z] = dk
lung = ndimage.binary_opening(lung, iterations=1)
# keep the two largest air blobs (the lungs), drop bowel-gas/trachea specks
lb, n = ndimage.label(lung)
if n >= 1:
    sizes = ndimage.sum(lung, lb, range(1, n+1))
    keep = np.argsort(sizes)[::-1][:2] + 1
    lung = np.isin(lb, keep)
lung &= ~gtv                       # the tumour is not lung
labels[lung] |= 0x08

# GTV / PTV (PTV = GTV + 5 mm, ITV-style SBRT margin)
labels[gtv] |= 0x01
ptv = ndimage.binary_dilation(gtv, iterations=max(1, int(round(5.0/SP))))
labels[ptv] |= 0x02

gz, gy, gx = np.where(gtv)
iso = [int(round(gx.mean())), int(round(gy.mean())), int(round(gz.mean()))]
print(f'GTV {int(gtv.sum())} vox  PTV {int(ptv.sum())} vox  iso(voxel)={iso}')
for nm, bit in [('Body',0x80),('Lung',0x08),('GTV',0x01),('PTV',0x02)]:
    print(f'  {nm:5s}: {int(np.sum((labels & bit) > 0))} vox')

# ── encode a volume as a PNG atlas (z-major tiling, matches decodeVol) ─────────
def encode_atlas(volume, tpr):
    rows = math.ceil(DZ / tpr)
    out = np.zeros((rows*DY, tpr*DX), np.uint8)
    for z in range(DZ):
        tc = z % tpr; tr = z // tpr
        out[tr*DY:tr*DY+DY, tc*DX:tc*DX+DX] = volume[z]
    buf = io.BytesIO(); Image.fromarray(out, 'L').save(buf, format='PNG', compress_level=9)
    return base64.b64encode(buf.getvalue()).decode('ascii'), len(buf.getvalue())

OUT_TPR = TPR
ct_b64, ct_sz = encode_atlas(vol, OUT_TPR)
lbl_b64, lbl_sz = encode_atlas(labels, OUT_TPR)
print(f'CT atlas {ct_sz//1024}KB   label atlas {lbl_sz//1024}KB')

meta = (f'{{"dims": [{DX}, {DY}, {DZ}], "spacingMm": [{SP}, {SP}, {SP}], '
        f'"physMm": [{PHYS[0]}, {PHYS[1]}, {PHYS[2]}], "tilesPerRow": {OUT_TPR}, '
        f'"tileRows": {math.ceil(DZ/OUT_TPR)}, "boneThr": 0.42}}')
with open('lung3d_data.js', 'w') as f:
    f.write('// Thoracic CT (from the spine planning CT) with a synthetic RLL SBRT nodule baked in.\n')
    f.write('// dims=[x(LR),y(AP),z(SI)]  x0=patient-right  y0=anterior  z0=inferior\n')
    f.write(f'const LUNG3D_VOL={meta};\n')
    f.write(f"LUNG3D_VOL.atlas='data:image/png;base64,{ct_b64}';\n")

lbl_meta = (f'{{"dims": [{DX}, {DY}, {DZ}], "spacingMm": [{SP}, {SP}, {SP}], '
            f'"tilesPerRow": {OUT_TPR}, "bits": {{"gtv": 1, "ptv": 2, "lung": 8, "body": 128}}, '
            f'"isoIdx": [{iso[0]}, {iso[1]}, {iso[2]}]}}')
with open('lung3d_labels_data.js', 'w') as f:
    f.write('// Lung SBRT case labels: body / lungs from CT + synthetic RLL GTV and PTV(GTV+5mm)\n')
    f.write(f'const LUNG3D_LABELS={lbl_meta};\n')
    f.write(f"LUNG3D_LABELS.atlas='data:image/png;base64,{lbl_b64}';\n")
print('wrote lung3d_data.js + lung3d_labels_data.js')
