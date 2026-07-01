#!/usr/bin/env python3
"""
generate_pelvis_volume.py
(Re-)build the prostate-plan pelvis CT atlas from a documented CC-BY IDC source and write
  - pelvis3d_data.js        (CT volume atlas)                 -> PELVIS3D_VOL
  - pelvis3d_labels_data.js (prostate/PTV/bladder/rectum/SV/body)-> PELVIS3D_LABELS

pelvis3d is NOT a trainer case itself (the old Pelvis CBCT case was retired in favour of
the Gynae/Uterus case). It is the SOURCE VOLUME the two prostate generators consume:
  - generate_prostate_fiducials.py -> prostate3d_*  (implants 3 gold seeds; CBCT case)
  - generate_prostate_2d.py        -> prostate2d    (ray-sum kV AP/Lat; 2D fiducial case,
                                                      also the full-treatment tx:prostate case)
so re-sourcing it here re-licenses BOTH prostate cases in one place.

DATA
----
Source (licence verified CC BY 4.0 via the IDC idc-index):
  prostate_anatomical_edge_cases   https://doi.org/10.7937/qstf-st65
  patient Prostate-AEC-124: an RT SIMULATION planning CT ("Prostate SBRT", 1 mm) + its
  "Contouring" RTSTRUCT (Prostate / Bladder / Rectum / femoral heads).
Pulled from the NCI Imaging Data Commons bucket s3://idc-open-data via idc-index.

Same tiled-atlas format every *3d_data.js uses: an 8-bit grayscale PNG with the Z slices
tiled in a grid, base64'd into a data-URI, plus a JSON metadata header. Axis convention
dims=[x(LR),y(AP),z(SI)], x0=patient-right, y0=anterior, z0=inferior (matches the other cases).

The RTSTRUCT carries no PTV or seminal-vesicle ROI, so the PTV is synthesised (prostate + 5 mm,
standard SBRT margin) and the SV bit is left unused; the gold fiducial seeds are added later by
generate_prostate_fiducials.py. Nothing is destructively baked into the CT here.

USAGE
-----
  pip install pydicom numpy scipy pillow
  python generate_pelvis_volume.py --ct /path/to/CT_series_dir --rtstruct /path/to/RTSTRUCT.dcm
"""
import argparse, os, re, io, base64, math, glob
import numpy as np
from PIL import Image
from scipy import ndimage

try:
    import pydicom
except ImportError:
    raise SystemExit("pydicom is required:  pip install pydicom numpy scipy pillow")

TARGET_XY      = 192    # longest-axis resample size (px), matches the other *3d atlases.
TILES_PER_ROW  = 12     # atlas tiling (keeps the same tpr the old pelvis atlas used).
CROP_MARGIN_MM = 42     # superior-inferior margin around the pelvic-organ slab (scroll context).
BODY_MARGIN_MM = 8      # in-plane (LR/AP) skin margin around the BODY mask.

# HU -> density(0..255):  HU = density*(2000/255) - 500  =>  density = (HU+500)*255/2000.
HU_OFF, HU_SCALE = -500.0, 2000.0 / 255.0
def hu_to_density(hu):
    return np.clip((hu - HU_OFF) / HU_SCALE, 0, 255).astype(np.uint8)

# Bit layout consumed by generate_prostate_fiducials.py / trainer.html's prostate struct set.
STRUCT_BITS = {'prostate': 1, 'ptv': 2, 'bladder': 4, 'rectum': 8, 'sv': 16, 'body': 128}
ROI_ALIASES = [   # lowercased substring -> struct key (specific first, first match wins)
    ('seminal', 'sv'), ('vesicle', 'sv'),
    ('prostate', 'prostate'),
    ('bladder', 'bladder'),
    ('rectum', 'rectum'), ('rectal', 'rectum'),
    ('external', 'body'), ('body', 'body'), ('skin', 'body'),
]
def map_roi(name):
    n = re.sub(r'[^a-z0-9]', '', name.lower())
    for sub, key in ROI_ALIASES:
        if re.sub(r'[^a-z0-9]', '', sub) in n:
            return key
    return None   # femoral heads / couch / helper ROIs are ignored

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
    slices.sort(key=lambda s: float(s.ImagePositionPatient[2]))   # ascending z = inferior->superior
    ref = slices[0]
    ny, nx = int(ref.Rows), int(ref.Columns)
    px, py = float(ref.PixelSpacing[1]), float(ref.PixelSpacing[0])
    z = [float(s.ImagePositionPatient[2]) for s in slices]
    dz = float(np.median(np.diff(z))) if len(z) > 1 else float(getattr(ref, 'SliceThickness', 1))
    vol = np.zeros((len(slices), ny, nx), np.float32)
    for i, s in enumerate(slices):
        vol[i] = s.pixel_array.astype(np.float32) * float(getattr(s, 'RescaleSlope', 1)) \
                 + float(getattr(s, 'RescaleIntercept', 0))
    print(f"CT: {nx}x{ny}x{len(slices)}  in-plane {px:.3f}x{py:.3f} mm  dz {abs(dz):.3f} mm")
    return dict(hu=vol, nx=nx, ny=ny, nz=len(slices), px=px, py=py, dz=abs(dz),
                origin=np.array(ref.ImagePositionPatient, float), z0=z[0])

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
        print(f"   {nm:20s} -> {key}")
    for k in ('prostate', 'bladder', 'rectum'):    # solid organs from outline contours
        if masks[k].any():
            filled = np.array([ndimage.binary_fill_holes(masks[k][z]) for z in range(nz)])
            lb, n = ndimage.label(filled)           # drop stray mis-rasterised specks -> largest 3D blob
            if n > 1:
                sizes = np.bincount(lb.ravel()); sizes[0] = 0
                filled = lb == sizes.argmax()
            masks[k] = filled
    return masks

