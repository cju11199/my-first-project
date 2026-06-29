#!/usr/bin/env python3
"""
generate_hn_cbct.py
Build the Head & Neck CBCT case from an EAY131 (NCI-MATCH) patient — a contrast
neck CT + RTSTRUCT tumour annotations (pharynx/larynx primary + an involved neck
node) — and write
  - hn3d_data.js        (CT volume atlas)              -> HN3D_VOL
  - hn3d_labels_data.js (target + body label atlas)    -> HN3D_LABELS

Same tiled-atlas format every other CBCT case uses (cervix/liver/sarcoma/...):
an 8-bit grayscale PNG with the Z slices tiled in a grid, base64'd into a
data-URI, plus a small JSON metadata header. trainer.html (decodeVol /
_decodeHNLabels) reslices it into the 3 MPR panes; the "CBCT/moving" image is
SYNTHESISED by reslicing the same CT through a hidden 6DOF offset, so a real
second CBCT series is NOT needed — we only consume the planning CT + its
annotations.  Default CBCT branch (body + generic 'tumor' slot), rigid 6DOF
soft-tissue match against full cervical-spine / mandible / skull-base bony
anatomy (the H&N teaching point: register the whole rigid head & neck, soft
tissue and bone together — a daily-IGRT neck setup).

DATA
----
Source (licence CC BY 4.0 — commercial use OK with attribution):
  EAY131 / NCI-MATCH (ECOG-ACRIN)   https://doi.org/10.7937/c5ke-yx42
  patient EAY131-7978834: a 0.7 mm contrast neck CT (Neck_1_0_I26s_3) with a
  RECIST tumour annotation referencing it — "PHARYNX AND LARYNX - 1" (the
  soft-tissue primary, the match target).  Pulled from the NCI Imaging Data
  Commons bucket s3://idc-open-data via the idc-index PyPI package.

NOTE: this neck CT has NON-UNIFORM native slice spacing — a clean ~0.7 mm run
(~48 mm) through the primary target, but scattered LARGE gaps (12-51 mm)
elsewhere in the stack.  So, unlike the cervix template, we (1) resample the
volume + masks onto a uniform world-Z grid (linear interp per column) before
the in-plane crop / isotropic resample (ndimage.zoom assumes uniform spacing,
so feeding it the raw stack would be geometrically wrong), AND (2) CLIP the
superior-inferior slab to the largest contiguous clean native run (gaps
<= GAP_TOL_MM) that contains the target.  Without (2), a symmetric target
+/- 30 mm slab pulled ~46% of its slices out of the big gaps, which the
uniform-Z interpolation smeared along the SI axis -> visible vertical streaking
in the coronal/sagittal reformats.  The "LEFT NECK LYMPH NODE - 1" annotation
sits ~13 mm superior of the clean run inside a 12.6 mm gap, so it can't be
rendered cleanly from this series and is intentionally dropped (primary-only).

USAGE
-----
  pip install idc-index pydicom numpy scipy pillow
  python generate_hn_cbct.py --ct /path/to/CT_series_dir \
                             --rtstruct /path/RTSTRUCT_pharynx.dcm /path/RTSTRUCT_node.dcm
  # or point --rtdir at a folder and it auto-discovers every RTSTRUCT under it.
"""
import argparse, os, re, io, base64, math, glob
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

try:
    import pydicom
except ImportError:
    raise SystemExit("pydicom is required:  pip install pydicom numpy scipy pillow")

# --- output sizing (keep the atlas ~1.5-2 MB like the other *3d_data.js files) ---
TARGET_XY      = 192    # longest-axis resample size (px). Other cases sit ~180-224.
TILES_PER_ROW  = 10     # atlas tiling (10 cols x ceil(Z/10) rows), matches the others.
UNIFORM_DZ_MM  = 1.0    # uniform world-Z grid spacing the native stack is resampled onto.
CROP_MARGIN_MM = 30     # superior-inferior margin around the target -> neck slab w/ spine context.
BODY_MARGIN_MM = 8      # in-plane (LR/AP) skin margin around the BODY mask.
GAP_TOL_MM     = 1.5    # native gaps <= this are "clean"; the SI slab is clipped to the largest
                        # contiguous clean run containing the target so the reformats never
                        # interpolate across the big (12-51 mm) native slice gaps (-> through-plane
                        # smear).  This neck CT's clean ~0.7 mm run is ~48 mm and holds the primary.

