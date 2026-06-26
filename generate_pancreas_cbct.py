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
TARGET_XY   = 192      # longest-axis resample size (px). Other cases sit ~180-224.
TILES_PER_ROW = 10     # atlas tiling (10 cols x ceil(Z/10) rows), matches the others.
CROP_MARGIN_MM = 55    # superior-inferior margin around the contoured OARs (defines the abdominal slab).
BODY_MARGIN_MM = 8     # in-plane (LR/AP) skin margin around the BODY mask, so tissue isn't flush to the frame.
# These collections ship extended-FOV breath-hold CTs (abdomen up through the lungs). Crop the
# SUPERIOR-INFERIOR extent to the abdominal OARs (FOCUS_KEYS) so the pancreas region fills the slab
# at good resolution instead of being a thin slab of a 500 mm scan, but crop the IN-PLANE (LR/AP)
# extent to the BODY mask, not the OARs. The OARs are central, so an OAR-based in-plane crop sliced
# the patient's sides/back off the frame (the "cut off at edge" artefact); the body bbox keeps the
# whole torso cross-section in view. Keys here define the SI slab (body/lung/cord are context).
FOCUS_KEYS = ('ptv', 'stomach', 'duodenum', 'bowel', 'liver', 'kidney')

# HU -> density(0..255) model the trainer uses:  HU = density*(2000/255) - 500
#   => density = (HU + 500) * 255/2000 , clipped to [0,255].
HU_OFF, HU_SCALE = -500.0, 2000.0 / 255.0
def hu_to_density(hu):
    d = (hu - HU_OFF) / HU_SCALE
    return np.clip(d, 0, 255).astype(np.uint8)

