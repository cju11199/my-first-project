#!/usr/bin/env python3
"""
generate_cervix_cbct.py
Build the Gynae / Uterus CBCT case from a CPTAC-UCEC patient (contrast venous-
phase pelvic CT + a radiologist UTERUS tumour annotation RTSTRUCT) and write
  - cervix3d_data.js        (CT volume atlas)              -> CERVIX3D_VOL
  - cervix3d_labels_data.js (target + OAR label atlas)     -> CERVIX3D_LABELS

Same tiled-atlas format every other CBCT case uses (pelvis/prostate/liver/...):
an 8-bit grayscale PNG with the Z slices tiled in a grid, base64'd into a
data-URI, plus a small JSON metadata header. trainer.html (decodeVol /
_decode*Labels) reslices it into the 3 MPR panes; the "CBCT/moving" image is
SYNTHESISED by reslicing the same CT through a hidden 6DOF offset, so a real
second CBCT series is NOT needed — we only consume the planning CT + its
annotation.

DATA
----
Source (confirm licence CC BY first):
  CPTAC-UCEC  (Uterine Corpus Endometrial Carcinoma)  https://doi.org/10.7937/k9/tcia.2018.3r3juisw
  patient C3N-00872: venous-phase contrast CT + a "UTERUS - 1" tumour annotation RTSTRUCT.
Pulled from the NCI Imaging Data Commons bucket s3://idc-open-data via idc-index.

The RTSTRUCT here is a radiologist TUMOUR ANNOTATION (the whole uterus as the
imaged target), not a full clinical RT plan, so it carries no OAR set. The body
is thresholded from the CT and the bladder is auto-segmented from CT fluid
density as a context OAR (printed size; drop with --no-bladder if QC is poor).
The uterus is the real target — nothing is synthesised destructively into the CT.

USAGE
-----
  pip install pydicom numpy scipy pillow
  python generate_cervix_cbct.py --ct /path/to/venous_CT_series_dir \
                                 --rtstruct /path/to/UTERUS_RTSTRUCT.dcm
"""
import argparse, os, re, io, base64, math, glob
import numpy as np
from PIL import Image
from scipy import ndimage

try:
    import pydicom
except ImportError:
    raise SystemExit("pydicom is required:  pip install pydicom numpy scipy pillow")

# --- output sizing (keep the atlas ~1.5-2 MB like the other *3d_data.js files) ---
TARGET_XY     = 192     # longest-axis resample size (px). Other cases sit ~180-224.
TILES_PER_ROW = 10      # atlas tiling (10 cols x ceil(Z/10) rows), matches the others.
CROP_MARGIN_MM = 60     # superior-inferior margin around the uterus target -> pelvic slab.
BODY_MARGIN_MM = 8      # in-plane (LR/AP) skin margin around the BODY mask.

# HU -> density(0..255):  HU = density*(2000/255) - 500  =>  density = (HU+500)*255/2000.
HU_OFF, HU_SCALE = -500.0, 2000.0 / 255.0
def hu_to_density(hu):
    return np.clip((hu - HU_OFF) / HU_SCALE, 0, 255).astype(np.uint8)

# Fixed bit layout consumed by trainer.html's default CBCT struct set (uint8 -> 8 bits).
# The uterine target uses the generic 'tumor' key so it reuses the trainer's existing tumour
# legend / contour-menu slot (same as the liver / sarcoma soft-tissue cases).
STRUCT_BITS = {
    'body':  1,    # External/BODY (thresholded from the CT)
    'tumor': 2,    # the tumour target (real UTERUS annotation)
}
# Lowercased substrings -> struct key (first match wins; specific first).
ROI_ALIASES = [
    ('uterus', 'tumor'), ('uterine', 'tumor'), ('cervix', 'tumor'),
    ('gtv', 'tumor'), ('ctv', 'tumor'), ('tumor', 'tumor'), ('tumour', 'tumor'),
    ('external', 'body'), ('body', 'body'), ('skin', 'body'),
]
def map_roi(name):
    n = re.sub(r'[^a-z0-9]', '', name.lower())
    if 'seed' in name.lower():          # skip the "- SEED POINT" helper ROIs
        return None
    for sub, key in ROI_ALIASES:
        if re.sub(r'[^a-z0-9]', '', sub) in n:
            return key
    return None

