#!/usr/bin/env python3
"""
generate_lung_volume.py
(Re-)build the Lung SBRT CBCT case from a documented CC-BY IDC chest CT and write
  - lung3d_data.js        (CT volume with a synthetic RLL nodule baked in) -> LUNG3D_VOL
  - lung3d_labels_data.js (Body / Lung / GTV / PTV label volume)           -> LUNG3D_LABELS

Re-sources the case off a real diagnostic chest CT (replaces the old build that was chained
off an undocumented thoracic atlas). A synthetic, irregular/spiculated peripheral nodule is
injected into the RIGHT LOWER LOBE — subpleural, in air-density lung — exactly as the previous
build did (the teaching point is off-bone differential motion: match the soft-tissue target,
not the spine). The nodule is auto-placed from the segmented right-lower lung so it stays a
valid subpleural RLL lesion regardless of the source patient's anatomy.

DATA
----
Source (licence verified CC BY 3.0 via the IDC idc-index):
  LIDC-IDRI  https://doi.org/10.7937/k9/tcia.2015.lo9ql9sx
  patient LIDC-IDRI-0136: a soft-kernel diagnostic chest CT ("ChestRoutine 3.0 B31f").
Pulled from the NCI Imaging Data Commons bucket s3://idc-open-data via idc-index.

Same tiled-atlas format / axis convention (dims=[x(LR),y(AP),z(SI)], x0=patient-right,
y0=anterior, z0=inferior) as the other *3d_data.js files.

USAGE
-----
  pip install pydicom numpy scipy pillow
  python generate_lung_volume.py --ct /path/to/CT_series_dir
"""
import argparse, os, re, io, base64, math, glob
import numpy as np
from PIL import Image
from scipy import ndimage

try:
    import pydicom
except ImportError:
    raise SystemExit("pydicom is required:  pip install pydicom numpy scipy pillow")

TARGET_XY     = 200     # longest-axis resample size (px)
TILES_PER_ROW = 12
CROP_MARGIN_MM = 12     # margin around the lung/body slab
LESION_HU     = 74.0    # solid soft-tissue nodule density in HU (baked hard-edged)

HU_OFF, HU_SCALE = -500.0, 2000.0 / 255.0
def hu_to_density(hu): return np.clip((hu - HU_OFF) / HU_SCALE, 0, 255).astype(np.uint8)

def load_ct(ct_dir):
    files = [f for f in glob.glob(os.path.join(ct_dir, '**', '*'), recursive=True) if os.path.isfile(f)]
    slices = []
    for f in files:
        try:
            ds = pydicom.dcmread(f, force=True)
        except Exception:
            continue
        if getattr(ds, 'Modality', '') == 'CT' and hasattr(ds, 'ImagePositionPatient'):
            slices.append(ds)
    if not slices:
        raise SystemExit(f"No CT slices under {ct_dir}")
    slices.sort(key=lambda s: float(s.ImagePositionPatient[2]))
    ref = slices[0]; ny, nx = int(ref.Rows), int(ref.Columns)
    px, py = float(ref.PixelSpacing[1]), float(ref.PixelSpacing[0])
    z = [float(s.ImagePositionPatient[2]) for s in slices]
    dz = float(np.median(np.diff(z))) if len(z) > 1 else 1.0
    vol = np.zeros((len(slices), ny, nx), np.float32)
    for i, s in enumerate(slices):
        vol[i] = s.pixel_array.astype(np.float32) * float(getattr(s, 'RescaleSlope', 1)) \
                 + float(getattr(s, 'RescaleIntercept', 0))
    print(f"CT: {nx}x{ny}x{len(slices)}  in-plane {px:.3f} mm  dz {abs(dz):.3f} mm")
    return vol, px, py, abs(dz)

def segment(hu):
    """Body (per-slice fill, largest CC) + lungs (the two largest internal air blobs)."""
    nz = hu.shape[0]
    body = np.array([ndimage.binary_fill_holes(hu[z] > -350) for z in range(nz)])
    lb, n = ndimage.label(body)
    if n > 1:
        sizes = np.bincount(lb.ravel()); sizes[0] = 0
        body = lb == sizes.argmax()
    lung = np.zeros_like(body)
    for z in range(nz):
        bod = ndimage.binary_erosion(ndimage.binary_fill_holes(hu[z] > -350), iterations=3)
        lung[z] = ndimage.binary_opening((hu[z] < -400) & bod, iterations=1)
    lung = ndimage.binary_opening(lung, iterations=1)
    lb, n = ndimage.label(lung)
    if n >= 1:
        sizes = ndimage.sum(lung, lb, range(1, n + 1))
        keep = np.argsort(sizes)[::-1][:2] + 1
        lung = np.isin(lb, keep)
    return body, lung

