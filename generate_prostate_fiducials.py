#!/usr/bin/env python3
"""
generate_prostate_fiducials.py
Build the Prostate (fiducial) CBCT case from the existing pelvis plan
(pelvis3d_data.js + pelvis3d_labels_data.js): implant 3 gold fiducial markers
inside the prostate and write
  - prostate3d_data.js        (CT volume with the seeds baked in)  -> PROSTATE3D_VOL
  - prostate3d_labels_data.js (pelvis structures + a fiducial bit)  -> PROSTATE3D_LABELS

Teaching point: the prostate (and its seeds) move relative to the bony pelvis
with bladder/rectal filling, so a bony match leaves the target off — you must
match the implanted fiducials. The seeds are baked HARD-EDGED and bright (gold,
density 255) so the off-bone reslice can hide the planning-position seeds and
redraw them at the drifted position.
"""
import re, base64, io, math
import numpy as np
from PIL import Image
from scipy import ndimage

def load_vol(path, var):
    js = open(path).read()
    dims = re.search(r'"dims":\s*\[(\d+),\s*(\d+),\s*(\d+)\]', js)
    DX, DY, DZ = int(dims[1]), int(dims[2]), int(dims[3])
    SP  = float(re.search(r'"spacingMm":\s*\[([0-9.]+)', js)[1])
    TPR = int(re.search(r'"tilesPerRow":\s*(\d+)', js)[1])
    b64 = re.search(var + r"\.atlas\s*=\s*'data:image/png;base64,([A-Za-z0-9+/=\s]+)'", js)[1].replace('\n','').replace(' ','')
    atlas = np.array(Image.open(io.BytesIO(base64.b64decode(b64))).convert('L'), np.uint8)
    v = np.zeros((DZ, DY, DX), np.uint8)
    for z in range(DZ):
        tc = z % TPR; tr = z // TPR
        v[z] = atlas[tr*DY:tr*DY+DY, tc*DX:tc*DX+DX]
    return v, (DX, DY, DZ), SP, TPR, js

ct,  (DX, DY, DZ), SP, TPR, ctjs  = load_vol('pelvis3d_data.js', 'PELVIS3D_VOL')
lbl, (LX, LY, LZ), LSP, LTPR, ljs = load_vol('pelvis3d_labels_data.js', 'PELVIS3D_LABELS')
phys = re.search(r'"physMm":\s*\[([0-9.]+),\s*([0-9.]+),\s*([0-9.]+)\]', ctjs)
PHYS = [float(phys[1]), float(phys[2]), float(phys[3])] if phys else [DX*SP, DY*SP, DZ*SP]
bits = eval(re.search(r'"bits":\s*(\{[^}]*\})', ljs)[1])
print(f'CT {DX}x{DY}x{DZ} sp={SP} tpr={TPR}  labels {LX}x{LY}x{LZ}  bits={bits}')

prostate = (lbl & bits['prostate']) > 0
pz, py, px = np.where(prostate)
cx, cy, cz = px.mean(), py.mean(), pz.mean()
print(f'prostate {prostate.sum()} vox  centroid(voxel)=({cx:.1f},{cy:.1f},{cz:.1f})  '
      f'x[{px.min()}-{px.max()}] y[{py.min()}-{py.max()}] z[{pz.min()}-{pz.max()}]')

# Place 3 seeds spread through the gland (classic base / apex / mid, offset laterally),
# each kept strictly inside an eroded prostate so they sit in soft tissue, not on an edge.
inner = ndimage.binary_erosion(prostate, iterations=2)
if inner.sum() < 30:
    inner = ndimage.binary_erosion(prostate, iterations=1)
xspan = (px.max()-px.min()); zspan = (pz.max()-pz.min())
cands = [
    (cx - 0.22*xspan, cy, cz + 0.28*zspan),   # left, superior (base)
    (cx + 0.24*xspan, cy, cz + 0.02*zspan),   # right, mid
    (cx - 0.05*xspan, cy, cz - 0.30*zspan),   # central, inferior (apex)
]
zz, yy, xx = np.mgrid[0:DZ, 0:DY, 0:DX]
def sph(c, rmm):
    return ((xx-c[0])*SP)**2 + ((yy-c[1])*SP)**2 + ((zz-c[2])*SP)**2 <= rmm*rmm
