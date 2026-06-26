#!/usr/bin/env python3
"""
generate_pancreas_cbct.py
Build the Pancreas CBCT case from a TCIA Pancreatic-CT-CBCT-SEG patient
(planning breath-hold CT + its RTSTRUCT organ-at-risk contours) and write
  - pancreas3d_data.js        (CT volume atlas)            -> PANCREAS3D_VOL
  - pancreas3d_labels_data.js (OAR + target label atlas)   -> PANCREAS3D_LABELS

These two files are the SAME format the trainer already consumes for every
other CBCT case (pelvis/brain/breast/spine/lung/prostate): an 8-bit grayscale
PNG "atlas" with the Z slices tiled in a grid, base64'd into a data-URI, plus a
small JSON metadata header. trainer.html (decodeVol / _decode*Labels) reslices
it into the 3 MPR panes; the "CBCT/moving" image is SYNTHESISED by reslicing the
same CT through a hidden 6DOF offset, so a real second CBCT series is NOT needed
here — we only consume the planning CT + its RTSTRUCT.

DATA
----
Download one patient from the TCIA collection (confirm the licence is CC BY
first — see README "Pancreas CBCT case"):
  Pancreatic-CT-CBCT-SEG  https://doi.org/10.7937/TCIA.ESHQ-4D90
You need that patient's planning-CT DICOM series folder and its RTSTRUCT file.

USAGE
-----
  pip install pydicom numpy scipy pillow
  python generate_pancreas_cbct.py --ct /path/to/CT_series_dir \
                                   --rtstruct /path/to/RTSTRUCT.dcm

The script PRINTS every ROI name it finds and how it mapped it, so on the first
run you can see exactly what the RTSTRUCT contains and adjust ROI_ALIASES below
if a structure didn't match. Nothing is baked destructively into the CT (unlike
the fiducial cases) — this is a plain rigid 6DOF soft-tissue match.

TEACHING POINT
--------------
Upper-abdominal anatomy moves with breathing and GI filling, so the student
aligns on the soft-tissue pancreas/target and watches the duodenum, stomach,
bowel and kidneys — not just the spine. (Both scans here are deep-inspiration
breath-hold, so a rigid match is clinically appropriate; an off-bone differential
-motion variant, like the lung case, is a possible future enhancement.)
"""
import argparse, os, re, io, base64, math, glob
import numpy as np
from PIL import Image
from scipy import ndimage

try:
    import pydicom
except ImportError:
    raise SystemExit("pydicom is required:  pip install pydicom numpy scipy pillow")

# --- output sizing (keep the atlas ~1.5 MB like the other *3d_data.js files) ---
TARGET_XY   = 192      # in-plane resample size (px). Other cases sit ~180-224.
TARGET_Z    = 96       # number of axial slices after resample (isotropic-ish).
TILES_PER_ROW = 10     # atlas tiling (10 cols x ceil(Z/10) rows), matches the others.

# HU -> density(0..255) model the trainer uses:  HU = density*(2000/255) - 500
#   => density = (HU + 500) * 255/2000 , clipped to [0,255].
HU_OFF, HU_SCALE = -500.0, 2000.0 / 255.0
def hu_to_density(hu):
    d = (hu - HU_OFF) / HU_SCALE
    return np.clip(d, 0, 255).astype(np.uint8)

# --- structure mapping -------------------------------------------------------
# Fixed bit layout consumed by trainer.html's PANCREAS_STRUCTS (uint8 -> 8 bits).
# The generator absorbs ROI-name variance; the trainer side stays fixed on these keys.
STRUCT_BITS = {
    'body':     1,    # External/BODY (or thresholded if the RTSTRUCT lacks one)
    'target':   2,    # the pancreas / CTV / GTV / tumour bed  -> iso source
    'duodenum': 4,
    'stomach':  8,
    'bowel':    16,   # small + large bowel merged
    'liver':    32,
    'kidney':   64,   # left + right kidney merged
    'cord':     128,  # spinal cord / canal
}
# Lowercased substrings -> struct key. First match wins; order matters (specific first).
ROI_ALIASES = [
    ('duoden',   'duodenum'),
    ('stomach',  'stomach'),
    ('smallbowel','bowel'), ('small_bowel','bowel'), ('largebowel','bowel'),
    ('large_bowel','bowel'), ('bowel','bowel'), ('colon','bowel'), ('intestine','bowel'),
    ('liver',    'liver'),
    ('kidney',   'kidney'), ('renal', 'kidney'),
    ('spinalcord','cord'), ('spinal_cord','cord'), ('cord','cord'), ('canal','cord'),
    # target / tumour: try the most specific clinical names first
    ('ctv',      'target'), ('gtv', 'target'), ('tumor','target'), ('tumour','target'),
    ('panc',     'target'),   # "Pancreas" ROI used as the soft-tissue target
    # body / external last so it can't steal a more specific match
    ('external', 'body'), ('body', 'body'), ('skin','body'), ('patient','body'),
]
def map_roi(name):
    n = re.sub(r'[^a-z0-9]', '', name.lower())
    for sub, key in ROI_ALIASES:
        if re.sub(r'[^a-z0-9]', '', sub) in n:
            return key
    return None

