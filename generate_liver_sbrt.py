#!/usr/bin/env python3
"""
generate_liver_sbrt.py
Build the Liver SBRT case from a TCIA Colorectal-Liver-Metastases patient
(contrast CT + a DICOM **SEG** with the liver organ + the tumour mass) and write
  - liver3d_data.js        (CT volume atlas)            -> LIVER3D_VOL
  - liver3d_labels_data.js (liver + tumour label atlas) -> LIVER3D_LABELS

Same tiled-atlas format as the other CBCT cases. Unlike the RTSTRUCT cases, the
contours here come from a **DICOM Segmentation (SEG)** object (multi-frame binary
masks). The "radiologist corrected" SEG carries segment 1 = Liver, 2 = Mass — a
real liver organ contour AND a real tumour target, so no synthesis is needed.

DATA (NCI Imaging Data Commons public bucket; reachable where TCIA is blocked):
  pip install idc-index pydicom numpy scipy pillow
  collection colorectal_liver_metastases, e.g. patient CRLM-CT-1012: download the CT
  series + the "...radiologist...corrected segmentation" SEG, then:
  python generate_liver_sbrt.py --ct /path/to/CT_series --seg /path/to/RADIOLOGIST_SEG.dcm

Licence CC BY 4.0 (commercial use OK with attribution) — attribute the
Colorectal-Liver-Metastases collection, The Cancer Imaging Archive,
doi:10.7937/QXK2-QG03 (baked into the data-file headers).

TEACHING POINT: liver SBRT — a soft-tissue match on the tumour within the liver
(respiratory motion makes the soft-tissue/fiducial match matter, not the bones).
"""
import argparse, os, re, io, base64, math, glob
import numpy as np
from PIL import Image
from scipy import ndimage

try:
    import pydicom
except ImportError:
    raise SystemExit("pydicom required:  pip install pydicom numpy scipy pillow")

TARGET_XY      = 200
TILES_PER_ROW  = 10
CROP_MARGIN_MM    = 30   # SI margin around the liver+tumour (defines the upper-abdomen slab)
INPLANE_MARGIN_MM = 28   # in-plane margin around the LIVER (these are wide, arms-in-FOV abdominal CTs,
                         # so frame on the liver for good resolution rather than the whole torso width)
FOCUS_KEYS = ('liver', 'tumor')

HU_OFF, HU_SCALE = -500.0, 2000.0 / 255.0
def hu_to_density(hu):
    return np.clip((hu - HU_OFF) / HU_SCALE, 0, 255).astype(np.uint8)

# uint8 bit layout consumed by trainer.html's LIVER_STRUCTS.
STRUCT_BITS = {'body': 1, 'tumor': 2, 'liver': 4}
# SEG SegmentLabel substrings -> key (first match wins; specific first so "Liver Remnant" is skipped).
SEG_ALIASES = [
    ('remnant', None), ('hepatic', None), ('portal', None), ('vein', None), ('artery', None),
    ('mass', 'tumor'), ('tumor', 'tumor'), ('tumour', 'tumor'), ('lesion', 'tumor'),
    ('gtv', 'tumor'), ('metas', 'tumor'),
    ('liver', 'liver'),
]
def map_seg(label):
    n = re.sub(r'[^a-z0-9]', '', (label or '').lower())
    for sub, key in SEG_ALIASES:
        if re.sub(r'[^a-z0-9]', '', sub) in n:
            return key
    return None

