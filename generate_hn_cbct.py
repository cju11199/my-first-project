#!/usr/bin/env python3
"""
generate_hn_cbct.py
Build the **Head & Neck CBCT** case from the SAME clean full-head patient as the 2D/2D H&N case —
TCIA **TCGA-THCA** patient **TCGA-DE-A4MA** ("CT HeadNeck 3.0 B31s") — and write
  - hn3d_data.js        (CT volume atlas)           -> HN3D_VOL
  - hn3d_labels_data.js (target + body label atlas) -> HN3D_LABELS

Same tiled-atlas format every other CBCT case uses (z-major tiles, X=LR cols, Y=AP rows; bits
body=1 / tumor=2). trainer.html (decodeVol / _decodeHNLabels) reslices it into the 3 MPR panes;
the "CBCT/moving" image is SYNTHESISED by reslicing the same CT through a hidden 6DOF offset, so a
real second CBCT series is NOT needed. Default H&N CBCT branch: rigid 6DOF match over the whole
cervical-spine / mandible / skull-base bony anatomy (a daily-IGRT neck setup) with a soft-tissue
target in the generic `tumor` slot.

HISTORY / SOURCE
----------------
This case was RE-SOURCED off the original EAY131 / NCI-MATCH neck CT (which had non-uniform native
slice spacing and only a partial-head FOV) onto TCGA-DE-A4MA, the clean uniform-1.5 mm axial HFS CT
that now also drives the 2D/2D H&N case — so the two H&N cases are the SAME patient, the FOV spans
the full cranial vault down through the neck, and there is no de-ID redaction box.

TCGA-THCA is a thyroid-cancer staging cohort whose CTs carry NO tumour RTSTRUCT/SEG, so the
soft-tissue **target is SYNTHESISED** — a smooth ~1.8 cm ellipsoidal node placed in a realistic
level-II cervical-nodal location (lateral to the pharynx, below the mandible). This is consistent
with the trainer's other synthetic targets (the lung nodule, the spine PTV) and with its
"all values are fictional / educational use only" framing; the match itself is a rigid 6DOF
registration of the real bony head & neck, the synthetic node just defines the isocentre/contour.

USAGE
-----
  pip install idc-index pydicom numpy scipy pillow
  python generate_hn_cbct.py            # defaults to the scratchpad CT dir below
  python generate_hn_cbct.py --ct /path/to/TCGA-DE-A4MA/CT_series_dir

Licence: TCIA TCGA-THCA, CC BY 3.0 — attribute doi:10.7937/k9/tcia.2016.9zfrvf1b.
"""
import argparse, os, io, base64, math, glob
import numpy as np
from PIL import Image
from scipy import ndimage

try:
    import pydicom
except ImportError:
    raise SystemExit("pydicom is required:  pip install pydicom numpy scipy pillow")

# --- output sizing (keep the atlas ~1.5-2 MB like the other *3d_data.js files) ---
TARGET_XY      = 192    # longest-axis resample size (px).
TILES_PER_ROW  = 10     # atlas tiling (10 cols x ceil(Z/10) rows), matches the others.
CROP_MARGIN_MM = 22     # superior-inferior half-slab of context above/below the (neck-spanning) target
                        # -> a realistic daily H&N CBCT longitudinal FOV (skull base + upper thorax).
BODY_MARGIN_MM = 8      # in-plane (LR/AP) skin margin around the BODY mask.