# HU -> density(0..255):  HU = density*(2000/255) - 500  =>  density = (HU+500)*255/2000.
HU_OFF, HU_SCALE = -500.0, 2000.0 / 255.0
def hu_to_density(hu):
    return np.clip((hu - HU_OFF) / HU_SCALE, 0, 255).astype(np.uint8)

# Fixed bit layout consumed by trainer.html's HN struct set (uint8 -> 8 bits).
# The H&N target uses the generic 'tumor' key so it reuses the trainer's existing tumour
# legend / contour-menu slot (same as the liver / sarcoma / cervix soft-tissue cases).
STRUCT_BITS = {
    'body':  1,    # External/BODY (thresholded from the CT)
    'tumor': 2,    # the tumour target (pharynx/larynx primary)
}
# Lowercased substrings -> struct key (first match wins; specific first).
# NOTE: the LEFT NECK LYMPH NODE annotation is deliberately NOT mapped: it sits ~13 mm superior of
# the primary, inside a 12.6 mm native slice gap, so it can't be rendered cleanly from this series.
# We ship the pharynx/larynx primary only (a clean, fully-sampled target).
ROI_ALIASES = [
    ('pharynx', 'tumor'), ('larynx', 'tumor'),
    ('gtv', 'tumor'), ('ctv', 'tumor'), ('tumor', 'tumor'), ('tumour', 'tumor'),
    ('external', 'body'), ('body', 'body'), ('skin', 'body'),
]
# The pharynx primary is the dominant volume -> its centroid is the isocentre.
PRIMARY_SUBSTR = 'pharynx'

def map_roi(name):
    n = name.lower()
    if 'seed' in n:                     # skip the "- SEED POINT" RECIST helper ROIs
        return None
    nn = re.sub(r'[^a-z0-9]', '', n)
    for sub, key in ROI_ALIASES:
        if re.sub(r'[^a-z0-9]', '', sub) in nn:
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
    zs = np.array([float(s.ImagePositionPatient[2]) for s in slices], float)
    origin = np.array(ref.ImagePositionPatient, float)
    vol = np.zeros((len(slices), ny, nx), np.float32)
    for i, s in enumerate(slices):
        arr = s.pixel_array.astype(np.float32)
        vol[i] = arr * float(getattr(s, 'RescaleSlope', 1)) + float(getattr(s, 'RescaleIntercept', 0))
    dz_med = float(np.median(np.diff(zs)))
    print(f"CT: {nx}x{ny}x{len(slices)}  in-plane {px:.3f}x{py:.3f} mm  native dz median {dz_med:.3f} mm "
          f"(min {np.diff(zs).min():.2f} / max {np.diff(zs).max():.2f}) — NON-UNIFORM, will resample to {UNIFORM_DZ_MM} mm")
    return dict(hu=vol, nx=nx, ny=ny, nz=len(slices), px=px, py=py,
                zs=zs, origin=origin, z0=float(zs[0]), uid=str(ref.SeriesInstanceUID))

# --- RTSTRUCT rasterisation (on the NATIVE non-uniform stack) -----------------
def _poly_mask(poly, ny, nx):
    img = Image.new('L', (nx, ny), 0)
    ImageDraw.Draw(img).polygon([tuple(p) for p in poly], outline=1, fill=1)
    return np.array(img, bool)

