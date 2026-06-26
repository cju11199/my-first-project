#!/usr/bin/env python3
"""
generate_vs_mr.py
Build the MR Acoustic Neuroma (vestibular schwannoma) SRS case from a TCIA
Vestibular-Schwannoma-SEG patient (contrast T1 GammaKnife planning MR + RTSTRUCT)
and write
  - acousticmr3d_data.js        (MR volume atlas)             -> ACOUSTICMR3D_VOL
  - acousticmr3d_labels_data.js (tumor + cochlea + skull)     -> ACOUSTICMR3D_LABELS

Same tiled-atlas format the trainer already consumes for the CT/CBCT cases, but the
volume is MR, not CT: there is no HU/Rescale model, so intensity is percentile-
normalised to 0..255 (the trainer treats the atlas as generic grayscale; an `mr`
flag on the VOLCASE entry hides the CT-only bone/HU window presets). The "moving"
image is synthesised by reslicing the same MR through a hidden 6DOF offset, as for
every volumetric case — so a daily image series is not needed.

DATA (NCI Imaging Data Commons public bucket, reachable where TCIA itself is blocked):
  pip install idc-index pydicom numpy scipy pillow
  from idc_index import index; c = index.IDCClient()
  # collection vestibular_schwannoma_seg, patient VS-SEG-001:
  #   download the t1 MR series + the "ROIs in MR T1 Gd" RTSTRUCT, then:
  python generate_vs_mr.py --mr /path/to/MR_series_dir --rtstruct /path/to/RTSTRUCT_T1Gd.dcm

Licence CC BY 4.0 (commercial use OK with attribution) — Shapey, J. et al.,
Vestibular-Schwannoma-SEG, The Cancer Imaging Archive, doi:10.7937/TCIA.9YTJ-5Q73.

TEACHING POINT: intracranial SRS to a vestibular schwannoma at the IAC/CPA — a tight
(1 mm / 1°) match on the enhancing tumour while sparing the cochlea.
"""
import argparse, os, re, io, base64, math, glob
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

try:
    import pydicom
except ImportError:
    raise SystemExit("pydicom required:  pip install pydicom numpy scipy pillow")

TARGET_XY      = 200    # longest-axis resample size (px)
TILES_PER_ROW  = 10
CROP_MARGIN_MM = 8      # margin around the skull/body bbox (whole head in frame, minimal air)

# Display normalisation: the trainer maps atlas density 0..255 -> "HU" = density*(2000/255)-500
# for the window/level widget. We are not real HU, but keep the same map so the existing window
# code works; the VOLCASE `win` is tuned to this normalisation (see trainer wiring).
def normalize_mr(vol):
    lo, hi = np.percentile(vol, 1.0), np.percentile(vol, 99.5)
    d = (vol - lo) / max(1e-3, (hi - lo))
    return np.clip(d * 255.0, 0, 255).astype(np.uint8)

# Fixed bit layout consumed by trainer.html's ACOUSTICMR_STRUCTS (uint8).
STRUCT_BITS = {'body': 1, 'tumor': 2, 'cochlea': 4}
ROI_ALIASES = [
    ('cochlea', 'cochlea'),
    ('tv', 'tumor'), ('gtv', 'tumor'), ('tumor', 'tumor'), ('tumour', 'tumor'),
    ('schwannoma', 'tumor'), ('vol2016', None),   # Vol2016 = alt tumour delineation -> skip
    ('skull', 'body'), ('external', 'body'), ('body', 'body'),
]
def map_roi(name):
    n = re.sub(r'[^a-z0-9]', '', name.lower())
    for sub, key in ROI_ALIASES:
        if re.sub(r'[^a-z0-9]', '', sub) in n:
            return key
    return None

def load_mr(mr_dir):
    files = [f for f in glob.glob(os.path.join(mr_dir, '**', '*'), recursive=True) if os.path.isfile(f)]
    sl = []
    for f in files:
        try:
            ds = pydicom.dcmread(f, force=True)
        except Exception:
            continue
        if getattr(ds, 'Modality', '') != 'MR' or not hasattr(ds, 'ImagePositionPatient'):
            continue
        sl.append(ds)
    if not sl:
        raise SystemExit(f"No MR slices under {mr_dir}")
    sl.sort(key=lambda s: float(s.ImagePositionPatient[2]))
    ref = sl[0]
    ny, nx = int(ref.Rows), int(ref.Columns)
    px, py = float(ref.PixelSpacing[1]), float(ref.PixelSpacing[0])
    z = [float(s.ImagePositionPatient[2]) for s in sl]
    dz = float(np.median(np.diff(z))) if len(z) > 1 else float(getattr(ref, 'SliceThickness', 1))
    vol = np.stack([s.pixel_array.astype(np.float32) for s in sl])   # raw MR intensity
    print(f"MR: {nx}x{ny}x{len(sl)}  in-plane {px:.3f}x{py:.3f} mm  dz {abs(dz):.3f} mm  "
          f"intensity p1={np.percentile(vol,1):.0f} p99.5={np.percentile(vol,99.5):.0f}")
    return dict(v=vol, nx=nx, ny=ny, nz=len(sl), px=px, py=py, dz=abs(dz),
                ox=float(ref.ImagePositionPatient[0]), oy=float(ref.ImagePositionPatient[1]), z0=z[0])