def place_nodule(lung, px, py, dz):
    """Auto-pick a subpleural RIGHT-LOWER-LOBE centre (patient-right = low x; inferior = low z)."""
    zz, yy, xx = np.where(lung)
    xc = xx.mean()
    right = xx < xc                                  # patient-right lung (x0 = patient-right)
    zthr = np.percentile(zz[right], 42)              # inferior portion
    sel = right & (zz < zthr)
    rx, ry, rz = xx[sel], yy[sel], zz[sel]
    # lateral (low x) + posterior (high y), a little inside the pleura
    cx = np.percentile(rx, 22)
    cy = np.percentile(ry, 62)
    cz = np.percentile(rz, 45)
    inner = ndimage.binary_erosion(lung, iterations=2)   # keep the centre off the pleural edge
    iz, iy, ix = np.where(inner)
    j = np.argmin(((ix - cx) * px) ** 2 + ((iy - cy) * py) ** 2 + ((iz - cz) * dz) ** 2)
    return float(ix[j]), float(iy[j]), float(iz[j])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ct', required=True)
    ap.add_argument('--qc', default='/tmp/lung_qc')
    args = ap.parse_args()

    hu, px, py, dz = load_ct(args.ct)
    body, lung = segment(hu)

    # crop to the lung slab (SI) + body (in-plane), then isotropically resample
    zsel = np.where(lung.any(axis=(1, 2)))[0]
    mz = CROP_MARGIN_MM / dz
    z0, z1 = max(0, int(zsel.min() - mz)), min(hu.shape[0], int(zsel.max() + mz) + 1)
    bslab = body[z0:z1]
    ysel = np.where(bslab.any(axis=(0, 2)))[0]; xsel = np.where(bslab.any(axis=(0, 1)))[0]
    y0, y1 = ysel.min(), ysel.max() + 1; x0, x1 = xsel.min(), xsel.max() + 1
    hu = hu[z0:z1, y0:y1, x0:x1]; body = body[z0:z1, y0:y1, x0:x1]; lung = lung[z0:z1, y0:y1, x0:x1]
    print(f"crop -> {hu.shape[::-1]}")
    CZ, CY, CX = hu.shape
    phys = [CX * px, CY * py, CZ * dz]
    SP = max(phys) / TARGET_XY
    OX, OY, OZ = (max(1, int(round(p / SP))) for p in phys)
    zoom = (OZ / CZ, OY / CY, OX / CX)
    print(f"resample -> {OX}x{OY}x{OZ}  iso {SP:.3f} mm")
    ct_d = hu_to_density(ndimage.zoom(hu, zoom, order=1)).astype(np.float32)
    body = ndimage.zoom(body.astype(np.float32), zoom, order=1) > 0.5
    lung = ndimage.zoom(lung.astype(np.float32), zoom, order=1) > 0.5
    DZ, DY, DX = ct_d.shape

    # synthetic spiculated RLL nodule (overlapping lobules + coarse pleural/vascular spicules)
    CXn, CYn, CZn = place_nodule(lung, SP, SP, SP)
    print(f"nodule centre voxel=({CXn:.0f},{CYn:.0f},{CZn:.0f})")
    zz, yy, xx = np.mgrid[0:DZ, 0:DY, 0:DX]
    def sph(cx, cy, cz, rmm): return ((xx-cx)*SP)**2 + ((yy-cy)*SP)**2 + ((zz-cz)*SP)**2 <= rmm*rmm
    gtv = np.zeros((DZ, DY, DX), bool)
    for dx, dy, dzz, r in [(0,0,0,6.6),(2,-1,0,5.2),(-2,2,1,5.4),(1,2,-1,4.6),
                           (-1,-2,2,4.4),(3,1,0,3.8),(-1,3,1,3.4),(2,-2,-2,3.4)]:
        gtv |= sph(CXn+dx, CYn+dy, CZn+dzz, r)
    for ux, uy, uz in [(-0.85,0.35,0.0),(0.25,-0.9,0.1),(0.55,0.6,-0.4),(-0.25,-0.5,0.75)]:
        nrm = (ux*ux+uy*uy+uz*uz)**0.5; ux, uy, uz = ux/nrm, uy/nrm, uz/nrm
        for smm, r in [(8,2.4),(11,1.9),(14,1.5)]:
            gtv |= sph(CXn+ux*smm/SP, CYn+uy*smm/SP, CZn+uz*smm/SP, r)

    vol = ct_d.copy(); vol[gtv] = LESION_HU
    vol = np.clip(vol, 0, 255).astype(np.uint8)

    labels = np.zeros((DZ, DY, DX), np.uint8)
    labels[body] |= 0x80
    labels[lung & ~gtv] |= 0x08
    labels[gtv] |= 0x01
    ptv = ndimage.binary_dilation(gtv, iterations=max(1, int(round(5.0 / SP))))
    labels[ptv] |= 0x02
    gz, gy, gx = np.where(gtv)
    iso = [int(round(gx.mean())), int(round(gy.mean())), int(round(gz.mean()))]
    print(f"GTV {int(gtv.sum())} vox  PTV {int(ptv.sum())} vox  iso={iso}")

    os.makedirs(args.qc, exist_ok=True)
    _qc(vol, {'gtv': gtv, 'ptv': ptv, 'lung': lung}, iso, args.qc)

    def enc(v):
        rows = math.ceil(DZ / TILES_PER_ROW)
        out = np.zeros((rows*DY, TILES_PER_ROW*DX), np.uint8)
        for z in range(DZ):
            out[(z//TILES_PER_ROW)*DY:(z//TILES_PER_ROW)*DY+DY, (z%TILES_PER_ROW)*DX:(z%TILES_PER_ROW)*DX+DX] = v[z]
        buf = io.BytesIO(); Image.fromarray(out, 'L').save(buf, 'PNG', compress_level=9)
        return base64.b64encode(buf.getvalue()).decode('ascii'), len(buf.getvalue()), rows
    ct_b64, ct_sz, rows = enc(vol); lbl_b64, lbl_sz, _ = enc(labels)
    print(f"CT atlas {ct_sz//1024} KB   label atlas {lbl_sz//1024} KB")

    ATTRIB = ('// Source: LIDC-IDRI (via NCI Imaging Data Commons, s3://idc-open-data).\n'
              '// Licence: CC BY 3.0 (commercial use permitted with attribution).\n'
              '// Attribution: LIDC-IDRI, The Cancer Imaging Archive, doi:10.7937/k9/tcia.2015.lo9ql9sx.\n'
              '// De-identified diagnostic chest CT (patient LIDC-IDRI-0136); a SYNTHETIC RLL SBRT nodule is baked in.\n')
    meta = (f'{{"dims": [{DX}, {DY}, {DZ}], "spacingMm": [{SP:.4f}, {SP:.4f}, {SP:.4f}], '
            f'"physMm": [{DX*SP:.2f}, {DY*SP:.2f}, {DZ*SP:.2f}], "tilesPerRow": {TILES_PER_ROW}, '
            f'"tileRows": {rows}, "boneThr": 0.42}}')
    with open('lung3d_data.js', 'w') as f:
        f.write(ATTRIB)
        f.write('// dims=[x(LR),y(AP),z(SI)]  x0=patient-right  y0=anterior  z0=inferior\n')
        f.write(f'const LUNG3D_VOL={meta};\n')
        f.write(f"LUNG3D_VOL.atlas='data:image/png;base64,{ct_b64}';\n")
    lbl_meta = (f'{{"dims": [{DX}, {DY}, {DZ}], "spacingMm": [{SP:.4f}, {SP:.4f}, {SP:.4f}], '
                f'"tilesPerRow": {TILES_PER_ROW}, "bits": {{"gtv": 1, "ptv": 2, "lung": 8, "body": 128}}, '
                f'"isoIdx": [{iso[0]}, {iso[1]}, {iso[2]}]}}')
    with open('lung3d_labels_data.js', 'w') as f:
        f.write(ATTRIB)
        f.write('// Lung SBRT case labels: body / lungs from CT + synthetic RLL GTV and PTV(GTV+5mm).\n')
        f.write(f'const LUNG3D_LABELS={lbl_meta};\n')
        f.write(f"LUNG3D_LABELS.atlas='data:image/png;base64,{lbl_b64}';\n")
    print('wrote lung3d_data.js + lung3d_labels_data.js')

def _qc(vol, masks, iso, outdir):
    ix, iy, iz = iso
    overlay = {'gtv': (255, 70, 70), 'ptv': (255, 200, 60), 'lung': (80, 160, 255)}
    def rgb(g): return np.stack([g]*3, -1).astype(np.uint8)
    def draw(base, m2d):
        img = rgb(base)
        for k, col in overlay.items():
            m = m2d.get(k)
            if m is None or not m.any(): continue
            img[m ^ ndimage.binary_erosion(m)] = col
        return img
    ax = draw(vol[iz], {k: masks[k][iz] for k in overlay})
    co = draw(vol[:, iy, :][::-1], {k: masks[k][:, iy, :][::-1] for k in overlay})
    sa = draw(vol[:, :, ix][::-1], {k: masks[k][:, :, ix][::-1] for k in overlay})
    for nm, im in [('axial', ax), ('coronal', co), ('sagittal', sa)]:
        Image.fromarray(im).resize((im.shape[1]*3, im.shape[0]*3), Image.NEAREST).save(f'{outdir}/lung_{nm}.png')

if __name__ == '__main__':
    main()
