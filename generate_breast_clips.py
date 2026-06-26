#!/usr/bin/env python3
"""
generate_breast_clips.py
Shrink + soften the surgical clips baked into the Breast CBCT case so they read as
small, stable fiducial marks instead of large, blooming, shimmery blobs.

In-place editor (re-runnable): reads the existing breast volume + label atlases,
finds the 5 clip clusters (label bit 64), and for each one:
  - erases the old hard-edged density-255 blob from the CT (fills the hole with the
    local breast-tissue density so nothing is left behind),
  - stamps a new compact clip at the same centroid: a small bright core with a soft
    (distance-ramped) feathered rim. The feather removes the 255-vs-tissue cliff that
    made the moving CBCT reslice shimmer, and keeps the bright footprint small so the
    marker no longer blooms past its true size under the breast window.
  - rewrites label bit 64 (clips) to the small new footprint so the white contour
    outline shrinks to match, and recomputes bit 128 (clips + 5 mm) from the new cores.

Reads/writes (same tiled-atlas format the trainer decodes):
  breast3d_data.js        -> BREAST3D_VOL    (CT, density 0..255, HU = density*2000/255 - 500)
  breast3d_labels_data.js -> BREAST3D_LABELS (bitfield: ... clips=64, clipmargin=128)

Needs numpy / scipy / pillow.  Browser-verify the result (canvas reslice/contours
are not headless-testable).
"""
import re, base64, io, math
import numpy as np
from PIL import Image
from scipy import ndimage

CT_FILE,  CT_VAR  = 'breast3d_data.js',        'BREAST3D_VOL'
LBL_FILE, LBL_VAR = 'breast3d_labels_data.js',  'BREAST3D_LABELS'
CLIP_BIT, MARGIN_BIT = 64, 128

# New clip geometry (mm). Surgical clips are ~2-3 mm marks; keep a bright core with a
# short feather so trilinear sampling stays smooth (stable) and the white footprint small.
PEAK      = 235.0    # bright core density (still clearly hyperdense; slightly under 255 to curb bloom)
R_CORE_MM = 0.9      # fully-bright core radius
R_EDGE_MM = 2.4      # density ramps PEAK->0 between R_CORE and R_EDGE (feathered rim)
MARGIN_MM = 5.0      # "clips + 5 mm" expansion (bit 128)

def load_atlas(path, var):
    js = open(path).read()
    dims = re.search(r'"dims":\s*\[(\d+),\s*(\d+),\s*(\d+)\]', js)
    DX, DY, DZ = int(dims[1]), int(dims[2]), int(dims[3])
    SP  = float(re.search(r'"spacingMm":\s*\[([0-9.]+)', js)[1])
    TPR = int(re.search(r'"tilesPerRow":\s*(\d+)', js)[1])
    b64 = re.search(var + r"\.atlas\s*=\s*'data:image/png;base64,([A-Za-z0-9+/=\s]+)'", js)[1]
    b64 = b64.replace('\n', '').replace(' ', '')
    atlas = np.array(Image.open(io.BytesIO(base64.b64decode(b64))).convert('L'), np.uint8)
    v = np.zeros((DZ, DY, DX), np.uint8)
    for z in range(DZ):
        tc = z % TPR; tr = z // TPR
        v[z] = atlas[tr*DY:tr*DY+DY, tc*DX:tc*DX+DX]
    return js, v, (DX, DY, DZ), SP, TPR

def encode_atlas(volume, DX, DY, DZ, tpr):
    rows = math.ceil(DZ / tpr)
    out = np.zeros((rows*DY, tpr*DX), np.uint8)
    for z in range(DZ):
        tc = z % tpr; tr = z // tpr
        out[tr*DY:tr*DY+DY, tc*DX:tc*DX+DX] = volume[z]
    buf = io.BytesIO(); Image.fromarray(out, 'L').save(buf, format='PNG', compress_level=9)
    return base64.b64encode(buf.getvalue()).decode('ascii'), len(buf.getvalue())

# ── load ──────────────────────────────────────────────────────────────────────
ct_js,  ct,  (DX, DY, DZ), SP, TPR = load_atlas(CT_FILE,  CT_VAR)
lbl_js, lbl, _,            _,  _   = load_atlas(LBL_FILE, LBL_VAR)
print(f'breast {DX}x{DY}x{DZ}  sp={SP}mm  tpr={TPR}')