def rasterize(rt_path, g):
    rt = pydicom.dcmread(rt_path, force=True)
    names = {r.ROINumber: r.ROIName for r in rt.StructureSetROISequence}
    nz, ny, nx = g['nz'], g['ny'], g['nx']
    masks = {k: np.zeros((nz, ny, nx), bool) for k in STRUCT_BITS}
    mapped = {}
    for roi in rt.ROIContourSequence:
        nm = names.get(roi.ReferencedROINumber, '?'); key = map_roi(nm); mapped[nm] = key
        if key is None or not hasattr(roi, 'ContourSequence'):
            continue
        for c in roi.ContourSequence:
            pts = np.array(c.ContourData, float).reshape(-1, 3)
            zi = int(round((pts[:, 2].mean() - g['z0']) / g['dz']))
            if not (0 <= zi < nz):
                continue
            col = (pts[:, 0] - g['ox']) / g['px']; row = (pts[:, 1] - g['oy']) / g['py']
            img = Image.new('L', (nx, ny), 0)
            ImageDraw.Draw(img).polygon(list(zip(col, row)), outline=1, fill=1)
            masks[key][zi] |= np.array(img, bool)
    print("ROI mapping:")
    for nm, key in sorted(mapped.items()):
        print(f"   {nm:24s} -> {key}")
    return masks