# Synthetic BILATERAL cervical-nodal PTV (no tumour ROI in TCGA-THCA): an anterior-convex horseshoe/U
# of two jugular-chain lobes (levels II-IV both sides) joined by a thin anterior bridge, carving out the
# central airway + the posterior spinal cord / vertebral body. Geometry from an ultracode design
# workflow (radonc + geometry proposals, judged + synthesised). Bounded to the CERVICAL z-window
# (the source CT is the full cranial vault, so a whole-head span would drape the PTV over the brain).
Z_FRAC_LO, Z_FRAC_HI = 0.30, 0.72   # cervical build window (skull base/C1 -> low neck/supraclav)
ISO_Z_FRAC   = 0.51     # iso SI hint within the window (~C3-C4); iso is recomputed post-resample anyway.
LOBE_RX_MM, LOBE_RY_MM = 13.0, 16.0 # lobe in-plane semi-axes (LR / AP) — ~26x32 mm jugular-chain lobe.
AP_BIAS      = -0.05    # lobe AP centre, fraction of body AP depth ANTERIOR of the body centroid.
BRIDGE_THICK_MM = 8.0   # AP thickness of the thin anterior bridge joining the two lobes across the front.
SKIN_MARGIN_MM  = 4.0   # inset of lobes/bridge from the anterior skin surface.
BODY_ERODE_MM   = 3.0   # erode body -> body_in; the PTV is constrained inside this (never reaches skin).
SPINE_HW_MM     = 12.0  # half-width of the posterior-central cord/vertebral-body keep-out column.
POST_CUT_FRAC   = 0.22  # posterior cutoff = cy + frac*AP_depth; drop voxels behind it (U stays open).
AIRWAY_PAD_MM   = 5.0   # dilation of the detected airway CC before subtraction (keeps the U's mouth clear).
TAPER_N         = 4     # top/bottom slices over which lobe radii + bridge taper for rounded SI caps.
SOFT_HU = (-50, 250)    # soft-tissue HU window (no airway / bone); BONE_HU>250, AIR_HU<-500.

# HU -> density(0..255):  HU = density*(2000/255) - 500  =>  density = (HU+500)*255/2000.
HU_OFF, HU_SCALE = -500.0, 2000.0 / 255.0
def hu_to_density(hu):
    return np.clip((hu - HU_OFF) / HU_SCALE, 0, 255).astype(np.uint8)

# Fixed bit layout consumed by trainer.html's HN struct set. The target uses the generic 'tumor'
# key so it reuses the trainer's existing tumour legend / contour-menu slot.
STRUCT_BITS = {'body': 1, 'tumor': 2}

# --- CT series loading (uniform axial HFS) -----------------------------------
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
    slices.sort(key=lambda s: float(s.ImagePositionPatient[2]))      # inferior -> superior
    ref = slices[0]
    ny, nx = int(ref.Rows), int(ref.Columns)
    px, py = float(ref.PixelSpacing[1]), float(ref.PixelSpacing[0])
    zs = np.array([float(s.ImagePositionPatient[2]) for s in slices], float)
    vol = np.zeros((len(slices), ny, nx), np.float32)
    for i, s in enumerate(slices):
        vol[i] = s.pixel_array.astype(np.float32) * float(getattr(s, 'RescaleSlope', 1)) + float(getattr(s, 'RescaleIntercept', 0))
    dz = float(np.median(np.diff(zs)))
    print(f"CT: {nx}x{ny}x{len(slices)}  in-plane {px:.3f}x{py:.3f} mm  dz {dz:.3f} mm  HU[{vol.min():.0f},{vol.max():.0f}]")
    return dict(hu=vol, nx=nx, ny=ny, nz=len(slices), px=px, py=py, dz=dz)

# --- body mask (drop couch/headrest) -----------------------------------------
def body_mask(hu):
    body = ndimage.binary_fill_holes(hu > -350)
    body = ndimage.binary_opening(body, iterations=2)
    lbl, n = ndimage.label(body)
    if n > 1:
        sizes = np.bincount(lbl.ravel()); sizes[0] = 0
        body = lbl == sizes.argmax()                                # largest CC = head/neck
    return ndimage.binary_fill_holes(body)