def load_ct(ct_dir):
    files = [f for f in glob.glob(os.path.join(ct_dir, '**', '*'), recursive=True) if os.path.isfile(f)]
    sl = []
    for f in files:
        try:
            ds = pydicom.dcmread(f, force=True)
        except Exception:
            continue
        if getattr(ds, 'Modality', '') != 'CT' or not hasattr(ds, 'ImagePositionPatient'):
            continue
        sl.append(ds)
    if not sl:
        raise SystemExit(f"No CT slices under {ct_dir}")
    sl.sort(key=lambda s: float(s.ImagePositionPatient[2]))
    ref = sl[0]; ny, nx = int(ref.Rows), int(ref.Columns)
    px, py = float(ref.PixelSpacing[1]), float(ref.PixelSpacing[0])
    z = [float(s.ImagePositionPatient[2]) for s in sl]
    dz = float(np.median(np.diff(z))) if len(z) > 1 else float(getattr(ref, 'SliceThickness', 1))
    vol = np.zeros((len(sl), ny, nx), np.float32)
    for i, s in enumerate(sl):
        vol[i] = s.pixel_array.astype(np.float32) * float(getattr(s, 'RescaleSlope', 1)) + float(getattr(s, 'RescaleIntercept', 0))
    print(f"CT: {nx}x{ny}x{len(sl)}  in-plane {px:.3f}x{py:.3f} mm  dz {abs(dz):.3f} mm")
    return dict(hu=vol, nx=nx, ny=ny, nz=len(sl), px=px, py=py, dz=abs(dz),
                ox=float(ref.ImagePositionPatient[0]), oy=float(ref.ImagePositionPatient[1]), z0=z[0])