def rasterize(rt_paths, ct):
    nz, ny, nx = ct['nz'], ct['ny'], ct['nx']
    px, py = ct['px'], ct['py']
    zs = ct['zs']
    ox, oy = ct['origin'][0], ct['origin'][1]
    masks = {k: np.zeros((nz, ny, nx), bool) for k in STRUCT_BITS}
    primary = np.zeros((nz, ny, nx), bool)     # pharynx-only, for the isocentre
    mapped = {}
    for rt_path in rt_paths:
        rt = pydicom.dcmread(rt_path, force=True)
        if getattr(rt, 'Modality', '') != 'RTSTRUCT':
            continue
        # does this RTSTRUCT reference our CT series? (skip the chest/abdo RECIST ones)
        try:
            ref = rt.ReferencedFrameOfReferenceSequence[0].RTReferencedStudySequence[0] \
                    .RTReferencedSeriesSequence[0].SeriesInstanceUID
            if str(ref) != ct['uid']:
                print(f"   (skip {os.path.basename(rt_path)} — references a different CT series)")
                continue
        except Exception:
            pass
        roi_names = {r.ROINumber: r.ROIName for r in rt.StructureSetROISequence}
        for roi in rt.ROIContourSequence:
            nm = roi_names.get(roi.ReferencedROINumber, f'ROI{roi.ReferencedROINumber}')
            key = map_roi(nm)
            mapped[nm] = key
            if key is None or not hasattr(roi, 'ContourSequence'):
                continue
            is_primary = PRIMARY_SUBSTR in nm.lower()
            for c in roi.ContourSequence:
                pts = np.array(c.ContourData, float).reshape(-1, 3)
                zi = int(np.argmin(np.abs(zs - pts[:, 2].mean())))   # nearest native slice
                col = (pts[:, 0] - ox) / px
                row = (pts[:, 1] - oy) / py
                m2d = _poly_mask(np.stack([col, row], 1), ny, nx)
                masks[key][zi] |= m2d
                if key == 'tumor' and is_primary:
                    primary[zi] |= m2d
    print("ROI mapping:")
    for nm, key in sorted(mapped.items()):
        print(f"   {nm:36s} -> {key}")
    return masks, primary

# --- resample native non-uniform stack -> uniform world-Z grid ---------------
def to_uniform_z(arr_f, zs, grid):
    """Linear-interpolate a (Z,Y,X) float array from native zs onto uniform `grid` z's."""
    order = np.argsort(zs)
    zss = zs[order]; src = arr_f[order]
    out = np.empty((len(grid), arr_f.shape[1], arr_f.shape[2]), np.float32)
    for j, g in enumerate(grid):
        k = int(np.clip(np.searchsorted(zss, g), 1, len(zss) - 1))
        z0, z1 = zss[k - 1], zss[k]
        t = (g - z0) / (z1 - z0) if z1 > z0 else 0.0
        out[j] = (1 - t) * src[k - 1] + t * src[k]
    return out

def clean_run_bounds(zs, tgt_lo, tgt_hi, gap_tol=GAP_TOL_MM):
    """World-Z bounds of the largest contiguous native run (every gap <= gap_tol) that holds the
    target.  Used to clip the SI slab so reformats never interpolate across the big native gaps."""
    z = np.sort(zs)
    gaps = np.diff(z)
    runs, start = [], 0
    for i, g in enumerate(gaps):
        if g > gap_tol:
            runs.append((start, i)); start = i + 1
    runs.append((start, len(z) - 1))
    tc = 0.5 * (tgt_lo + tgt_hi)
    for a, b in runs:                                  # run covering the target centroid
        if z[a] <= tc <= z[b]:
            return float(z[a]), float(z[b])
    a, b = max(runs, key=lambda r: z[r[1]] - z[r[0]])  # fallback: largest run
    return float(z[a]), float(z[b])

def uniformise(ct, masks, primary):
    zs = ct['zs']
    grid = np.arange(zs.min(), zs.max() + 1e-3, UNIFORM_DZ_MM)
    hu = to_uniform_z(ct['hu'], zs, grid)
    um = {k: to_uniform_z(m.astype(np.float32), zs, grid) > 0.5 for k, m in masks.items()}
    uprim = to_uniform_z(primary.astype(np.float32), zs, grid) > 0.5
    # clean contiguous native run holding the primary target -> world-Z bounds to clip the SI slab
    pz = np.where(primary.any(axis=(1, 2)))[0] if primary.any() else np.where(um['tumor'].any(axis=(1,2)))[0]
    ptgt = (float(zs[pz.min()]), float(zs[pz.max()])) if pz.size else (float(zs.min()), float(zs.max()))
    clean = clean_run_bounds(zs, *ptgt)
    print(f"uniform-Z resample: {ct['nz']} native -> {len(grid)} slices @ {UNIFORM_DZ_MM} mm")
    print(f"clean native run (gaps<= {GAP_TOL_MM} mm) world-Z [{clean[0]:.1f}, {clean[1]:.1f}] "
          f"({clean[1]-clean[0]:.1f} mm) — SI slab will be clipped to this")
    ct = dict(ct); ct['hu'] = hu; ct['nz'] = len(grid); ct['dz'] = UNIFORM_DZ_MM
    ct['z_uniform0'] = float(grid[0]); ct['clean_z'] = clean
    return ct, um, uprim