clips = (lbl & CLIP_BIT) > 0
cc, n = ndimage.label(clips)
sizes = ndimage.sum(clips, cc, range(1, n+1)).astype(int)
print(f'old clips: {n} clusters, voxel sizes {sorted(sizes.tolist(), reverse=True)}')

ctf = ct.astype(np.float32)
zz, yy, xx = np.mgrid[0:DZ, 0:DY, 0:DX]

# ── per-cluster: erase old blob, stamp new compact clip ─────────────────────────
new_clip = np.zeros((DZ, DY, DX), bool)
for i in range(1, n+1):
    m = (cc == i)
    cz, cy, cx = (zz[m].mean(), yy[m].mean(), xx[m].mean())
    # fill the old footprint with the local tissue density (mean of a 2-voxel shell around it)
    shell = ndimage.binary_dilation(m, iterations=2) & ~m
    fill = float(ctf[shell].mean()) if shell.any() else 150.0
    ctf[m] = fill
    # new feathered clip at the same centroid
    d = np.sqrt(((xx-cx)*SP)**2 + ((yy-cy)*SP)**2 + ((zz-cz)*SP)**2)
    dens = np.zeros_like(ctf)
    core = d <= R_CORE_MM
    rim  = (d > R_CORE_MM) & (d < R_EDGE_MM)
    dens[core] = PEAK
    t = (R_EDGE_MM - d[rim]) / (R_EDGE_MM - R_CORE_MM)   # 1 at core edge -> 0 at outer edge
    dens[rim] = PEAK * (t*t*(3 - 2*t))                   # smoothstep ramp (soft, anti-shimmer)
    ctf = np.maximum(ctf, dens)                          # bake on top of tissue
    new_clip |= dens >= PEAK*0.5                         # contour footprint = bright half

ct_out = np.clip(ctf, 0, 255).astype(np.uint8)

# ── rewrite label bits 64 (clips) and 128 (clips + MARGIN_MM) ────────────────────
lbl_out = lbl.copy()
lbl_out &= ~np.uint8(CLIP_BIT | MARGIN_BIT)             # clear old clips + margin
lbl_out[new_clip] |= CLIP_BIT
margin = ndimage.binary_dilation(new_clip, iterations=max(1, int(round(MARGIN_MM / SP))))
lbl_out[margin] |= MARGIN_BIT

ncc, nn = ndimage.label(new_clip)
nsizes = ndimage.sum(new_clip, ncc, range(1, nn+1)).astype(int)
diam = [round((s*3/4/np.pi)**(1/3)*2*SP, 1) for s in sorted(nsizes.tolist(), reverse=True)]
print(f'new clips: {nn} clusters, voxel sizes {sorted(nsizes.tolist(), reverse=True)}  ~diam(mm) {diam}')
print(f'clip CT density: core={int(ct_out[new_clip].max())}  margin voxels={int((((lbl_out&MARGIN_BIT)>0)).sum())}')

# ── re-encode + write back, preserving each file's meta/header verbatim ──────────
ct_b64,  ct_sz  = encode_atlas(ct_out,  DX, DY, DZ, TPR)
lbl_b64, lbl_sz = encode_atlas(lbl_out, DX, DY, DZ, TPR)
ct_js  = re.sub(r"(" + CT_VAR  + r"\.atlas\s*=\s*'data:image/png;base64,)[A-Za-z0-9+/=\s]+(')",
                lambda mm: mm.group(1) + ct_b64  + mm.group(2), ct_js,  count=1)
lbl_js = re.sub(r"(" + LBL_VAR + r"\.atlas\s*=\s*'data:image/png;base64,)[A-Za-z0-9+/=\s]+(')",
                lambda mm: mm.group(1) + lbl_b64 + mm.group(2), lbl_js, count=1)
open(CT_FILE,  'w').write(ct_js)
open(LBL_FILE, 'w').write(lbl_js)
print(f'wrote {CT_FILE} ({ct_sz//1024}KB)  +  {LBL_FILE} ({lbl_sz//1024}KB)')
