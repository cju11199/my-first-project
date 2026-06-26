#!/usr/bin/env python3
"""
generate_sarcoma.py
Build the Soft-tissue Sarcoma case from a TCIA Soft-tissue-Sarcoma patient
(extremity CT + a GTV_Mass RTSTRUCT) and write
  - sarcoma3d_data.js        (CT volume atlas)        -> SARCOMA3D_VOL
  - sarcoma3d_labels_data.js (tumour + limb label)    -> SARCOMA3D_LABELS

Same tiled-atlas format as the other CBCT cases. A soft-tissue sarcoma in a limb:
the RTSTRUCT carries a single real GTV (GTV_Mass) — the target — so no synthesis.

DATA (NCI Imaging Data Commons public bucket; reachable where TCIA is blocked):
  pip install idc-index pydicom numpy scipy pillow
  collection soft_tissue_sarcoma, e.g. patient STS_004: download the CT series + a
  GTV_Mass RTSTRUCT, then:
  python generate_sarcoma.py --ct /path/to/CT_series --rtstruct /path/to/RTSTRUCT.dcm

Licence CC BY 3.0 (commercial use OK with attribution) — attribute the
Soft-tissue-Sarcoma collection, The Cancer Imaging Archive, doi:10.7937/K9/TCIA.2015.7GO2GSKS
(baked into the data-file headers).

TEACHING POINT: unusual (non-axial) anatomy — align a limb soft-tissue sarcoma; the
bony landmark is a single long bone, so the soft-tissue tumour drives the match.
"""
import argparse, os, re, io, base64, math, glob
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

try:
    import pydicom
except ImportError:
    raise SystemExit("pydicom required:  pip install pydicom numpy scipy pillow")

TARGET_XY      = 200
TILES_PER_ROW  = 10
CROP_MARGIN_MM    = 35   # SI margin around the tumour (slab of the limb around the lesion)
INPLANE_MARGIN_MM = 55   # in-plane margin around the TUMOUR -> frames the AFFECTED limb (these scans
                         # often image both legs; a tumour-centred crop keeps resolution + the right limb)

HU_OFF, HU_SCALE = -500.0, 2000.0 / 255.0
def hu_to_density(hu):
    return np.clip((hu - HU_OFF) / HU_SCALE, 0, 255).astype(np.uint8)

STRUCT_BITS = {'body': 1, 'tumor': 2}
ROI_ALIASES = [
    ('edema', None), ('oedema', None),                    # GTV_Edema is NOT the target -> skip (else 'gtv' below folds it into the mass)
    ('mass', 'tumor'), ('gtvmass', 'tumor'), ('gtv', 'tumor'), ('tumor', 'tumor'), ('tumour', 'tumor'),
    ('lesion', 'tumor'), ('sarcoma', 'tumor'),
    ('external', 'body'), ('body', 'body'), ('skin', 'body'),
]
def map_roi(name):
    n = re.sub(r'[^a-z0-9]', '', name.lower())
    for sub, key in ROI_ALIASES:
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