# --- crop + isotropic resample ----------------------------------------------
def resample(ct, masks, primary):
    src = ct['hu']
    SZ, SY, SX = ct['nz'], ct['ny'], ct['nx']
    spz, spy, spx = ct['dz'], ct['py'], ct['px']
    tgt = masks['tumor']
    if tgt.any():
        zsel = np.where(tgt.any(axis=(1, 2)))[0]
        mz = CROP_MARGIN_MM / spz
        z0, z1 = max(0, int(zsel.min() - mz)), min(SZ, int(zsel.max() + mz) + 1)
    else:
        z0, z1 = 0, SZ
    # clip the SI slab to the clean contiguous native run (no interpolation across big native gaps)
    clean = ct.get('clean_z')
    if clean is not None:
        g0 = int(round((clean[0] - ct['z_uniform0']) / spz))
        g1 = int(round((clean[1] - ct['z_uniform0']) / spz)) + 1
        z0, z1 = max(z0, g0), min(z1, g1)
        print(f"  SI slab clipped to clean run -> z[{z0}:{z1}] (was target +/- {CROP_MARGIN_MM} mm)")
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
    print(f"crop z[{z0}:{z1}] (neck slab) y[{y0}:{y1}] x[{x0}:{x1}] (body) of {SZ}x{SY}x{SX}")
    src = src[z0:z1, y0:y1, x0:x1]
    masks = {k: m[z0:z1, y0:y1, x0:x1] for k, m in masks.items()}
    primary = primary[z0:z1, y0:y1, x0:x1]
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
    out_prim = (ndimage.zoom(primary.astype(np.float32), zoom, order=1) > 0.5) if primary.any() \
               else out_masks['tumor']
    return ct_d, out_masks, out_prim, (OX, OY, OZ), iso_sp

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
    ap.add_argument('--rtstruct', nargs='*', default=[], help='RTSTRUCT .dcm file(s)')
    ap.add_argument('--rtdir', help='folder to auto-discover every RTSTRUCT under')
    ap.add_argument('--qc', default='/tmp/hn_qc', help='QC stills output dir')
    args = ap.parse_args()

    rt_paths = list(args.rtstruct)
    if args.rtdir:
        for f in glob.glob(os.path.join(args.rtdir, '**', '*'), recursive=True):
            if not os.path.isfile(f):
                continue
            try:
                if getattr(pydicom.dcmread(f, force=True, stop_before_pixels=True), 'Modality', '') == 'RTSTRUCT':
                    rt_paths.append(f)
            except Exception:
                pass
    if not rt_paths:
        raise SystemExit("No RTSTRUCT given (use --rtstruct or --rtdir)")
    print(f"RTSTRUCTs: {[os.path.basename(p) for p in rt_paths]}")

    ct = load_ct(args.ct)
    masks, primary = rasterize(rt_paths, ct)
    if not masks['tumor'].any():
        raise SystemExit("No tumour target rasterised — check the RTSTRUCT(s) reference this CT series.")

    # body: threshold the CT (no external ROI in a tumour-annotation RTSTRUCT)
    print("thresholding the CT for a body mask")
    body = ndimage.binary_fill_holes(ct['hu'] > -350)
    body = ndimage.binary_opening(body, iterations=2)
    lbl, n = ndimage.label(body)
    if n > 1:
        sizes = np.bincount(lbl.ravel()); sizes[0] = 0
        body = lbl == sizes.argmax()           # largest CC = head/neck (drops the couch/headrest)
    masks['body'] = body

    # resample native non-uniform stack -> uniform world-Z grid before in-plane work
    ct, masks, primary = uniformise(ct, masks, primary)

    ct_d, rmasks, rprim, (OX, OY, OZ), iso_sp = resample(ct, masks, primary)

    def centroid(mask):
        zz, yy, xx = np.where(mask)
        return [int(round(xx.mean())), int(round(yy.mean())), int(round(zz.mean()))]
    iso = centroid(rprim if rprim.any() else rmasks['tumor'])
    vol_cc = rmasks['tumor'].sum() * iso_sp**3 / 1000
    print(f"H&N target {int(rmasks['tumor'].sum())} vox ({vol_cc:.1f} cc) — iso at pharynx centroid {iso}")

    labels = np.zeros((OZ, OY, OX), np.uint8)
    bits_present = {}
    for k, bit in STRUCT_BITS.items():
        if rmasks[k].any():
            labels[rmasks[k]] |= bit; bits_present[k] = bit
    print(f"iso(voxel)={iso}  bits={bits_present}")

    os.makedirs(args.qc, exist_ok=True)
    _qc(ct_d, rmasks, iso, args.qc)

    ct_b64, ct_sz, rows = encode_atlas(ct_d, OX, OY, OZ, TILES_PER_ROW)
    lbl_b64, lbl_sz, _  = encode_atlas(labels, OX, OY, OZ, TILES_PER_ROW)
    print(f"CT atlas {ct_sz//1024} KB   label atlas {lbl_sz//1024} KB")

    meta = (f'{{"dims": [{OX}, {OY}, {OZ}], "spacingMm": [{iso_sp:.4f}, {iso_sp:.4f}, {iso_sp:.4f}], '
            f'"physMm": [{OX*iso_sp:.2f}, {OY*iso_sp:.2f}, {OZ*iso_sp:.2f}], '
            f'"tilesPerRow": {TILES_PER_ROW}, "tileRows": {rows}, "boneThr": 0.62}}')
    ATTRIB = ('// Source: EAY131 / NCI-MATCH (ECOG-ACRIN; via NCI Imaging Data Commons, s3://idc-open-data).\n'
              '// Licence: CC BY 4.0 (commercial use permitted with attribution).\n'
              '// Attribution: ECOG-ACRIN Cancer Research Group, EAY131 / NCI-MATCH,\n'
              '//   The Cancer Imaging Archive, doi:10.7937/c5ke-yx42.\n'
              '// De-identified contrast neck CT (patient EAY131-7978834), resampled to a uniform\n'
              '// world-Z grid, cropped to the neck + resampled to an isotropic atlas.\n')
    with open('hn3d_data.js', 'w') as f:
        f.write(ATTRIB)
        f.write('// dims=[x(LR),y(AP),z(SI)]. Plain CT (no baked features); rigid 6DOF match (head & neck).\n')
        f.write(f'const HN3D_VOL={meta};\n')
        f.write(f"HN3D_VOL.atlas='data:image/png;base64,{ct_b64}';\n")

    bits_json = ', '.join(f'"{k}": {v}' for k, v in bits_present.items())
    lbl_meta = (f'{{"dims": [{OX}, {OY}, {OZ}], "spacingMm": [{iso_sp:.4f}, {iso_sp:.4f}, {iso_sp:.4f}], '
                f'"tilesPerRow": {TILES_PER_ROW}, "bits": {{{bits_json}}}, '
                f'"isoIdx": [{iso[0]}, {iso[1]}, {iso[2]}]}}')
    with open('hn3d_labels_data.js', 'w') as f:
        f.write(ATTRIB)
        f.write('// Head & Neck CBCT case labels: pharynx/larynx primary + involved node (bit "tumor") + thresholded body.\n')
        f.write(f'const HN3D_LABELS={lbl_meta};\n')
        f.write(f"HN3D_LABELS.atlas='data:image/png;base64,{lbl_b64}';\n")
    print('wrote hn3d_data.js + hn3d_labels_data.js')
    print(f'QC stills in {args.qc} — review before wiring trainer.html.')

def _qc(ct_d, rmasks, iso, outdir):
    ix, iy, iz = iso
    overlay = {'tumor': (255, 60, 60), 'body': (60, 220, 100)}
    def rgb(gray):
        return np.stack([gray]*3, -1).astype(np.uint8)
    def draw(base, masks2d):
        img = rgb(base)
        for k, col in overlay.items():
            m = masks2d.get(k)
            if m is None or not m.any():
                continue
            edge = m ^ ndimage.binary_erosion(m)
            img[edge] = col
        return img
    ax = draw(ct_d[iz], {k: rmasks[k][iz] for k in overlay})
    co = draw(ct_d[:, iy, :][::-1], {k: rmasks[k][:, iy, :][::-1] for k in overlay})
    sa = draw(ct_d[:, :, ix][::-1], {k: rmasks[k][:, :, ix][::-1] for k in overlay})
    for nm, im in [('axial', ax), ('coronal', co), ('sagittal', sa)]:
        Image.fromarray(im).resize((im.shape[1]*3, im.shape[0]*3), Image.NEAREST).save(f'{outdir}/hn_{nm}.png')

if __name__ == '__main__':
    main()