# --- synthesise a BILATERAL cervical-nodal PTV (horseshoe/U) -----------------
# Two jugular-chain lobes (levels II-IV, both sides) joined by a thin anterior bridge, carving out the
# central airway + posterior cord/vertebra so the U opens posteriorly (cord-sparing). Level-aware:
# II (sup, narrower/medial) -> III (mid, widest/lateral) -> IV (inf, anterior supraclav shelf), with
# optional Ib (submandibular, top) and Va (posterolateral nub, mid). Geometry from the ultracode design.
def synth_target(body, hu, dz, py, px, seed=7):
    SZ, SY, SX = body.shape
    rng = np.random.default_rng(seed)
    air  = hu < -500
    bone = hu > 250
    soft = (hu > SOFT_HU[0]) & (hu < SOFT_HU[1])
    body_in = ndimage.binary_erosion(body, iterations=max(1, round(BODY_ERODE_MM/px)))

    # cervical SI window (NOT the whole cranial vault — the CT spans vertex -> shoulders)
    zb = np.where(body.any(axis=(1, 2)))[0]
    z_lo, z_hi = int(zb.min()), int(zb.max())
    z0 = int(round(z_lo + Z_FRAC_LO*(z_hi - z_lo)))
    z1 = int(round(z_lo + Z_FRAC_HI*(z_hi - z_lo)))

    # per-slice body frame (midline cx, centroid cy, half-width, anterior edge, AP depth), z-smoothed
    cx = np.zeros(SZ); cy = np.zeros(SZ); hw = np.zeros(SZ)
    yant = np.zeros(SZ); apd = np.zeros(SZ); act = np.zeros(SZ, bool)
    for z in range(z0, z1+1):
        if not body[z].any():
            continue
        yy, xx = np.where(body[z])
        cx[z]=xx.mean(); cy[z]=yy.mean(); hw[z]=0.5*(xx.max()-xx.min())
        yant[z]=yy.min(); apd[z]=yy.max()-yy.min(); act[z]=True
    cx = ndimage.uniform_filter1d(cx, 5); hw = ndimage.uniform_filter1d(hw, 5)

    # airway keep-out: the central low-density connected component (pharynx/larynx lumen), dilated
    airway = np.zeros_like(body)
    for z in range(z0, z1+1):
        if not act[z]:
            continue
        lab, n = ndimage.label(air[z] & body[z])
        best=None; bestd=1e18
        for L in range(1, n+1):
            ys, xs = np.where(lab==L)
            area = ys.size*py*px
            if not (20 <= area <= 400):
                continue
            d = (ys.mean()-cy[z])**2 + (xs.mean()-cx[z])**2
            if d < bestd: bestd=d; best=L
        airway[z] = (lab==best) if best is not None else (air[z] & body[z] & (np.abs(np.arange(SX)[None,:]-cx[z])<15))
    airway_ko = ndimage.binary_dilation(airway, iterations=max(1, round(AIRWAY_PAD_MM/px)))

    Y, X = np.ogrid[0:SY, 0:SX]
    tgt = np.zeros_like(body)
    lat_frac = lambda f: 0.46 + (0.34-0.46)*f      # 0.34 sup(II) -> 0.42 mid(III) -> 0.46 inf(IV)
    bridge_hw_f = lambda f: 0.55 + (0.30-0.55)*f   # 0.30 sup -> 0.55 inf
    span = max(1, z1 - z0)
    for z in range(z0, z1+1):
        if not act[z]:
            continue
        f = (z - z0)/span
        ke = min(z - z0, z1 - z, TAPER_N); taper = 0.55 + 0.45*(ke/float(TAPER_N))   # rounded SI caps
        yc_lobe = cy[z] + AP_BIAS*apd[z]
        loff = lat_frac(f)*hw[z]
        sl = np.zeros((SY, SX), bool)
        for sgn in (-1, +1):                        # -1 = patient-left (cx - off); both sides -> bilateral
            jit = float(rng.normal(1, 0.03))
            xc = cx[z] + sgn*loff*jit
            rx = (LOBE_RX_MM/px)*taper*jit; ry = (LOBE_RY_MM/py)*taper
            sl |= (((X-xc)/rx)**2 + ((Y-yc_lobe)/ry)**2) <= 1.0
        # thin anterior bridge joining the lobes across the front (midline primary / low-neck junction)
        bhw = bridge_hw_f(f)*hw[z]
        yin = yant[z] + SKIN_MARGIN_MM/py; yout = yin + (BRIDGE_THICK_MM/py)*taper
        sl |= (np.abs(X-cx[z])<=bhw) & (Y>=yin) & (Y<=yout)
        # optional level Ib (submandibular, superior) + Va (posterolateral nub, mid)
        if f >= 0.88:
            for sgn in (-1, +1):
                sl |= (((X-(cx[z]+sgn*0.22*hw[z]))/(8.0/px))**2 + ((Y-(yant[z]+0.30*apd[z]))/(8.0/py))**2) <= 1.0
        va = np.zeros((SY, SX), bool)
        if 0.45 <= f <= 0.80:
            for sgn in (-1, +1):
                va |= (((X-(cx[z]+sgn*0.55*hw[z]))/(7.0/px))**2 + ((Y-(cy[z]+0.10*apd[z]))/(7.0/py))**2) <= 1.0
        # cord/vertebra keep-out + posterior cutoff (Va is the only thing allowed past the cutoff)
        spine = (np.abs(X-cx[z])<=SPINE_HW_MM/px) & (Y>=cy[z]-0.02*apd[z])
        ypc = cy[z] + POST_CUT_FRAC*apd[z]
        sl = (sl | va) & ~spine
        sl &= (Y<=ypc) | va
        tgt[z] = sl

    # constrain to soft tissue inside the body, carve airway
    tgt &= body_in & soft & ~bone & ~air & ~airway_ko
    tgt = ndimage.binary_closing(tgt, iterations=2)
    for z in range(z0, z1+1):
        tgt[z] = ndimage.binary_fill_holes(tgt[z])
    # z-continuity (rounded reformats), then RE-APPLY the keep-outs LAST (smoothing can bleed)
    tgt = ndimage.gaussian_filter(tgt.astype(np.float32), sigma=(1.8/dz, 1.0/py, 1.0/px)) > 0.5
    tgt &= body_in & soft & ~bone & ~air & ~airway_ko

    iz = int(round(z0 + ISO_Z_FRAC*span))
    ix = int(round(cx[iz])); iy = int(round(cy[iz] + AP_BIAS*apd[iz]))
    print(f"bilateral neck PTV: z-window [{z0},{z1}] ({z1-z0} sl)  -> {int(tgt.sum())} vox  iso hint (x={ix},y={iy},z={iz})")
    return tgt, (ix, iy, iz)