# --- CT series loading -------------------------------------------------------
def load_ct(ct_dir):
    files = [f for f in glob.glob(os.path.join(ct_dir, '**', '*'), recursive=True)
             if os.path.isfile(f)]
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
    origin = np.array(ref.ImagePositionPatient, float)         # patient mm of voxel (0,0,0)
    vol = np.zeros((len(slices), ny, nx), np.float32)
    for i, s in enumerate(slices):
        arr = s.pixel_array.astype(np.float32)
        arr = arr * float(getattr(s, 'RescaleSlope', 1)) + float(getattr(s, 'RescaleIntercept', 0))
        vol[i] = arr                                           # HU
    print(f"CT: {nx}x{ny}x{len(slices)}  in-plane {px:.3f}x{py:.3f} mm  dz {abs(dz):.3f} mm")
    return dict(hu=vol, nx=nx, ny=ny, nz=len(slices), px=px, py=py, dz=abs(dz),
                origin=origin, z0=z[0], iop=np.array(ref.ImageOrientationPatient, float))

# --- RTSTRUCT rasterisation --------------------------------------------------
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
            zc = pts[:, 2]
            zi = int(round((zc.mean() - z0) / dz))
            if zi < 0 or zi >= nz:
                continue
            # patient mm -> pixel col/row (axial, standard HFS orientation)
            col = (pts[:, 0] - ox) / px
            row = (pts[:, 1] - oy) / py
            poly = np.stack([col, row], 1)
            m = _poly_mask(poly, ny, nx)
            masks[key][zi] |= m
    print("ROI mapping:")
    for nm, key in sorted(mapped.items()):
        print(f"   {nm:32s} -> {key}")
    return masks

def _poly_mask(poly, ny, nx):
    """Even-odd polygon fill onto an (ny,nx) grid."""
    from PIL import ImageDraw
    img = Image.new('L', (nx, ny), 0)
    ImageDraw.Draw(img).polygon([tuple(p) for p in poly], outline=1, fill=1)
    return np.array(img, bool)

