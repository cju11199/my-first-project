#!/usr/bin/env python3
"""
generate_adrenal_cbct.py
Build the Adrenal CBCT case from an Adrenal-ACC-Ki67-Seg patient (contrast
abdominal CT + a DICOM-SEG tumour segmentation) and write
  - adrenal3d_data.js        (CT volume atlas)            -> ADRENAL3D_VOL
  - adrenal3d_labels_data.js (target + body label atlas)  -> ADRENAL3D_LABELS

Same tiled-atlas format every other CBCT case uses (liver/cervix/sarcoma/...).
trainer.html (decodeVol / _decodeAdrenalLabels) reslices it into the 3 MPR
panes; the "CBCT/moving" image is SYNTHESISED by reslicing the same CT through
a hidden 6DOF offset, so a real second CBCT series is NOT needed.

This is an **off-bone** case (config-driven in trainer.html's VOLCASE.adrenal):
the adrenal mass drifts with respiration relative to the skeleton, so a bony
(vertebral) match leaves the target off — the student must register the
soft-tissue mass. The mass is a soft-tissue density sitting in retroperitoneal
FAT, so the off-bone hide/redraw reads with strong contrast (mass ~40 HU vs
fat ~-80 HU), exactly like the lung-nodule-in-air case — and unlike a liver
metastasis, which is isodense with liver and can't be shown off-bone.

DATA
----
Source (licence CC BY 4.0 — commercial use OK with attribution):
  Adrenal-ACC-Ki67-Seg   https://doi.org/10.7937/1fpg-vm46
  patient Adrenal_Ki67_Seg_052: a 1.25 mm contrast abdominal CT with a
  DICOM-SEG of the adrenocortical carcinoma. Pulled from the NCI Imaging Data
  Commons bucket s3://idc-open-data via the idc-index PyPI package. Patient 052
  was chosen over the 5 mm venous series of patient 001 because its SEG is drawn
  on a thin 1.25 mm series -> sharp coronal/sagittal reformats.

The SEG carries only the tumour segment (no OARs / external), so the body is
thresholded from the CT and the mass is the real, un-synthesised target.

USAGE
-----
  pip install idc-index pydicom numpy scipy pillow
  python generate_adrenal_cbct.py --ct /path/to/CT_series_dir --seg /path/to/SEG.dcm
"""
import argparse, os, re, io, base64, math, glob
import numpy as np
from PIL import Image
from scipy import ndimage

try:
    import pydicom
except ImportError:
    raise SystemExit("pydicom required:  pip install pydicom numpy scipy pillow")

TARGET_XY      = 200    # longest-axis resample size (px)
TILES_PER_ROW  = 10
CROP_MARGIN_MM = 30     # SI margin around the mass (defines the abdominal slab)
BODY_MARGIN_MM = 10     # in-plane (LR/AP) skin margin around the BODY mask (keep whole torso framed)

HU_OFF, HU_SCALE = -500.0, 2000.0 / 255.0
def hu_to_density(hu):
    return np.clip((hu - HU_OFF) / HU_SCALE, 0, 255).astype(np.uint8)