def rasterize(rt_path, ct):
    rt = pydicom.dcmread(rt_path, force=True)
    names = {r.ROINumber: r.ROIName for r in rt.StructureSetROISequence}
    masks = {k: np.zeros((ct['nz'], ct['ny'], ct['nx']), bool) for k in STRUCT_BITS}
    mapped = {}
    for roi in rt.ROIContourSequence:
        nm = names.get(roi.ReferencedROINumber, '?'); key = map_roi(nm); mapped[nm] = key
        if key is None or not hasattr(roi, 'ContourSequence'):
            continue
        for c in roi.ContourSequence:
            pts = np.array(c.ContourData, float).reshape(-1, 3)
            zi = int(round((pts[:, 2].mean() - ct['z0']) / ct['dz']))
            if not (0 <= zi < ct['nz']):
                continue
            col = (pts[:, 0] - ct['ox']) / ct['px']; row = (pts[:, 1] - ct['oy']) / ct['py']
            img = Image.new('L', (ct['nx'], ct['ny']), 0)
            ImageDraw.Draw(img).polygon(list(zip(col, row)), outline=1, fill=1)
            masks[key][zi] |= np.array(img, bool)
    print("ROI mapping:", {k: v for k, v in mapped.items()})
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
    ap.add_argument('--rtstruct', required=True, help='GTV_Mass RTSTRUCT')
    args = ap.parse_args()

    ct = load_ct(args.ct)
    masks = rasterize(args.rtstruct, ct)
    if not masks['tumor'].any():
        raise SystemExit("no GTV/tumour ROI matched — check ROI_ALIASES against the printed ROI list")
    # body = the limb; keep the largest 3D connected component so the CT/CT-table support
    # (couch) is excluded (its own component), then zero the CT outside the limb to drop the
    # bright table arc from view.
    body = ndimage.binary_opening(ndimage.binary_fill_holes(ct['hu'] > -350), iterations=2)
    lb, n = ndimage.label(body)
    if n > 1:
        sizes = np.bincount(lb.ravel()); sizes[0] = 0; body = lb == sizes.argmax()
    masks['body'] = body
    dens = hu_to_density(ct['hu'])
    dens[~ndimage.binary_dilation(body, iterations=2)] = 0   # remove couch/background
    spz, spy, spx = ct['dz'], ct['py'], ct['px']

    # crop: SI (z) to the tumour slab; in-plane (x,y) to the AFFECTED LIMB (tumour bbox + margin,
    # clamped to the body so we don't frame empty air)
    tzz, tyy, txx = np.where(masks['tumor'])
    mz, my, mx = CROP_MARGIN_MM/spz, INPLANE_MARGIN_MM/spy, INPLANE_MARGIN_MM/spx
    z0, z1 = max(0, int(tzz.min()-mz)), min(ct['nz'], int(tzz.max()+mz)+1)
    by, bx = np.where(masks['body'][z0:z1].any(axis=0))
    y0 = max(int(by.min()), int(tyy.min()-my)); y1 = min(int(by.max())+1, int(tyy.max()+my)+1)
    x0 = max(int(bx.min()), int(txx.min()-mx)); x1 = min(int(bx.max())+1, int(txx.max()+mx)+1)
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
    tz2, ty2, tx2 = np.where(rm['tumor'])
    iso = [int(round(tx2.mean())), int(round(ty2.mean())), int(round(tz2.mean()))]
    vcc = rm['tumor'].sum()*iso_sp**3/1000
    print(f"iso(voxel)={iso}  bits={bits}  tumour {int(rm['tumor'].sum())} vox ({vcc:.1f} cc)")

    ct_b64, ct_sz, rows = encode_atlas(vol_d, OX, OY, OZ, TILES_PER_ROW)
    lbl_b64, lbl_sz, _  = encode_atlas(labels, OX, OY, OZ, TILES_PER_ROW)
    print(f"CT atlas {ct_sz//1024} KB   label atlas {lbl_sz//1024} KB")

    ATTRIB = ('// Source: TCIA Soft-tissue-Sarcoma (via NCI Imaging Data Commons, s3://idc-open-data).\n'
              '// Licence: CC BY 3.0 (commercial use permitted with attribution).\n'
              '// Attribution: Soft-tissue-Sarcoma, The Cancer Imaging Archive, doi:10.7937/K9/TCIA.2015.7GO2GSKS.\n'
              '// De-identified extremity CT with a real GTV_Mass tumour RTSTRUCT.\n')
    meta = (f'{{"dims": [{OX}, {OY}, {OZ}], "spacingMm": [{iso_sp:.4f}, {iso_sp:.4f}, {iso_sp:.4f}], '
            f'"physMm": [{OX*iso_sp:.2f}, {OY*iso_sp:.2f}, {OZ*iso_sp:.2f}], '
            f'"tilesPerRow": {TILES_PER_ROW}, "tileRows": {rows}, "boneThr": 0.62}}')
    with open('sarcoma3d_data.js', 'w') as f:
        f.write(ATTRIB)
        f.write('// dims=[x(LR),y(AP),z(SI)]. Plain extremity CT; rigid 6DOF soft-tissue tumour match.\n')
        f.write(f'const SARCOMA3D_VOL={meta};\n')
        f.write(f"SARCOMA3D_VOL.atlas='data:image/png;base64,{ct_b64}';\n")
    bits_json = ', '.join(f'"{k}": {v}' for k, v in bits.items())
    lbl_meta = (f'{{"dims": [{OX}, {OY}, {OZ}], "spacingMm": [{iso_sp:.4f}, {iso_sp:.4f}, {iso_sp:.4f}], '
                f'"tilesPerRow": {TILES_PER_ROW}, "bits": {{{bits_json}}}, "isoIdx": [{iso[0]}, {iso[1]}, {iso[2]}]}}')
    with open('sarcoma3d_labels_data.js', 'w') as f:
        f.write(ATTRIB)
        f.write('// Sarcoma labels: tumour (GTV_Mass) target + limb body, from the RTSTRUCT.\n')
        f.write(f'const SARCOMA3D_LABELS={lbl_meta};\n')
        f.write(f"SARCOMA3D_LABELS.atlas='data:image/png;base64,{lbl_b64}';\n")
    print('wrote sarcoma3d_data.js + sarcoma3d_labels_data.js')

if __name__ == '__main__':
    main()