# --- crop neck slab + body in-plane, isotropic resample ----------------------
def resample(hu, masks, dz, py, px):
    SZ, SY, SX = hu.shape
    tgt = masks['tumor']
    zsel = np.where(tgt.any(axis=(1, 2)))[0]
    mz = CROP_MARGIN_MM / dz
    z0, z1 = max(0, int(zsel.min() - mz)), min(SZ, int(zsel.max() + mz) + 1)
    bslab = masks['body'][z0:z1]
    ysel = np.where(bslab.any(axis=(0, 2)))[0]; xsel = np.where(bslab.any(axis=(0, 1)))[0]
    my, mx = BODY_MARGIN_MM / py, BODY_MARGIN_MM / px
    y0, y1 = max(0, int(ysel.min() - my)), min(SY, int(ysel.max() + my) + 1)
    x0, x1 = max(0, int(xsel.min() - mx)), min(SX, int(xsel.max() + mx) + 1)
    print(f"crop z[{z0}:{z1}] (neck slab) y[{y0}:{y1}] x[{x0}:{x1}] of {SZ}x{SY}x{SX}")
    hu = hu[z0:z1, y0:y1, x0:x1]
    masks = {k: m[z0:z1, y0:y1, x0:x1] for k, m in masks.items()}
    CZ, CY, CX = hu.shape
    phys = [CX*px, CY*py, CZ*dz]
    iso_sp = max(phys) / TARGET_XY
    OX = max(1, int(round(phys[0]/iso_sp))); OY = max(1, int(round(phys[1]/iso_sp))); OZ = max(1, int(round(phys[2]/iso_sp)))
    zoom = (OZ/CZ, OY/CY, OX/CX)
    print(f"resample -> {OX}x{OY}x{OZ}  iso spacing {iso_sp:.3f} mm  phys {[round(p) for p in phys]}")
    ct_d = hu_to_density(ndimage.zoom(hu, zoom, order=1))
    out = {k: (ndimage.zoom(m.astype(np.float32), zoom, order=1) > 0.5) if m.any() else np.zeros((OZ, OY, OX), bool)
           for k, m in masks.items()}
    return ct_d, out, (OX, OY, OZ), iso_sp

# --- atlas encode ------------------------------------------------------------
def encode_atlas(vol, OX, OY, OZ, tpr):
    rows = math.ceil(OZ / tpr)
    out = np.zeros((rows*OY, tpr*OX), np.uint8)
    for z in range(OZ):
        tc, tr = z % tpr, z // tpr
        out[tr*OY:tr*OY+OY, tc*OX:tc*OX+OX] = vol[z]
    buf = io.BytesIO(); Image.fromarray(out, 'L').save(buf, format='PNG', compress_level=9)
    return base64.b64encode(buf.getvalue()).decode('ascii'), len(buf.getvalue()), rows