def snap_inside(c):
    ci = [int(round(c[0])), int(round(c[1])), int(round(c[2]))]
    if inner[ci[2], ci[1], ci[0]]:
        return ci
    iz, iy, ix = np.where(inner)
    d = (ix-c[0])**2 + (iy-c[1])**2 + (iz-c[2])**2
    j = np.argmin(d)
    return [int(ix[j]), int(iy[j]), int(iz[j])]

seeds = [snap_inside(c) for c in cands]
SEED_RMM = 2.0                      # tiny gold marker (single voxel per seed at 2.2 mm) — most seed-like
fid = np.zeros((DZ, DY, DX), bool)
for s in seeds:
    fid |= sph(s, SEED_RMM)
print('seed voxels:', [tuple(s) for s in seeds], ' fiducial vox:', int(fid.sum()))

# Bake the seeds into the CT as bright gold (density 255 ~ +1500 HU), hard-edged.
GOLD = 255
vol = ct.copy()
vol[fid] = GOLD

# Labels = pelvis structures + a fiducial bit (32 is free: prostate1 ptv2 bladder4 rectum8 sv16 body128).
FID_BIT = 32
labels = lbl.copy()
labels[fid] |= FID_BIT
bits = dict(bits); bits['fiducial'] = FID_BIT

iso = [int(round(cx)), int(round(cy)), int(round(cz))]
print('iso(voxel)=', iso, ' bits=', bits)

def encode_atlas(volume, tpr):
    rows = math.ceil(DZ / tpr)
    out = np.zeros((rows*DY, tpr*DX), np.uint8)
    for z in range(DZ):
        tc = z % tpr; tr = z // tpr
        out[tr*DY:tr*DY+DY, tc*DX:tc*DX+DX] = volume[z]
    buf = io.BytesIO(); Image.fromarray(out, 'L').save(buf, format='PNG', compress_level=9)
    return base64.b64encode(buf.getvalue()).decode('ascii'), len(buf.getvalue())

ct_b64, ct_sz   = encode_atlas(vol, TPR)
lbl_b64, lbl_sz = encode_atlas(labels, TPR)
print(f'CT atlas {ct_sz//1024}KB  label atlas {lbl_sz//1024}KB')

meta = (f'{{"dims": [{DX}, {DY}, {DZ}], "spacingMm": [{SP}, {SP}, {SP}], '
        f'"physMm": [{PHYS[0]}, {PHYS[1]}, {PHYS[2]}], "tilesPerRow": {TPR}, '
        f'"tileRows": {math.ceil(DZ/TPR)}, "boneThr": 0.42}}')
with open('prostate3d_data.js', 'w') as f:
    f.write('// Pelvis CT (the prostate plan) with 3 implanted gold fiducial markers baked in.\n')
    f.write('// dims=[x(LR),y(AP),z(SI)]  seeds = bright (density 255) hard-edged blobs in the prostate.\n')
    f.write(f'const PROSTATE3D_VOL={meta};\n')
    f.write(f"PROSTATE3D_VOL.atlas='data:image/png;base64,{ct_b64}';\n")

lbl_meta = (f'{{"dims": [{DX}, {DY}, {DZ}], "spacingMm": [{SP}, {SP}, {SP}], '
            f'"tilesPerRow": {TPR}, "bits": {{__BITS__}}'
            f'}}')
# build bits json explicitly to keep key order readable
bits_json = ', '.join(f'"{k}": {v}' for k, v in bits.items())
lbl_meta = (f'{{"dims": [{DX}, {DY}, {DZ}], "spacingMm": [{SP}, {SP}, {SP}], '
            f'"tilesPerRow": {TPR}, "bits": {{{bits_json}}}, '
            f'"isoIdx": [{iso[0]}, {iso[1]}, {iso[2]}]}}')
with open('prostate3d_labels_data.js', 'w') as f:
    f.write('// Prostate fiducial case labels: pelvis structures + 3 gold fiducial markers (bit 32).\n')
    f.write(f'const PROSTATE3D_LABELS={lbl_meta};\n')
    f.write(f"PROSTATE3D_LABELS.atlas='data:image/png;base64,{lbl_b64}';\n")
print('wrote prostate3d_data.js + prostate3d_labels_data.js')