# --- isotropic resample to the target grid -----------------------------------
def resample(ct, masks):
    src = ct['hu']
    SZ, SY, SX = ct['nz'], ct['ny'], ct['nx']
    # physical extent (mm)
    phys = [SX * ct['px'], SY * ct['py'], SZ * ct['dz']]
    iso_sp = max(phys) / TARGET_XY                                 # one isotropic spacing
    OX = max(1, int(round(phys[0] / iso_sp)))
    OY = max(1, int(round(phys[1] / iso_sp)))
    OZ = TARGET_Z
    zoom = (OZ / SZ, OY / SY, OX / SX)
    print(f"resample -> {OX}x{OY}x{OZ}  iso spacing {iso_sp:.3f} mm  phys {phys}")
    ct_d = hu_to_density(ndimage.zoom(src, zoom, order=1))
    out_masks = {}
    for k, m in masks.items():
        if m.any():
            out_masks[k] = ndimage.zoom(m.astype(np.float32), zoom, order=1) > 0.5
        else:
            out_masks[k] = np.zeros((OZ, OY, OX), bool)
    return ct_d, out_masks, (OX, OY, OZ), iso_sp, phys

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
    ap.add_argument('--rtstruct', required=True, help='RTSTRUCT .dcm file')
    args = ap.parse_args()

    ct = load_ct(args.ct)
    masks = rasterize(args.rtstruct, ct)

    # If the RTSTRUCT had no body/external ROI, synthesise one by thresholding the CT.
    if not masks['body'].any():
        print("no body/external ROI -> thresholding the CT for a body mask")
        body = ndimage.binary_fill_holes(ct['hu'] > -350)
        body = ndimage.binary_opening(body, iterations=2)
        masks['body'] = body

    ct_d, rmasks, (OX, OY, OZ), iso_sp, phys = resample(ct, masks)

    # build the packed label volume (OR of bits)
    labels = np.zeros((OZ, OY, OX), np.uint8)
    bits_present = {}
    for k, bit in STRUCT_BITS.items():
        if rmasks[k].any():
            labels[rmasks[k]] |= bit
            bits_present[k] = bit
    if 'body' in bits_present and bits_present == {'body': 1}:
        print("WARNING: only a body mask was produced — check ROI_ALIASES against the printed ROI list")

    # isocentre = target centroid (fallback: centre of everything contoured, else volume centre)
    def centroid(mask):
        zz, yy, xx = np.where(mask)
        return [int(round(xx.mean())), int(round(yy.mean())), int(round(zz.mean()))]
    if rmasks['target'].any():
        iso = centroid(rmasks['target'])
    else:
        any_oar = np.zeros((OZ, OY, OX), bool)
        for k in ('duodenum', 'stomach', 'bowel', 'liver', 'kidney'):
            any_oar |= rmasks[k]
        iso = centroid(any_oar) if any_oar.any() else [OX//2, OY//2, OZ//2]
        print("WARNING: no target ROI matched — iso set from OAR/volume centre; "
              "set a target by adding the pancreas/CTV ROI name to ROI_ALIASES")
    print(f"iso(voxel)={iso}  bits={bits_present}")

    ct_b64, ct_sz, rows = encode_atlas(ct_d, OX, OY, OZ, TILES_PER_ROW)
    lbl_b64, lbl_sz, _  = encode_atlas(labels, OX, OY, OZ, TILES_PER_ROW)
    print(f"CT atlas {ct_sz//1024} KB   label atlas {lbl_sz//1024} KB")

    meta = (f'{{"dims": [{OX}, {OY}, {OZ}], "spacingMm": [{iso_sp:.4f}, {iso_sp:.4f}, {iso_sp:.4f}], '
            f'"physMm": [{OX*iso_sp:.2f}, {OY*iso_sp:.2f}, {OZ*iso_sp:.2f}], '
            f'"tilesPerRow": {TILES_PER_ROW}, "tileRows": {rows}, "boneThr": 0.62}}')
    with open('pancreas3d_data.js', 'w') as f:
        f.write('// Pancreas (TCIA Pancreatic-CT-CBCT-SEG) breath-hold planning CT, resampled to an\n')
        f.write('// isotropic atlas. dims=[x(LR),y(AP),z(SI)]. Plain CT (no baked features); rigid 6DOF.\n')
        f.write(f'const PANCREAS3D_VOL={meta};\n')
        f.write(f"PANCREAS3D_VOL.atlas='data:image/png;base64,{ct_b64}';\n")

    bits_json = ', '.join(f'"{k}": {v}' for k, v in bits_present.items())
    lbl_meta = (f'{{"dims": [{OX}, {OY}, {OZ}], "spacingMm": [{iso_sp:.4f}, {iso_sp:.4f}, {iso_sp:.4f}], '
                f'"tilesPerRow": {TILES_PER_ROW}, "bits": {{{bits_json}}}, '
                f'"isoIdx": [{iso[0]}, {iso[1]}, {iso[2]}]}}')
    with open('pancreas3d_labels_data.js', 'w') as f:
        f.write('// Pancreas CBCT case labels: pancreas/target + abdominal OAR contours from the RTSTRUCT.\n')
        f.write(f'const PANCREAS3D_LABELS={lbl_meta};\n')
        f.write(f"PANCREAS3D_LABELS.atlas='data:image/png;base64,{lbl_b64}';\n")
    print('wrote pancreas3d_data.js + pancreas3d_labels_data.js')
    print('Next: enable the picker card in trainer.html (see the // PANCREAS note) and '
          'verify the MPR panes + contours in Chrome/Edge.')

if __name__ == '__main__':
    main()