def _qc(ct_d, rmasks, iso, outdir):
    ix, iy, iz = iso
    overlay = {'tumor': (255, 60, 60), 'body': (60, 220, 100)}
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
    os.makedirs(outdir, exist_ok=True)
    for nm, im in [('axial', ax), ('coronal', co), ('sagittal', sa)]:
        Image.fromarray(im).resize((im.shape[1]*3, im.shape[0]*3), Image.NEAREST).save(f'{outdir}/hn_{nm}.png')
    print(f"QC stills in {outdir}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ct', default='scratchpad/hn_thca', help='TCGA-DE-A4MA CT DICOM series directory')
    ap.add_argument('--qc', default='/tmp/hn_cbct_qc', help='QC stills output dir')
    args = ap.parse_args()

    ct = load_ct(args.ct)
    body = body_mask(ct['hu'])
    masks = {'body': body}
    masks['tumor'], _ = synth_target(body, ct['hu'], ct['dz'], ct['py'], ct['px'])

    ct_d, rmasks, (OX, OY, OZ), iso_sp = resample(ct['hu'], masks, ct['dz'], ct['py'], ct['px'])

    zz, yy, xx = np.where(rmasks['tumor'])
    iso = [int(round(xx.mean())), int(round(yy.mean())), int(round(zz.mean()))]
    vol_cc = rmasks['tumor'].sum() * iso_sp**3 / 1000
    print(f"H&N target {int(rmasks['tumor'].sum())} vox ({vol_cc:.1f} cc) — iso at node centroid {iso}")

    labels = np.zeros((OZ, OY, OX), np.uint8)
    bits_present = {}
    for k, bit in STRUCT_BITS.items():
        if rmasks[k].any():
            labels[rmasks[k]] |= bit; bits_present[k] = bit
    print(f"iso(voxel)={iso}  bits={bits_present}")

    _qc(ct_d, rmasks, iso, args.qc)

    ct_b64, ct_sz, rows = encode_atlas(ct_d, OX, OY, OZ, TILES_PER_ROW)
    lbl_b64, lbl_sz, _  = encode_atlas(labels, OX, OY, OZ, TILES_PER_ROW)
    print(f"CT atlas {ct_sz//1024} KB   label atlas {lbl_sz//1024} KB")

    ATTRIB = ('// Source: TCIA TCGA-THCA (via NCI Imaging Data Commons, s3://idc-open-data).\n'
              '// Licence: CC BY 3.0 (commercial use permitted with attribution).\n'
              '// Attribution: The Cancer Genome Atlas Thyroid Cancer (TCGA-THCA) collection,\n'
              '//   The Cancer Imaging Archive, doi:10.7937/k9/tcia.2016.9zfrvf1b.\n'
              '// De-identified head-and-neck CT (patient TCGA-DE-A4MA, "CT HeadNeck 3.0"); full\n'
              '// cranial vault through the neck, cropped to a neck slab + isotropic atlas. SAME\n'
              '// patient as the 2D/2D H&N case. The soft-tissue target is SYNTHETIC (a BILATERAL\n'
              '// cervical-nodal PTV — a horseshoe over levels II-IV both sides, cord/airway-sparing) —\n'
              '// TCGA-THCA carries no tumour annotation; the match is a rigid 6DOF registration of the\n'
              '// real bony head & neck. Educational use only; values fictional.\n')
    meta = (f'{{"dims": [{OX}, {OY}, {OZ}], "spacingMm": [{iso_sp:.4f}, {iso_sp:.4f}, {iso_sp:.4f}], '
            f'"physMm": [{OX*iso_sp:.2f}, {OY*iso_sp:.2f}, {OZ*iso_sp:.2f}], '
            f'"tilesPerRow": {TILES_PER_ROW}, "tileRows": {rows}, "boneThr": 0.62}}')
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
        f.write('// Head & Neck CBCT labels: synthetic BILATERAL cervical-nodal PTV — horseshoe over levels II-IV\n')
        f.write('// both sides, cord/airway-sparing (bit "tumor") + thresholded body.\n')
        f.write(f'const HN3D_LABELS={lbl_meta};\n')
        f.write(f"HN3D_LABELS.atlas='data:image/png;base64,{lbl_b64}';\n")
    print('wrote hn3d_data.js + hn3d_labels_data.js')

if __name__ == '__main__':
    main()