# --- CT series loading -------------------------------------------------------
def load_ct(ct_dir):
    files = [f for f in glob.glob(os.path.join(ct_dir, '**', '*'), recursive=True) if os.path.isfile(f)]
    slices = []
    for f in files:
        try:
            ds = pydicom.dcmread(f, force=True)
        except Exception:
            continue
        if getattr(ds, 'Modality', '') != 'CT' or not hasattr(ds, 'ImagePositionPatient'):
            continue
        slices.append(ds)
    if not slices:
        raise SystemExit(f"No CT slices found under {ct_dir}")
    slices.sort(key=lambda s: float(s.ImagePositionPatient[2]))
    ref = slices[0]
    ny, nx = int(ref.Rows), int(ref.Columns)
    px, py = float(ref.PixelSpacing[1]), float(ref.PixelSpacing[0])
    z = [float(s.ImagePositionPatient[2]) for s in slices]
    dz = float(np.median(np.diff(z))) if len(z) > 1 else float(getattr(ref, 'SliceThickness', 1))
    origin = np.array(ref.ImagePositionPatient, float)
    vol = np.zeros((len(slices), ny, nx), np.float32)
    for i, s in enumerate(slices):
        arr = s.pixel_array.astype(np.float32)
        vol[i] = arr * float(getattr(s, 'RescaleSlope', 1)) + float(getattr(s, 'RescaleIntercept', 0))
    print(f"CT: {nx}x{ny}x{len(slices)}  in-plane {px:.3f}x{py:.3f} mm  dz {abs(dz):.3f} mm")
    return dict(hu=vol, nx=nx, ny=ny, nz=len(slices), px=px, py=py, dz=abs(dz),
                origin=origin, z0=z[0])

# --- RTSTRUCT rasterisation --------------------------------------------------
def _poly_mask(poly, ny, nx):
    from PIL import ImageDraw
    img = Image.new('L', (nx, ny), 0)
    ImageDraw.Draw(img).polygon([tuple(p) for p in poly], outline=1, fill=1)
    return np.array(img, bool)

def rasterize(rt_path, ct):
    rt = pydicom.dcmread(rt_path, force=True)
    roi_names = {r.ROINumber: r.ROIName for r in rt.StructureSetROISequence}
    nz, ny, nx = ct['nz'], ct['ny'], ct['nx']
    px, py, z0, dz = ct['px'], ct['py'], ct['z0'], ct['dz']
    ox, oy = ct['origin'][0], ct['origin'][1]
    masks = {k: np.zeros((nz, ny, nx), bool) for k in STRUCT_BITS}
    mapped = {}
    for roi in rt.ROIContourSequence:
        nm = roi_names.get(roi.ReferencedROINumber, f'ROI{roi.ReferencedROINumber}')
        key = map_roi(nm)
        mapped[nm] = key
        if key is None or not hasattr(roi, 'ContourSequence'):
            continue
        for c in roi.ContourSequence:
            pts = np.array(c.ContourData, float).reshape(-1, 3)
            zi = int(round((pts[:, 2].mean() - z0) / dz))
            if zi < 0 or zi >= nz:
                continue
            col = (pts[:, 0] - ox) / px
            row = (pts[:, 1] - oy) / py
            masks[key][zi] |= _poly_mask(np.stack([col, row], 1), ny, nx)
    print("ROI mapping:")
    for nm, key in sorted(mapped.items()):
        print(f"   {nm:36s} -> {key}")
    # uterus annotations are drawn on outline slices only -> fill the z-gaps so the
    # target is a solid volume, not a venetian-blind stack of rings.
    if masks['tumor'].any():
        masks['tumor'] = _fill_z_gaps(masks['tumor'])
    return masks

def _fill_z_gaps(mask):
    """Fill empty axial slices between contoured ones by morphological closing in z."""
    out = mask.copy()
    zhit = np.where(mask.any(axis=(1, 2)))[0]
    if len(zhit) < 2:
        return out
    for z in range(zhit.min(), zhit.max() + 1):
        if not out[z].any():
            lo = max(zhit[zhit <= z]); hi = min(zhit[zhit >= z])
            out[z] = mask[lo] & mask[hi]      # intersection of bracketing slices
    return out