# --- structure mapping -------------------------------------------------------
# Fixed bit layout consumed by trainer.html's PANCREAS_STRUCTS (uint8 -> 8 bits).
# The generator absorbs ROI-name variance; the trainer side stays fixed on these keys.
# Synthetic teaching PTV: this collection is OAR-only (no tumour ROI), so when no target ROI matches
# we synthesise an anatomically authentic head-of-pancreas tumour PTV via HU region-grow (see
# synth_ptv) — the trainer's targets are explicitly training values. This gives the case a realistic
# target to align to, placed in the pancreatic bed (anterior to the vertebra, posterior to the stomach).
STRUCT_BITS = {
    'body':     1,    # External/BODY (or thresholded if the RTSTRUCT lacks one)
    'ptv':      2,    # tumour target: real target ROI if present, else a synthetic teaching PTV
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
    ('ptv',      'ptv'), ('ctv', 'ptv'), ('gtv', 'ptv'), ('tumor','ptv'), ('tumour','ptv'),
    ('panc',     'ptv'),   # "Pancreas" ROI used as the soft-tissue target
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

# --- crop to the region of interest, then isotropic resample -----------------
def resample(ct, masks):
    src = ct['hu']
    SZ, SY, SX = ct['nz'], ct['ny'], ct['nx']
    spz, spy, spx = ct['dz'], ct['py'], ct['px']

    # Crop box (see CROP_MARGIN_MM / BODY_MARGIN_MM notes):
    #   z (superior-inferior): focus OARs + CROP_MARGIN_MM  -> abdominal slab centred on the GI region.
    #   x,y (in-plane LR/AP):  BODY mask + BODY_MARGIN_MM    -> full patient cross-section, never clipped.
    focus = np.zeros((SZ, SY, SX), bool)
    for k in FOCUS_KEYS:
        if k in masks and masks[k].any():
            focus |= masks[k]
    if focus.any():
        zsel = np.where(focus.any(axis=(1, 2)))[0]
        mz = CROP_MARGIN_MM/spz
        z0, z1 = max(0, int(zsel.min()-mz)), min(SZ, int(zsel.max()+mz)+1)
    else:
        z0, z1 = 0, SZ
        print("no focus OARs to crop on -> full z range")
    body = masks.get('body')
    if body is not None and body.any():
        bslab = body[z0:z1]                                    # body bbox within the abdominal slab
        ysel = np.where(bslab.any(axis=(0, 2)))[0]
        xsel = np.where(bslab.any(axis=(0, 1)))[0]
        my, mx = BODY_MARGIN_MM/spy, BODY_MARGIN_MM/spx
        y0, y1 = max(0, int(ysel.min()-my)), min(SY, int(ysel.max()+my)+1)
        x0, x1 = max(0, int(xsel.min()-mx)), min(SX, int(xsel.max()+mx)+1)
    else:
        y0, y1, x0, x1 = 0, SY, 0, SX
    print(f"crop z[{z0}:{z1}] (OAR slab) y[{y0}:{y1}] x[{x0}:{x1}] (body) of {SZ}x{SY}x{SX}")
    src = src[z0:z1, y0:y1, x0:x1]
    masks = {k: m[z0:z1, y0:y1, x0:x1] for k, m in masks.items()}
    CZ, CY, CX = src.shape

    # isotropic resample of the cropped region (one spacing for all axes -> no squish)
    phys = [CX*spx, CY*spy, CZ*spz]
    iso_sp = max(phys) / TARGET_XY
    OX = max(1, int(round(phys[0]/iso_sp)))
    OY = max(1, int(round(phys[1]/iso_sp)))
    OZ = max(1, int(round(phys[2]/iso_sp)))
    zoom = (OZ/CZ, OY/CY, OX/CX)
    print(f"resample -> {OX}x{OY}x{OZ}  iso spacing {iso_sp:.3f} mm  phys {[round(p) for p in phys]}")
    ct_d = hu_to_density(ndimage.zoom(src, zoom, order=1))
    out_masks = {}
    for k, m in masks.items():
        out_masks[k] = (ndimage.zoom(m.astype(np.float32), zoom, order=1) > 0.5) if m.any() \
                       else np.zeros((OZ, OY, OX), bool)
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

# --- synthetic, anatomically authentic head-of-pancreas tumour PTV -------------
def synth_ptv(ct_d, rmasks, HU, iso_sp, dims):
    """Anatomy-seeded HU region-grow -> head-of-pancreas tumour PTV (bool ndarray, shape OZ,OY,OX).

    Designed + adversarially judged against the real CT (regiongrow method). Axes: x=Left+,
    y=Posterior+, z=Superior+.
      1. Detect the vertebral body per slice (HU>250 central column) -> midline x, anterior edge y.
      2. Seed the GTV in the pancreatic bed: anterior to the vertebra, posterior to the stomach,
         shifted slightly to the patient's RIGHT (head of pancreas).
      3. Region-grow from the seed in soft-tissue HU [-25,80] (below contrast vessels), excluding
         stomach/bowel lumen + bone, within a focal ball -> organic GTV.
      4. PTV = uniform ~5 mm 3D ball margin; light smoothing; trim hard air/bone; kill thin slivers.
    """
    OX, OY, OZ = dims
    stomach = rmasks['stomach']; bowel = rmasks['bowel']
    bone = HU > 250

    # 1. vertebral body per slice (largest compact bone blob in the central column)
    cx_mid = OX / 2.0
    vb_cx, vb_yant = {}, {}
    lo, hi = int(cx_mid - 22), int(cx_mid + 22)
    for z in range(OZ):
        band = np.zeros((OY, OX), bool); band[:, lo:hi] = bone[z][:, lo:hi]
        if band.sum() < 30:
            continue
        lbl, n = ndimage.label(band)
        best = None
        for i in range(1, n + 1):
            ys, xs = np.where(lbl == i)
            if len(ys) < 30:
                continue
            if best is None or len(ys) > best[0]:
                best = (len(ys), xs.mean(), ys.min())
        if best is not None:
            vb_cx[z] = best[1]; vb_yant[z] = best[2]

    # 2. stomach (+duodenum) centroid / z-extent
    szz, syy, sxx = np.where(stomach)
    st_cy = syy.mean(); st_zlo, st_zhi = szz.min(), szz.max()

    # 3. seed in the pancreatic-head plane (mid/lower stomach block)
    z_lo = int(st_zlo + 0.20 * (st_zhi - st_zlo)); z_hi = int(st_zlo + 0.45 * (st_zhi - st_zlo))
    z_cands = [z for z in range(z_lo, z_hi) if z in vb_yant]
    z_seed = int(np.median(z_cands)) if z_cands else (z_lo + z_hi) // 2
    win = [z for z in range(z_seed - 6, z_seed + 7) if z in vb_yant]
    yant = np.median([vb_yant[z] for z in win]); midx = np.median([vb_cx[z] for z in win])
    y_seed = int(round(yant - 26 / iso_sp))             # ~26 mm anterior of the vertebra (off the vessels)
    y_seed = max(y_seed, int(st_cy + 12 / iso_sp))      # stay posterior to the stomach
    x_seed = int(round(midx - 6 / iso_sp))              # ~6 mm to the patient's right (head)

    # soft-tissue admissibility (cap below contrast vessels)
    soft = (HU >= -25) & (HU <= 80)
    lumen = stomach | bowel | (HU < -150)
    bone_d = ndimage.binary_dilation(bone, iterations=1)
    admit = soft & (~lumen) & (~bone_d)
    admit = ndimage.binary_closing(admit, structure=np.ones((1, 3, 3)), iterations=1)

    # snap seed to nearest admissible voxel
    if not admit[z_seed, y_seed, x_seed]:
        zz, yy, xx = np.where(admit[z_seed-3:z_seed+4, y_seed-6:y_seed+7, x_seed-6:x_seed+7])
        if len(zz):
            j = ((zz-3)**2 + (yy-6)**2 + (xx-6)**2).argmin()
            z_seed, y_seed, x_seed = z_seed-3+zz[j], y_seed-6+yy[j], x_seed-6+xx[j]

    # 4. region-grow inside a focal ball (slightly compressed SI)
    rvox = 18.0 / iso_sp
    zz, yy, xx = np.ogrid[0:OZ, 0:OY, 0:OX]
    ball = ((xx - x_seed)**2 + (yy - y_seed)**2 + ((zz - z_seed)*0.85)**2) <= rvox**2
    lbl, n = ndimage.label(admit & ball)
    seedlab = lbl[z_seed, y_seed, x_seed]
    if seedlab == 0:
        sub = lbl[z_seed-2:z_seed+3, y_seed-2:y_seed+3, x_seed-2:x_seed+3]; vals = sub[sub > 0]
        seedlab = int(np.bincount(vals).argmax()) if len(vals) else 0
    gtv = (lbl == seedlab) if seedlab else (admit & ball)

    # organic close + fill vessel holes + keep largest blob
    gtv = ndimage.binary_closing(gtv, structure=np.ones((3, 3, 3)), iterations=1)
    for z in range(OZ):
        if gtv[z].any():
            gtv[z] = ndimage.binary_fill_holes(gtv[z])
    lbl, n = ndimage.label(gtv)
    if n > 1:
        sizes = np.bincount(lbl.ravel()); sizes[0] = 0; gtv = lbl == sizes.argmax()

    # 5. uniform ~5 mm 3D ball margin -> PTV; smooth; trim hard air/bone
    r = int(round(5 / iso_sp)); rr = np.arange(-r, r + 1)
    ZB, YB, XB = np.meshgrid(rr, rr, rr, indexing='ij')
    ball_se = (ZB**2 + YB**2 + XB**2) <= r**2
    ptv = ndimage.binary_dilation(gtv, structure=ball_se)
    ptv = ndimage.binary_closing(ptv, structure=np.ones((3, 3, 3)), iterations=1)
    ptv = ptv & (~((HU < -200) | (HU > 300)))
    # light surface smoothing (removes sharp notches, keeps organic shape)
    ptv = ndimage.gaussian_filter(ptv.astype(np.float32), 0.8) > 0.45
    ptv = ptv & (~((HU < -200) | (HU > 300)))
    # kill thin inferior slivers: drop small per-slice fragments, then keep the largest 3D blob
    for z in range(OZ):
        if ptv[z].any():
            sl, m = ndimage.label(ptv[z])
            if m > 1:
                sz = np.bincount(sl.ravel()); sz[0] = 0
                ptv[z] = np.isin(sl, np.where(sz >= 25)[0])
    lbl, n = ndimage.label(ptv)
    if n > 1:
        sizes = np.bincount(lbl.ravel()); sizes[0] = 0; ptv = lbl == sizes.argmax()
    return ptv.astype(bool)

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
        # Keep only the largest connected component = the patient torso. The opening thins the
        # patient's contact with the CT couch enough to split them, so this drops the table/rails
        # (otherwise they widen the in-plane body bbox by ~150 mm, halving the atlas resolution and
        # painting the couch into the body contour).
        lbl, n = ndimage.label(body)
        if n > 1:
            sizes = np.bincount(lbl.ravel()); sizes[0] = 0
            body = lbl == sizes.argmax()
        masks['body'] = body

    ct_d, rmasks, (OX, OY, OZ), iso_sp, phys = resample(ct, masks)

    def centroid(mask):
        zz, yy, xx = np.where(mask)
        return [int(round(xx.mean())), int(round(yy.mean())), int(round(zz.mean()))]

    # PTV: use a real target ROI if one matched; otherwise synthesise an anatomically authentic
    # head-of-pancreas tumour PTV via HU region-grow (synth_ptv). iso = PTV centre.
    if rmasks['ptv'].any():
        iso = centroid(rmasks['ptv'])
        print(f"target ROI present -> using it as the PTV ({int(rmasks['ptv'].sum())} vox)")
    else:
        HU = ct_d.astype(np.float32) * (2000.0 / 255.0) - 500.0
        rmasks['ptv'] = synth_ptv(ct_d, rmasks, HU, iso_sp, (OX, OY, OZ))
        iso = centroid(rmasks['ptv'])
        vol_cc = rmasks['ptv'].sum() * iso_sp**3 / 1000
        print(f"no target ROI -> SYNTHETIC head-of-pancreas PTV via region-grow "
              f"({int(rmasks['ptv'].sum())} vox, {vol_cc:.1f} cc) centred {iso}")

    # build the packed label volume (OR of bits)
    labels = np.zeros((OZ, OY, OX), np.uint8)
    bits_present = {}
    for k, bit in STRUCT_BITS.items():
        if rmasks[k].any():
            labels[rmasks[k]] |= bit
            bits_present[k] = bit
    print(f"iso(voxel)={iso}  bits={bits_present}")

    ct_b64, ct_sz, rows = encode_atlas(ct_d, OX, OY, OZ, TILES_PER_ROW)
    lbl_b64, lbl_sz, _  = encode_atlas(labels, OX, OY, OZ, TILES_PER_ROW)
    print(f"CT atlas {ct_sz//1024} KB   label atlas {lbl_sz//1024} KB")

    meta = (f'{{"dims": [{OX}, {OY}, {OZ}], "spacingMm": [{iso_sp:.4f}, {iso_sp:.4f}, {iso_sp:.4f}], '
            f'"physMm": [{OX*iso_sp:.2f}, {OY*iso_sp:.2f}, {OZ*iso_sp:.2f}], '
            f'"tilesPerRow": {TILES_PER_ROW}, "tileRows": {rows}, "boneThr": 0.62}}')
    ATTRIB = ('// Source: TCIA Pancreatic-CT-CBCT-SEG (via NCI Imaging Data Commons, s3://idc-open-data).\n'
              '// Licence: CC BY 4.0 (commercial use permitted with attribution).\n'
              '// Attribution: Hong, J. et al., The Cancer Imaging Archive, doi:10.7937/TCIA.ESHQ-4D90.\n'
              '// De-identified breath-hold planning CT, cropped to the abdomen + resampled to an isotropic atlas.\n')
    with open('pancreas3d_data.js', 'w') as f:
        f.write(ATTRIB)
        f.write('// dims=[x(LR),y(AP),z(SI)]. Plain CT (no baked features); rigid 6DOF soft-tissue match.\n')
        f.write(f'const PANCREAS3D_VOL={meta};\n')
        f.write(f"PANCREAS3D_VOL.atlas='data:image/png;base64,{ct_b64}';\n")

    bits_json = ', '.join(f'"{k}": {v}' for k, v in bits_present.items())
    lbl_meta = (f'{{"dims": [{OX}, {OY}, {OZ}], "spacingMm": [{iso_sp:.4f}, {iso_sp:.4f}, {iso_sp:.4f}], '
                f'"tilesPerRow": {TILES_PER_ROW}, "bits": {{{bits_json}}}, '
                f'"isoIdx": [{iso[0]}, {iso[1]}, {iso[2]}]}}')
    with open('pancreas3d_labels_data.js', 'w') as f:
        f.write(ATTRIB)
        f.write('// Pancreas CBCT case labels: abdominal OAR contours from the RTSTRUCT (bits below).\n')
        f.write(f'const PANCREAS3D_LABELS={lbl_meta};\n')
        f.write(f"PANCREAS3D_LABELS.atlas='data:image/png;base64,{lbl_b64}';\n")
    print('wrote pancreas3d_data.js + pancreas3d_labels_data.js')
    print('Next: enable the picker card in trainer.html (see the // PANCREAS note) and '
          'verify the MPR panes + contours in Chrome/Edge.')

if __name__ == '__main__':
    main()