def encode_atlas(vol, OX, OY, OZ, tpr):
    rows = math.ceil(OZ / tpr)
    out = np.zeros((rows*OY, tpr*OX), np.uint8)
    for z in range(OZ):
        tc, tr = z % tpr, z // tpr
        out[tr*OY:tr*OY+OY, tc*OX:tc*OX+OX] = vol[z]
    buf = io.BytesIO(); Image.fromarray(out, 'L').save(buf, format='PNG', compress_level=9)
    return base64.b64encode(buf.getvalue()).decode('ascii'), len(buf.getvalue()), rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mr', required=True, help='contrast-T1 MR series directory')
    ap.add_argument('--rtstruct', required=True, help='RTSTRUCT drawn on that MR')
    args = ap.parse_args()

    g = load_mr(args.mr)
    masks = rasterize(args.rtstruct, g)
    if not masks['tumor'].any():
        raise SystemExit("no tumour ROI matched — check ROI_ALIASES against the printed ROI list")
    dens = normalize_mr(g['v'])
    spz, spy, spx = g['dz'], g['py'], g['px']

    # crop to the WHOLE HEAD (skull/body bounding box + a small margin) so the entire head is in
    # frame, not just the IAC/CPA tumour (ultracode-judged "skullbbox" framing). Fall back to a
    # thresholded head mask if no skull/body ROI is present.
    head = masks['body'] if masks['body'].any() else (dens > 28)
    zz, yy, xx = np.where(head)
    mz, my, mx = CROP_MARGIN_MM/spz, CROP_MARGIN_MM/spy, CROP_MARGIN_MM/spx
    z0, z1 = max(0, int(zz.min()-mz)), min(g['nz'], int(zz.max()+mz)+1)
    y0, y1 = max(0, int(yy.min()-my)), min(g['ny'], int(yy.max()+my)+1)
    x0, x1 = max(0, int(xx.min()-mx)), min(g['nx'], int(xx.max()+mx)+1)
    print(f"crop to head box z[{z0}:{z1}] y[{y0}:{y1}] x[{x0}:{x1}] of {g['nz']}x{g['ny']}x{g['nx']}")
    dens = dens[z0:z1, y0:y1, x0:x1]
    masks = {k: m[z0:z1, y0:y1, x0:x1] for k, m in masks.items()}
    CZ, CY, CX = dens.shape

    # isotropic resample
    phys = [CX*spx, CY*spy, CZ*spz]
    iso_sp = max(phys) / TARGET_XY
    OX = max(1, round(phys[0]/iso_sp)); OY = max(1, round(phys[1]/iso_sp)); OZ = max(1, round(phys[2]/iso_sp))
    zoom = (OZ/CZ, OY/CY, OX/CX)
    print(f"resample -> {OX}x{OY}x{OZ}  iso {iso_sp:.3f} mm  phys {[round(p) for p in phys]}")
    vol_d = np.clip(ndimage.zoom(dens.astype(np.float32), zoom, order=1), 0, 255).astype(np.uint8)
    rmasks = {k: (ndimage.zoom(m.astype(np.float32), zoom, order=1) > 0.5) if m.any()
                 else np.zeros((OZ, OY, OX), bool) for k, m in masks.items()}
    # the cochlea is tiny (~3 mm); at whole-head resolution it's only a few voxels, so dilate 1
    # voxel for a legible contour (it's a key SRS avoidance structure).
    if rmasks['cochlea'].any():
        rmasks['cochlea'] = ndimage.binary_dilation(rmasks['cochlea'], iterations=1)

    labels = np.zeros((OZ, OY, OX), np.uint8); bits = {}
    for k, bit in STRUCT_BITS.items():
        if rmasks[k].any():
            labels[rmasks[k]] |= bit; bits[k] = bit
    tz, ty, tx = np.where(rmasks['tumor'])
    iso = [int(round(tx.mean())), int(round(ty.mean())), int(round(tz.mean()))]
    print(f"iso(voxel)={iso}  bits={bits}  tumour {int(rmasks['tumor'].sum())} vox  "
          f"cochlea {int(rmasks['cochlea'].sum())} vox")

    ct_b64, ct_sz, rows = encode_atlas(vol_d, OX, OY, OZ, TILES_PER_ROW)
    lbl_b64, lbl_sz, _  = encode_atlas(labels, OX, OY, OZ, TILES_PER_ROW)
    print(f"MR atlas {ct_sz//1024} KB   label atlas {lbl_sz//1024} KB")

    ATTRIB = ('// Source: TCIA Vestibular-Schwannoma-SEG (via NCI Imaging Data Commons, s3://idc-open-data).\n'
              '// Licence: CC BY 4.0 (commercial use permitted with attribution).\n'
              '// Attribution: Shapey, J. et al., The Cancer Imaging Archive, doi:10.7937/TCIA.9YTJ-5Q73.\n'
              '// De-identified contrast-T1 planning MR, cropped to the IAC/CPA tumour + percentile-normalised.\n')
    meta = (f'{{"dims": [{OX}, {OY}, {OZ}], "spacingMm": [{iso_sp:.4f}, {iso_sp:.4f}, {iso_sp:.4f}], '
            f'"physMm": [{OX*iso_sp:.2f}, {OY*iso_sp:.2f}, {OZ*iso_sp:.2f}], '
            f'"tilesPerRow": {TILES_PER_ROW}, "tileRows": {rows}, "boneThr": 0.55, "mr": true}}')
    with open('acousticmr3d_data.js', 'w') as f:
        f.write(ATTRIB)
        f.write('// MR (not CT): dims=[x(LR),y(AP),z(SI)], intensity percentile-normalised to 0..255.\n')
        f.write(f'const ACOUSTICMR3D_VOL={meta};\n')
        f.write(f"ACOUSTICMR3D_VOL.atlas='data:image/png;base64,{ct_b64}';\n")
    bits_json = ', '.join(f'"{k}": {v}' for k, v in bits.items())
    lbl_meta = (f'{{"dims": [{OX}, {OY}, {OZ}], "spacingMm": [{iso_sp:.4f}, {iso_sp:.4f}, {iso_sp:.4f}], '
                f'"tilesPerRow": {TILES_PER_ROW}, "bits": {{{bits_json}}}, "isoIdx": [{iso[0]}, {iso[1]}, {iso[2]}]}}')
    with open('acousticmr3d_labels_data.js', 'w') as f:
        f.write(ATTRIB)
        f.write('// VS SRS labels: tumour (TV) + cochlea OAR + skull/body, from the T1 Gd RTSTRUCT.\n')
        f.write(f'const ACOUSTICMR3D_LABELS={lbl_meta};\n')
        f.write(f"ACOUSTICMR3D_LABELS.atlas='data:image/png;base64,{lbl_b64}';\n")
    print('wrote acousticmr3d_data.js + acousticmr3d_labels_data.js')

if __name__ == '__main__':
    main()