# uint8 bit layout consumed by trainer.html's ADRENAL_STRUCTS. The mass uses the generic 'tumor'
# key so it reuses the trainer's existing tumour legend/contour slot (like liver/sarcoma/cervix).
STRUCT_BITS = {'body': 1, 'tumor': 2}
# SEG SegmentLabel substrings -> key (first match wins; specific first).
SEG_ALIASES = [
    ('mass', 'tumor'), ('tumor', 'tumor'), ('tumour', 'tumor'), ('lesion', 'tumor'),
    ('gtv', 'tumor'), ('acc', 'tumor'), ('adrenal', 'tumor'), ('metas', 'tumor'),
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
        print(f"   {str(nm):24s} -> {key}")
    return masks

def encode_atlas(vol, OX, OY, OZ, tpr):
    rows = math.ceil(OZ / tpr)
    out = np.zeros((rows*OY, tpr*OX), np.uint8)
    for z in range(OZ):
        tc, tr = z % tpr, z // tpr
        out[tr*OY:tr*OY+OY, tc*OX:tc*OX+OX] = vol[z]
    buf = io.BytesIO(); Image.fromarray(out, 'L').save(buf, format='PNG', compress_level=9)
    return base64.b64encode(buf.getvalue()).decode('ascii'), len(buf.getvalue()), rows

def _qc(vol_d, rm, iso, outdir):
    os.makedirs(outdir, exist_ok=True)
    ix, iy, iz = iso
    overlay = {'tumor': (255, 60, 60), 'body': (60, 220, 100)}
    def draw(base, masks2d):
        img = np.stack([base]*3, -1).astype(np.uint8)
        for k, col in overlay.items():
            m = masks2d.get(k)
            if m is None or not m.any():
                continue
            img[m ^ ndimage.binary_erosion(m)] = col
        return img
    ax = draw(vol_d[iz], {k: rm[k][iz] for k in overlay})
    co = draw(vol_d[:, iy, :][::-1], {k: rm[k][:, iy, :][::-1] for k in overlay})
    sa = draw(vol_d[:, :, ix][::-1], {k: rm[k][:, :, ix][::-1] for k in overlay})
    for nm, im in [('axial', ax), ('coronal', co), ('sagittal', sa)]:
        Image.fromarray(im).resize((im.shape[1]*3, im.shape[0]*3), Image.NEAREST).save(f'{outdir}/adrenal_{nm}.png')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ct', required=True, help='abdominal-CT DICOM series directory')
    ap.add_argument('--seg', required=True, help='adrenal tumour DICOM-SEG .dcm')
    ap.add_argument('--qc', default='/tmp/adrenal_qc', help='QC stills output dir')
    args = ap.parse_args()

    ct = load_ct(args.ct)
    masks = rasterize_seg(args.seg, ct)
    if not masks['tumor'].any():
        raise SystemExit("no tumour segment matched — check SEG_ALIASES against the printed segment list")

    body = ndimage.binary_opening(ndimage.binary_fill_holes(ct['hu'] > -350), iterations=2)
    lbl, n = ndimage.label(body)
    if n > 1:
        sizes = ndimage.sum(np.ones_like(lbl), lbl, range(1, n + 1))
        body = lbl == (int(sizes.argmax()) + 1)        # largest CC = torso (drops the couch)
    masks['body'] = body
    dens = hu_to_density(ct['hu'])
    spz, spy, spx = ct['dz'], ct['py'], ct['px']

    # crop: SI (z) to the mass slab; in-plane (x,y) to the BODY bbox (keep the whole torso framed)
    fzz = np.where(masks['tumor'].any(axis=(1, 2)))[0]
    mz = CROP_MARGIN_MM/spz
    z0, z1 = max(0, int(fzz.min()-mz)), min(ct['nz'], int(fzz.max()+mz)+1)
    bslab = masks['body'][z0:z1]
    yy = np.where(bslab.any(axis=(0, 2)))[0]; xx = np.where(bslab.any(axis=(0, 1)))[0]
    my, mx = BODY_MARGIN_MM/spy, BODY_MARGIN_MM/spx
    y0, y1 = max(0, int(yy.min()-my)), min(ct['ny'], int(yy.max()+my)+1)
    x0, x1 = max(0, int(xx.min()-mx)), min(ct['nx'], int(xx.max()+mx)+1)
    print(f"crop z[{z0}:{z1}] (mass slab) y[{y0}:{y1}] x[{x0}:{x1}] (body) of {ct['nz']}x{ct['ny']}x{ct['nx']}")
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
    print(f"iso(voxel)={iso}  bits={bits}  tumour {int(rm['tumor'].sum())} vox ({vcc:.1f} cc)")

    _qc(vol_d, rm, iso, args.qc)
    ct_b64, ct_sz, rows = encode_atlas(vol_d, OX, OY, OZ, TILES_PER_ROW)
    lbl_b64, lbl_sz, _  = encode_atlas(labels, OX, OY, OZ, TILES_PER_ROW)
    print(f"CT atlas {ct_sz//1024} KB   label atlas {lbl_sz//1024} KB")

    ATTRIB = ('// Source: Adrenal-ACC-Ki67-Seg (via NCI Imaging Data Commons, s3://idc-open-data).\n'
              '// Licence: CC BY 4.0 (commercial use permitted with attribution).\n'
              '// Attribution: Adrenal-ACC-Ki67-Seg, The Cancer Imaging Archive, doi:10.7937/1fpg-vm46.\n'
              '// De-identified contrast abdominal CT (patient Adrenal_Ki67_Seg_052, 1.25 mm) with a\n'
              '// radiologist adrenal-tumour DICOM-SEG; cropped to the upper abdomen + isotropic atlas.\n')
    meta = (f'{{"dims": [{OX}, {OY}, {OZ}], "spacingMm": [{iso_sp:.4f}, {iso_sp:.4f}, {iso_sp:.4f}], '
            f'"physMm": [{OX*iso_sp:.2f}, {OY*iso_sp:.2f}, {OZ*iso_sp:.2f}], '
            f'"tilesPerRow": {TILES_PER_ROW}, "tileRows": {rows}, "boneThr": 0.62}}')
    with open('adrenal3d_data.js', 'w') as f:
        f.write(ATTRIB)
        f.write('// dims=[x(LR),y(AP),z(SI)]. Plain CT; off-bone 6DOF match (adrenal mass drifts vs the spine).\n')
        f.write(f'const ADRENAL3D_VOL={meta};\n')
        f.write(f"ADRENAL3D_VOL.atlas='data:image/png;base64,{ct_b64}';\n")
    bits_json = ', '.join(f'"{k}": {v}' for k, v in bits.items())
    lbl_meta = (f'{{"dims": [{OX}, {OY}, {OZ}], "spacingMm": [{iso_sp:.4f}, {iso_sp:.4f}, {iso_sp:.4f}], '
                f'"tilesPerRow": {TILES_PER_ROW}, "bits": {{{bits_json}}}, "isoIdx": [{iso[0]}, {iso[1]}, {iso[2]}]}}')
    with open('adrenal3d_labels_data.js', 'w') as f:
        f.write(ATTRIB)
        f.write('// Adrenal CBCT labels: adrenal tumour (bit "tumor", off-bone target) + thresholded body.\n')
        f.write(f'const ADRENAL3D_LABELS={lbl_meta};\n')
        f.write(f"ADRENAL3D_LABELS.atlas='data:image/png;base64,{lbl_b64}';\n")
    print('wrote adrenal3d_data.js + adrenal3d_labels_data.js')
    print(f'QC stills in {args.qc} — review before wiring trainer.html.')

if __name__ == '__main__':
    main()