def rasterize_seg(seg_path, ct):
    ds = pydicom.dcmread(seg_path, force=True)
    labels = {int(s.SegmentNumber): getattr(s, 'SegmentLabel', '?') for s in ds.SegmentSequence}
    arr = ds.pixel_array
    if arr.ndim == 2:
        arr = arr[None]
    if ds.Rows != ct['ny'] or ds.Columns != ct['nx']:
        raise SystemExit(f"SEG grid {ds.Columns}x{ds.Rows} != CT {ct['nx']}x{ct['ny']} (in-plane resample not implemented)")
    masks = {k: np.zeros((ct['nz'], ct['ny'], ct['nx']), bool) for k in STRUCT_BITS}
    mapped = {}
    for i, fg in enumerate(ds.PerFrameFunctionalGroupsSequence):
        z = float(fg.PlanePositionSequence[0].ImagePositionPatient[2])
        segn = int(fg.SegmentIdentificationSequence[0].ReferencedSegmentNumber)
        zi = int(round((z - ct['z0']) / ct['dz']))
        if not (0 <= zi < ct['nz']):
            continue
        key = map_seg(labels.get(segn, '')); mapped[labels.get(segn)] = key
        if key is None:
            continue
        masks[key][zi] |= arr[i].astype(bool)
    print("SEG segment mapping:")
    for nm, key in sorted(mapped.items(), key=lambda kv: str(kv[0])):
        print(f"   {str(nm):20s} -> {key}")
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
    ap.add_argument('--ct', required=True)
    ap.add_argument('--seg', required=True, help='radiologist-corrected SEG (segments: Liver, Mass)')
    args = ap.parse_args()

    ct = load_ct(args.ct)
    masks = rasterize_seg(args.seg, ct)
    if not masks['tumor'].any():
        raise SystemExit("no tumour/mass segment matched — check SEG_ALIASES against the printed segment list")
    masks['body'] = ndimage.binary_opening(ndimage.binary_fill_holes(ct['hu'] > -350), iterations=2)
    dens = hu_to_density(ct['hu'])
    spz, spy, spx = ct['dz'], ct['py'], ct['px']

    # crop: SI (z) to the liver+tumour slab; in-plane (x,y) to the BODY bbox (keep the torso in frame)
    focus = np.zeros_like(masks['tumor'])
    for k in FOCUS_KEYS:
        focus |= masks[k]
    fzz, fyy, fxx = np.where(focus)
    mz, my, mx = CROP_MARGIN_MM/spz, INPLANE_MARGIN_MM/spy, INPLANE_MARGIN_MM/spx
    z0, z1 = max(0, int(fzz.min()-mz)), min(ct['nz'], int(fzz.max()+mz)+1)
    y0, y1 = max(0, int(fyy.min()-my)), min(ct['ny'], int(fyy.max()+my)+1)
    x0, x1 = max(0, int(fxx.min()-mx)), min(ct['nx'], int(fxx.max()+mx)+1)
    print(f"crop z[{z0}:{z1}] y[{y0}:{y1}] x[{x0}:{x1}] of {ct['nz']}x{ct['ny']}x{ct['nx']}")
    dens = dens[z0:z1, y0:y1, x0:x1]
    masks = {k: m[z0:z1, y0:y1, x0:x1] for k, m in masks.items()}
    CZ, CY, CX = dens.shape

    phys = [CX*spx, CY*spy, CZ*spz]; iso_sp = max(phys)/TARGET_XY
    OX, OY, OZ = max(1, round(phys[0]/iso_sp)), max(1, round(phys[1]/iso_sp)), max(1, round(phys[2]/iso_sp))
    zoom = (OZ/CZ, OY/CY, OX/CX)
    print(f"resample -> {OX}x{OY}x{OZ}  iso {iso_sp:.3f} mm  phys {[round(p) for p in phys]}")
    vol_d = np.clip(ndimage.zoom(dens.astype(np.float32), zoom, order=1), 0, 255).astype(np.uint8)
    rm = {k: (ndimage.zoom(m.astype(np.float32), zoom, order=1) > 0.5) if m.any()
             else np.zeros((OZ, OY, OX), bool) for k, m in masks.items()}

    labels = np.zeros((OZ, OY, OX), np.uint8); bits = {}
    for k, bit in STRUCT_BITS.items():
        if rm[k].any():
            labels[rm[k]] |= bit; bits[k] = bit
    tz, ty, tx = np.where(rm['tumor'])
    iso = [int(round(tx.mean())), int(round(ty.mean())), int(round(tz.mean()))]
    vcc = rm['tumor'].sum()*iso_sp**3/1000
    print(f"iso(voxel)={iso}  bits={bits}  tumour {int(rm['tumor'].sum())} vox ({vcc:.1f} cc)  liver {int(rm['liver'].sum())} vox")

    ct_b64, ct_sz, rows = encode_atlas(vol_d, OX, OY, OZ, TILES_PER_ROW)
    lbl_b64, lbl_sz, _  = encode_atlas(labels, OX, OY, OZ, TILES_PER_ROW)
    print(f"CT atlas {ct_sz//1024} KB   label atlas {lbl_sz//1024} KB")

    ATTRIB = ('// Source: TCIA Colorectal-Liver-Metastases (via NCI Imaging Data Commons, s3://idc-open-data).\n'
              '// Licence: CC BY 4.0 (commercial use permitted with attribution).\n'
              '// Attribution: Colorectal-Liver-Metastases, The Cancer Imaging Archive, doi:10.7937/QXK2-QG03.\n'
              '// De-identified contrast CT with radiologist liver + tumour (Mass) DICOM-SEG contours.\n')
    meta = (f'{{"dims": [{OX}, {OY}, {OZ}], "spacingMm": [{iso_sp:.4f}, {iso_sp:.4f}, {iso_sp:.4f}], '
            f'"physMm": [{OX*iso_sp:.2f}, {OY*iso_sp:.2f}, {OZ*iso_sp:.2f}], '
            f'"tilesPerRow": {TILES_PER_ROW}, "tileRows": {rows}, "boneThr": 0.62}}')
    with open('liver3d_data.js', 'w') as f:
        f.write(ATTRIB)
        f.write('// dims=[x(LR),y(AP),z(SI)]. Plain CT; rigid 6DOF soft-tissue liver-tumour match.\n')
        f.write(f'const LIVER3D_VOL={meta};\n')
        f.write(f"LIVER3D_VOL.atlas='data:image/png;base64,{ct_b64}';\n")
    bits_json = ', '.join(f'"{k}": {v}' for k, v in bits.items())
    lbl_meta = (f'{{"dims": [{OX}, {OY}, {OZ}], "spacingMm": [{iso_sp:.4f}, {iso_sp:.4f}, {iso_sp:.4f}], '
                f'"tilesPerRow": {TILES_PER_ROW}, "bits": {{{bits_json}}}, "isoIdx": [{iso[0]}, {iso[1]}, {iso[2]}]}}')
    with open('liver3d_labels_data.js', 'w') as f:
        f.write(ATTRIB)
        f.write('// Liver SBRT labels: tumour (Mass) target + liver organ + body, from the radiologist SEG.\n')
        f.write(f'const LIVER3D_LABELS={lbl_meta};\n')
        f.write(f"LIVER3D_LABELS.atlas='data:image/png;base64,{lbl_b64}';\n")
    print('wrote liver3d_data.js + liver3d_labels_data.js')

if __name__ == '__main__':
    main()