# --- crop + isotropic resample ----------------------------------------------
def resample(ct, masks):
    src = ct['hu']
    SZ, SY, SX = ct['nz'], ct['ny'], ct['nx']
    spz, spy, spx = ct['dz'], ct['py'], ct['px']
    organs = masks['prostate'] | masks['bladder'] | masks['rectum']
    zsel = np.where(organs.any(axis=(1, 2)))[0]
    mz = CROP_MARGIN_MM / spz
    z0, z1 = max(0, int(zsel.min() - mz)), min(SZ, int(zsel.max() + mz) + 1)
    bslab = masks['body'][z0:z1]
    ysel = np.where(bslab.any(axis=(0, 2)))[0]; xsel = np.where(bslab.any(axis=(0, 1)))[0]
    my, mx = BODY_MARGIN_MM / spy, BODY_MARGIN_MM / spx
    y0, y1 = max(0, int(ysel.min() - my)), min(SY, int(ysel.max() + my) + 1)
    x0, x1 = max(0, int(xsel.min() - mx)), min(SX, int(xsel.max() + mx) + 1)
    print(f"crop z[{z0}:{z1}] (organ slab) y[{y0}:{y1}] x[{x0}:{x1}] (body) of {SZ}x{SY}x{SX}")
    src = src[z0:z1, y0:y1, x0:x1]
    masks = {k: m[z0:z1, y0:y1, x0:x1] for k, m in masks.items()}
    CZ, CY, CX = src.shape
    phys = [CX * spx, CY * spy, CZ * spz]
    iso_sp = max(phys) / TARGET_XY
    OX, OY, OZ = (max(1, int(round(p / iso_sp))) for p in phys)
    zoom = (OZ / CZ, OY / CY, OX / CX)
    print(f"resample -> {OX}x{OY}x{OZ}  iso spacing {iso_sp:.3f} mm  phys {[round(p) for p in phys]}")
    ct_d = hu_to_density(ndimage.zoom(src, zoom, order=1))
    out = {}
    for k, m in masks.items():
        out[k] = (ndimage.zoom(m.astype(np.float32), zoom, order=1) > 0.5) if m.any() \
                 else np.zeros((OZ, OY, OX), bool)
    return ct_d, out, (OX, OY, OZ), iso_sp