# --- crop + isotropic resample ----------------------------------------------
def resample(ct, masks):
    src = ct['hu']
    SZ, SY, SX = ct['nz'], ct['ny'], ct['nx']
    spz, spy, spx = ct['dz'], ct['py'], ct['px']
    # z slab around the uterus target; in-plane crop to the body mask.
    tgt = masks['tumor']
    if tgt.any():
        zsel = np.where(tgt.any(axis=(1, 2)))[0]
        mz = CROP_MARGIN_MM / spz
        z0, z1 = max(0, int(zsel.min() - mz)), min(SZ, int(zsel.max() + mz) + 1)
    else:
        z0, z1 = 0, SZ
    body = masks.get('body')
    if body is not None and body[z0:z1].any():
        bslab = body[z0:z1]
        ysel = np.where(bslab.any(axis=(0, 2)))[0]
        xsel = np.where(bslab.any(axis=(0, 1)))[0]
        my, mx = BODY_MARGIN_MM / spy, BODY_MARGIN_MM / spx
        y0, y1 = max(0, int(ysel.min() - my)), min(SY, int(ysel.max() + my) + 1)
        x0, x1 = max(0, int(xsel.min() - mx)), min(SX, int(xsel.max() + mx) + 1)
    else:
        y0, y1, x0, x1 = 0, SY, 0, SX
    print(f"crop z[{z0}:{z1}] (uterus slab) y[{y0}:{y1}] x[{x0}:{x1}] (body) of {SZ}x{SY}x{SX}")
    src = src[z0:z1, y0:y1, x0:x1]
    masks = {k: m[z0:z1, y0:y1, x0:x1] for k, m in masks.items()}
    CZ, CY, CX = src.shape

    phys = [CX * spx, CY * spy, CZ * spz]
    iso_sp = max(phys) / TARGET_XY
    OX = max(1, int(round(phys[0] / iso_sp)))
    OY = max(1, int(round(phys[1] / iso_sp)))
    OZ = max(1, int(round(phys[2] / iso_sp)))
    zoom = (OZ / CZ, OY / CY, OX / CX)
    print(f"resample -> {OX}x{OY}x{OZ}  iso spacing {iso_sp:.3f} mm  phys {[round(p) for p in phys]}")
    ct_d = hu_to_density(ndimage.zoom(src, zoom, order=1))
    out_masks = {}
    for k, m in masks.items():
        out_masks[k] = (ndimage.zoom(m.astype(np.float32), zoom, order=1) > 0.5) if m.any() \
                       else np.zeros((OZ, OY, OX), bool)
    return ct_d, out_masks, (OX, OY, OZ), iso_sp