def encode_atlas(vol, OX, OY, OZ, tpr):
    rows = math.ceil(OZ / tpr)
    out = np.zeros((rows * OY, tpr * OX), np.uint8)
    for z in range(OZ):
        out[(z//tpr)*OY:(z//tpr)*OY+OY, (z%tpr)*OX:(z%tpr)*OX+OX] = vol[z]
    buf = io.BytesIO(); Image.fromarray(out, 'L').save(buf, format='PNG', compress_level=9)
    return base64.b64encode(buf.getvalue()).decode('ascii'), len(buf.getvalue()), rows

ATTRIB = ('// Source: prostate_anatomical_edge_cases (via NCI Imaging Data Commons, s3://idc-open-data).\n'
          '// Licence: CC BY 4.0 (commercial use permitted with attribution).\n'
          '// Attribution: Prostate Anatomical Edge Cases, The Cancer Imaging Archive, doi:10.7937/qstf-st65.\n'
          '// De-identified prostate RT-planning CT (patient Prostate-AEC-124), cropped to the pelvis + isotropic atlas.\n')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ct', required=True, help='planning-CT DICOM series directory')
    ap.add_argument('--rtstruct', required=True, help='RTSTRUCT .dcm file')
    ap.add_argument('--qc', default='/tmp/pelvis_qc')
    args = ap.parse_args()

    ct = load_ct(args.ct)
    masks = rasterize(args.rtstruct, ct)
    if not masks['prostate'].any():
        raise SystemExit("No Prostate ROI rasterised — check the RTSTRUCT references this CT series.")

    # body: threshold the CT (RTSTRUCT has no external ROI), largest CC drops the couch.
    body = ndimage.binary_fill_holes(ct['hu'] > -350)
    body = ndimage.binary_opening(body, iterations=2)
    lbl, n = ndimage.label(body)
    if n > 1:
        sizes = np.bincount(lbl.ravel()); sizes[0] = 0
        body = lbl == sizes.argmax()
    masks['body'] = body

    # PTV = prostate + 5 mm (SBRT margin); RTSTRUCT carries no PTV ROI.
    ptv_it = max(1, int(round(5.0 / min(ct['px'], ct['py'], ct['dz']))))
    masks['ptv'] = ndimage.binary_dilation(masks['prostate'], iterations=ptv_it)

    ct_d, rmasks, (OX, OY, OZ), iso_sp = resample(ct, masks)

    zz, yy, xx = np.where(rmasks['prostate'])
    iso = [int(round(xx.mean())), int(round(yy.mean())), int(round(zz.mean()))]
    print(f"prostate {int(rmasks['prostate'].sum())} vox  iso(voxel)={iso}")

    labels = np.zeros((OZ, OY, OX), np.uint8)
    bits_present = {}
    for k, bit in STRUCT_BITS.items():
        if rmasks[k].any():
            labels[rmasks[k]] |= bit; bits_present[k] = bit
    print(f"bits present: {bits_present}")

    os.makedirs(args.qc, exist_ok=True)
    _qc(ct_d, rmasks, iso, args.qc)

    ct_b64, ct_sz, rows = encode_atlas(ct_d, OX, OY, OZ, TILES_PER_ROW)
    lbl_b64, lbl_sz, _  = encode_atlas(labels, OX, OY, OZ, TILES_PER_ROW)
    print(f"CT atlas {ct_sz//1024} KB   label atlas {lbl_sz//1024} KB")

    meta = (f'{{"dims": [{OX}, {OY}, {OZ}], "spacingMm": [{iso_sp:.4f}, {iso_sp:.4f}, {iso_sp:.4f}], '
            f'"physMm": [{OX*iso_sp:.2f}, {OY*iso_sp:.2f}, {OZ*iso_sp:.2f}], '
            f'"tilesPerRow": {TILES_PER_ROW}, "tileRows": {rows}, "boneThr": 0.4}}')
    with open('pelvis3d_data.js', 'w') as f:
        f.write(ATTRIB)
        f.write('// Prostate-centered pelvis CT; source volume for the prostate CBCT + 2D fiducial cases.\n')
        f.write('// dims=[x(LR),y(AP),z(SI)]  x0=patient-right  y0=anterior  z0=inferior\n')
        f.write(f'const PELVIS3D_VOL={meta};\n')
        f.write(f"PELVIS3D_VOL.atlas='data:image/png;base64,{ct_b64}';\n")

    bits_json = ', '.join(f'"{k}": {v}' for k, v in bits_present.items())
    lbl_meta = (f'{{"dims": [{OX}, {OY}, {OZ}], "spacingMm": [{iso_sp:.4f}, {iso_sp:.4f}, {iso_sp:.4f}], '
                f'"tilesPerRow": {TILES_PER_ROW}, "bits": {{{bits_json}}}, '
                f'"isoIdx": [{iso[0]}, {iso[1]}, {iso[2]}]}}')
    with open('pelvis3d_labels_data.js', 'w') as f:
        f.write(ATTRIB)
        f.write('// Pelvis plan labels: prostate/PTV(prostate+5mm)/bladder/rectum/body (SV bit reserved, unused).\n')
        f.write(f'const PELVIS3D_LABELS={lbl_meta};\n')
        f.write(f"PELVIS3D_LABELS.atlas='data:image/png;base64,{lbl_b64}';\n")
    print('wrote pelvis3d_data.js + pelvis3d_labels_data.js')
    print(f'QC stills in {args.qc}')

def _qc(ct_d, rmasks, iso, outdir):
    ix, iy, iz = iso
    overlay = {'prostate': (255, 80, 80), 'bladder': (80, 160, 255), 'rectum': (150, 110, 60), 'ptv': (255, 200, 60)}
    def rgb(g): return np.stack([g]*3, -1).astype(np.uint8)
    def draw(base, m2d):
        img = rgb(base)
        for k, col in overlay.items():
            m = m2d.get(k)
            if m is None or not m.any(): continue
            img[m ^ ndimage.binary_erosion(m)] = col
        return img
    ax = draw(ct_d[iz], {k: rmasks[k][iz] for k in overlay})
    co = draw(ct_d[:, iy, :][::-1], {k: rmasks[k][:, iy, :][::-1] for k in overlay})
    sa = draw(ct_d[:, :, ix][::-1], {k: rmasks[k][:, :, ix][::-1] for k in overlay})
    for nm, im in [('axial', ax), ('coronal', co), ('sagittal', sa)]:
        Image.fromarray(im).resize((im.shape[1]*3, im.shape[0]*3), Image.NEAREST).save(f'{outdir}/pelvis_{nm}.png')

if __name__ == '__main__':
    main()