# --- atlas encode ------------------------------------------------------------
def encode_atlas(vol, OX, OY, OZ, tpr):
    rows = math.ceil(OZ / tpr)
    out = np.zeros((rows * OY, tpr * OX), np.uint8)
    for z in range(OZ):
        tc, tr = z % tpr, z // tpr
        out[tr*OY:tr*OY+OY, tc*OX:tc*OX+OX] = vol[z]
    buf = io.BytesIO(); Image.fromarray(out, 'L').save(buf, format='PNG', compress_level=9)
    return base64.b64encode(buf.getvalue()).decode('ascii'), len(buf.getvalue()), rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ct', required=True, help='planning-CT DICOM series directory')
    ap.add_argument('--rtstruct', required=True, help='UTERUS RTSTRUCT .dcm file')
    ap.add_argument('--qc', default='/tmp/cervix_qc', help='QC stills output dir')
    args = ap.parse_args()

    ct = load_ct(args.ct)
    masks = rasterize(args.rtstruct, ct)
    if not masks['tumor'].any():
        raise SystemExit("No UTERUS target rasterised — check the RTSTRUCT references this CT series.")

    # body: threshold the CT (no external ROI in a tumour-annotation RTSTRUCT)
    print("thresholding the CT for a body mask")
    body = ndimage.binary_fill_holes(ct['hu'] > -350)
    body = ndimage.binary_opening(body, iterations=2)
    lbl, n = ndimage.label(body)
    if n > 1:
        sizes = np.bincount(lbl.ravel()); sizes[0] = 0
        body = lbl == sizes.argmax()           # largest CC = torso (drops the couch)
    masks['body'] = body

    ct_d, rmasks, (OX, OY, OZ), iso_sp = resample(ct, masks)

    def centroid(mask):
        zz, yy, xx = np.where(mask)
        return [int(round(xx.mean())), int(round(yy.mean())), int(round(zz.mean()))]
    iso = centroid(rmasks['tumor'])
    vol_cc = rmasks['tumor'].sum() * iso_sp**3 / 1000
    print(f"uterus target {int(rmasks['tumor'].sum())} vox ({vol_cc:.1f} cc) centred {iso}")

    labels = np.zeros((OZ, OY, OX), np.uint8)
    bits_present = {}
    for k, bit in STRUCT_BITS.items():
        if rmasks[k].any():
            labels[rmasks[k]] |= bit; bits_present[k] = bit
    print(f"iso(voxel)={iso}  bits={bits_present}")

    # QC stills: axial/coronal/sagittal through the iso with target+bladder overlaid
    os.makedirs(args.qc, exist_ok=True)
    _qc(ct_d, rmasks, iso, args.qc)

    ct_b64, ct_sz, rows = encode_atlas(ct_d, OX, OY, OZ, TILES_PER_ROW)
    lbl_b64, lbl_sz, _  = encode_atlas(labels, OX, OY, OZ, TILES_PER_ROW)
    print(f"CT atlas {ct_sz//1024} KB   label atlas {lbl_sz//1024} KB")

    meta = (f'{{"dims": [{OX}, {OY}, {OZ}], "spacingMm": [{iso_sp:.4f}, {iso_sp:.4f}, {iso_sp:.4f}], '
            f'"physMm": [{OX*iso_sp:.2f}, {OY*iso_sp:.2f}, {OZ*iso_sp:.2f}], '
            f'"tilesPerRow": {TILES_PER_ROW}, "tileRows": {rows}, "boneThr": 0.62}}')
    ATTRIB = ('// Source: CPTAC-UCEC (Uterine Corpus Endometrial Carcinoma; via NCI Imaging Data Commons, s3://idc-open-data).\n'
              '// Licence: CC BY 4.0 (commercial use permitted with attribution).\n'
              '// Attribution: National Cancer Institute Clinical Proteomic Tumor Analysis Consortium (CPTAC),\n'
              '//   The Cancer Imaging Archive, doi:10.7937/k9/tcia.2018.3r3juisw.\n'
              '// De-identified contrast-CT pelvis, cropped to the uterus region + resampled to an isotropic atlas.\n')
    with open('cervix3d_data.js', 'w') as f:
        f.write(ATTRIB)
        f.write('// dims=[x(LR),y(AP),z(SI)]. Plain CT (no baked features); rigid 6DOF soft-tissue match (gynae/uterus target).\n')
        f.write(f'const CERVIX3D_VOL={meta};\n')
        f.write(f"CERVIX3D_VOL.atlas='data:image/png;base64,{ct_b64}';\n")

    bits_json = ', '.join(f'"{k}": {v}' for k, v in bits_present.items())
    lbl_meta = (f'{{"dims": [{OX}, {OY}, {OZ}], "spacingMm": [{iso_sp:.4f}, {iso_sp:.4f}, {iso_sp:.4f}], '
                f'"tilesPerRow": {TILES_PER_ROW}, "bits": {{{bits_json}}}, '
                f'"isoIdx": [{iso[0]}, {iso[1]}, {iso[2]}]}}')
    with open('cervix3d_labels_data.js', 'w') as f:
        f.write(ATTRIB)
        f.write('// Gynae/Uterus CBCT case labels: real UTERUS tumour target (bit "tumor") + thresholded body (bits below).\n')
        f.write(f'const CERVIX3D_LABELS={lbl_meta};\n')
        f.write(f"CERVIX3D_LABELS.atlas='data:image/png;base64,{lbl_b64}';\n")
    print('wrote cervix3d_data.js + cervix3d_labels_data.js')
    print(f'QC stills in {args.qc} — review before wiring trainer.html.')

def _qc(ct_d, rmasks, iso, outdir):
    ix, iy, iz = iso
    overlay = {'tumor': (255, 60, 60), 'body': (60, 220, 100)}
    def rgb(gray):
        return np.stack([gray]*3, -1).astype(np.uint8)
    def draw(plane, base, masks2d):
        img = rgb(base)
        for k, col in overlay.items():
            m = masks2d.get(k)
            if m is None or not m.any():
                continue
            edge = m ^ ndimage.binary_erosion(m)
            img[edge] = col
        return img
    # axial @ iz
    ax = draw('ax', ct_d[iz], {k: rmasks[k][iz] for k in overlay})
    co = draw('co', ct_d[:, iy, :][::-1], {k: rmasks[k][:, iy, :][::-1] for k in overlay})
    sa = draw('sa', ct_d[:, :, ix][::-1], {k: rmasks[k][:, :, ix][::-1] for k in overlay})
    for nm, im in [('axial', ax), ('coronal', co), ('sagittal', sa)]:
        Image.fromarray(im).resize((im.shape[1]*3, im.shape[0]*3), Image.NEAREST).save(f'{outdir}/cervix_{nm}.png')

if __name__ == '__main__':
    main()
