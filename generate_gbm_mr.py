#!/usr/bin/env python3
"""
generate_gbm_mr.py
Build the MR Glioblastoma (GBM) cranial case from a UPenn-GBM patient (post-contrast
T1 "stealth" planning MR + a BraTS-style tumour DICOM-SEG) and write
  - gbm3d_data.js        (MR volume atlas)                 -> GBM3D_VOL
  - gbm3d_labels_data.js (enhancing+necrosis target, edema, body)   -> GBM3D_LABELS

Second MR case (after the acoustic neuroma). Like that one: no HU model — MR intensity is
percentile-normalised to 0..255 and the VOLCASE entry carries `mr:true`. The moving image is
synthesised by reslicing the MR through a hidden 6DOF offset (no daily series needed).

SEG-sourced (like the Liver case), not RTSTRUCT: a multi-frame segmentation with three BraTS
segments — Necrosis (1), Edema (2), Enhancing Lesion (3). The **target** is the GTV =
enhancing lesion + necrotic core (contrast-enhancing rim + central necrosis); peritumoral
**edema** is kept as a separate context structure. The SEG carries no body ROI, so the **body**
structure is a smoothed **external head contour** derived from the MR (this is a full-head MR —
skull, scalp, orbits and face present — so body = the patient's outer head surface).

DATA (NCI Imaging Data Commons public bucket, reachable where TCIA itself is blocked):
  pip install idc-index pydicom numpy scipy pillow
  from idc_index import index; c = index.IDCClient()
  # collection upenn_gbm, patient UPENN-GBM-00019:
  #   the "t1 axial stealth-post" MR series + the radiologist-corrected SEG referencing it, then:
  python generate_gbm_mr.py --mr /path/MR_t1post_dir --seg /path/SEG_referencing_t1post.dcm

Licence CC BY 4.0 (commercial use OK with attribution) — Bakas, S. et al., UPenn-GBM,
The Cancer Imaging Archive, doi:10.7937/TCIA.709X-DN49.

TEACHING POINT: cranial registration to a glioblastoma — a larger, irregular enhancing
target with central necrosis and surrounding edema, contrasting with the tiny acoustic neuroma.
"""
import argparse, os, io, base64, math, glob, re
import numpy as np
from PIL import Image
from scipy import ndimage

try:
    import pydicom
except ImportError:
    raise SystemExit("pydicom required:  pip install pydicom numpy scipy pillow")

TARGET_XY      = 200    # longest-axis resample size (px)
TILES_PER_ROW  = 10
CROP_MARGIN_MM = 8      # margin around the head bbox (whole head in frame, minimal air)

# Display normalisation (same map as the acoustic-neuroma MR case): trainer maps density
# 0..255 -> "HU" = density*(2000/255)-500 for the window widget; we are not real HU.
def normalize_mr(vol):
    nz = vol[vol > 0]
    lo, hi = np.percentile(nz, 1.0), np.percentile(nz, 99.5)
    d = (vol - lo) / max(1e-3, (hi - lo))
    return np.clip(d * 255.0, 0, 255).astype(np.uint8)

# uint8 bit layout consumed by trainer.html's GBM_STRUCTS.
STRUCT_BITS = {'body': 1, 'tumor': 2, 'edema': 4}

# BraTS SEG segment label -> our key. Enhancing lesion + necrotic core = the GTV/target;
# peritumoral edema kept separate; everything else ignored.
def map_seg(label):
    n = re.sub(r'[^a-z]', '', str(label).lower())
    if 'enhanc' in n or 'necro' in n or 'tumor' in n or 'tumour' in n:
        return 'tumor'
    if 'edema' in n or 'oedema' in n:
        return 'edema'
    return None

def load_mr(mr_dir):
    files = [f for f in glob.glob(os.path.join(mr_dir, '**', '*'), recursive=True) if os.path.isfile(f)]
    sl = []
    for f in files:
        try:
            ds = pydicom.dcmread(f, force=True)
        except Exception:
            continue
        if getattr(ds, 'Modality', '') != 'MR' or not hasattr(ds, 'ImagePositionPatient'):
            continue
        sl.append(ds)
    if not sl:
        raise SystemExit(f"No MR slices under {mr_dir}")
    sl.sort(key=lambda s: float(s.ImagePositionPatient[2]))
    ref = sl[0]
    ny, nx = int(ref.Rows), int(ref.Columns)
    px, py = float(ref.PixelSpacing[1]), float(ref.PixelSpacing[0])
    z = [float(s.ImagePositionPatient[2]) for s in sl]
    dz = float(np.median(np.diff(z))) if len(z) > 1 else float(getattr(ref, 'SliceThickness', 1))
    vol = np.stack([s.pixel_array.astype(np.float32) for s in sl])
    print(f"MR: {nx}x{ny}x{len(sl)}  in-plane {px:.3f}x{py:.3f} mm  dz {abs(dz):.3f} mm")
    return dict(v=vol, nx=nx, ny=ny, nz=len(sl), px=px, py=py, dz=abs(dz),
                iop=[float(x) for x in ref.ImageOrientationPatient],
                ox=float(ref.ImagePositionPatient[0]), oy=float(ref.ImagePositionPatient[1]), z0=z[0])

def rasterize_seg(seg_path, g):
    ds = pydicom.dcmread(seg_path, force=True)
    labels = {int(s.SegmentNumber): getattr(s, 'SegmentLabel', '?') for s in ds.SegmentSequence}
    arr = ds.pixel_array
    if arr.ndim == 2:
        arr = arr[None]
    if ds.Rows != g['ny'] or ds.Columns != g['nx']:
        raise SystemExit(f"SEG grid {ds.Columns}x{ds.Rows} != MR {g['nx']}x{g['ny']} (in-plane resample not implemented)")
    # The AIMI/CaPTk SEG can be stored at a 180° in-plane orientation vs the MR
    # (IOP = [-1,0,0,0,-1,0] vs the MR's [1,0,0,0,1,0]); the slice normal still points +z, so
    # only the in-plane axes need flipping. Detect from the SEG's IOP sign relative to the MR's
    # so a same-orientation SEG is left untouched.
    try:
        seg_iop = [float(x) for x in ds.SharedFunctionalGroupsSequence[0].PlaneOrientationSequence[0].ImageOrientationPatient]
    except Exception:
        seg_iop = [float(x) for x in ds.PerFrameFunctionalGroupsSequence[0].PlaneOrientationSequence[0].ImageOrientationPatient]
    flip_col = (seg_iop[0] * g['iop'][0]) < 0   # column (x) direction opposed -> flip cols
    flip_row = (seg_iop[4] * g['iop'][4]) < 0   # row (y) direction opposed -> flip rows
    print(f"SEG IOP {[round(v,2) for v in seg_iop]}  -> flip_row={flip_row} flip_col={flip_col}")
    masks = {k: np.zeros((g['nz'], g['ny'], g['nx']), bool) for k in STRUCT_BITS}
    mapped = {}
    for i, fg in enumerate(ds.PerFrameFunctionalGroupsSequence):
        z = float(fg.PlanePositionSequence[0].ImagePositionPatient[2])
        segn = int(fg.SegmentIdentificationSequence[0].ReferencedSegmentNumber)
        zi = int(round((z - g['z0']) / g['dz']))
        if not (0 <= zi < g['nz']):
            continue
        key = map_seg(labels.get(segn, '')); mapped[labels.get(segn)] = key
        if key is None:
            continue
        frame = arr[i].astype(bool)
        if flip_row:
            frame = frame[::-1, :]
        if flip_col:
            frame = frame[:, ::-1]
        masks[key][zi] |= frame
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
    ap.add_argument('--mr', required=True, help='post-contrast T1 MR series directory')
    ap.add_argument('--seg', required=True, help='DICOM-SEG drawn on that MR (BraTS labels)')
    args = ap.parse_args()

    g = load_mr(args.mr)
    masks = rasterize_seg(args.seg, g)
    if not masks['tumor'].any():
        raise SystemExit("no tumour segment matched — check map_seg against the printed SEG labels")
    dens = normalize_mr(g['v'])
    spz, spy, spx = g['dz'], g['py'], g['px']

    # External head/body contour. This MR is a FULL head (not skull-stripped — skull, scalp,
    # orbits and face are all present), so `body` is the patient's outer head surface, the
    # conventional external/body structure. A raw threshold of the noisy MR periphery gives a
    # jagged, hairy contour, so smooth it: blur -> threshold -> close -> fill -> largest CC ->
    # open (shave thin scalp/noise spikes) -> fill -> blur the binary mask and re-threshold so
    # the rendered outline is a clean rounded head boundary instead of pixel-level fuzz.
    sm = ndimage.gaussian_filter(dens.astype(np.float32), sigma=(0.6, 1.2, 1.2))
    head = sm > 22
    head = ndimage.binary_closing(head, iterations=3)
    head = ndimage.binary_fill_holes(head)
    lab, n = ndimage.label(head)
    if n:
        sizes = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1))
        head = lab == (1 + int(np.argmax(sizes)))
    head = ndimage.binary_opening(head, iterations=2)        # remove thin protrusions (hair/noise)
    head = ndimage.binary_fill_holes(head)
    head = ndimage.gaussian_filter(head.astype(np.float32), sigma=1.0) > 0.5   # round the boundary
    masks['body'] = head

    # crop to the whole head (body bbox + small margin)
    zz, yy, xx = np.where(head)
    mz, my, mx = CROP_MARGIN_MM/spz, CROP_MARGIN_MM/spy, CROP_MARGIN_MM/spx
    z0, z1 = max(0, int(zz.min()-mz)), min(g['nz'], int(zz.max()+mz)+1)
    y0, y1 = max(0, int(yy.min()-my)), min(g['ny'], int(yy.max()+my)+1)
    x0, x1 = max(0, int(xx.min()-mx)), min(g['nx'], int(xx.max()+mx)+1)
    print(f"crop to head box z[{z0}:{z1}] y[{y0}:{y1}] x[{x0}:{x1}] of {g['nz']}x{g['ny']}x{g['nx']}")
    dens = dens[z0:z1, y0:y1, x0:x1]
    masks = {k: m[z0:z1, y0:y1, x0:x1] for k, m in masks.items()}
    CZ, CY, CX = dens.shape

    # isotropic resample to a tile-friendly size
    phys = [CX*spx, CY*spy, CZ*spz]
    iso_sp = max(phys) / TARGET_XY
    OX = max(1, round(phys[0]/iso_sp)); OY = max(1, round(phys[1]/iso_sp)); OZ = max(1, round(phys[2]/iso_sp))
    zoom = (OZ/CZ, OY/CY, OX/CX)
    print(f"resample -> {OX}x{OY}x{OZ}  iso {iso_sp:.3f} mm  phys {[round(p) for p in phys]}")
    vol_d = np.clip(ndimage.zoom(dens.astype(np.float32), zoom, order=1), 0, 255).astype(np.uint8)
    rmasks = {k: (ndimage.zoom(m.astype(np.float32), zoom, order=1) > 0.5) if m.any()
                 else np.zeros((OZ, OY, OX), bool) for k, m in masks.items()}

    labels = np.zeros((OZ, OY, OX), np.uint8); bits = {}
    for k, bit in STRUCT_BITS.items():
        if rmasks[k].any():
            labels[rmasks[k]] |= bit; bits[k] = bit
    tz, ty, tx = np.where(rmasks['tumor'])
    iso = [int(round(tx.mean())), int(round(ty.mean())), int(round(tz.mean()))]
    print(f"iso(voxel)={iso}  bits={bits}  tumour {int(rmasks['tumor'].sum())} vox  "
          f"edema {int(rmasks['edema'].sum())} vox  body {int(rmasks['body'].sum())} vox")

    mr_b64, mr_sz, rows = encode_atlas(vol_d, OX, OY, OZ, TILES_PER_ROW)
    lbl_b64, lbl_sz, _  = encode_atlas(labels, OX, OY, OZ, TILES_PER_ROW)
    print(f"MR atlas {mr_sz//1024} KB   label atlas {lbl_sz//1024} KB")

    # QC stills: mid-tumour axial of the MR + the label overlay (for review with Read)
    qz = int(iso[2])
    Image.fromarray(vol_d[qz]).resize((OX*2, OY*2)).save('/tmp/gbm_mr_qc.png')
    ov = np.stack([vol_d[qz]]*3, -1).astype(np.uint8)
    ov[rmasks['tumor'][qz]] = [255, 60, 60]; ov[rmasks['edema'][qz] & ~rmasks['tumor'][qz]] = [80, 180, 255]
    Image.fromarray(ov).resize((OX*2, OY*2)).save('/tmp/gbm_lbl_qc.png')

    ATTRIB = ('// Source: TCIA UPenn-GBM (via NCI Imaging Data Commons, s3://idc-open-data).\n'
              '// Licence: CC BY 4.0 (commercial use permitted with attribution).\n'
              '// Attribution: Bakas, S. et al., The Cancer Imaging Archive, doi:10.7937/TCIA.709X-DN49.\n'
              '// De-identified post-contrast T1 planning MR (skull-stripped, CaPTk-processed),\n'
              '// cropped to the head + percentile-normalised. Tumour SEG: BraTS radiologist-corrected.\n')
    meta = (f'{{"dims": [{OX}, {OY}, {OZ}], "spacingMm": [{iso_sp:.4f}, {iso_sp:.4f}, {iso_sp:.4f}], '
            f'"physMm": [{OX*iso_sp:.2f}, {OY*iso_sp:.2f}, {OZ*iso_sp:.2f}], '
            f'"tilesPerRow": {TILES_PER_ROW}, "tileRows": {rows}, "boneThr": 0.55, "mr": true}}')
    with open('gbm3d_data.js', 'w') as f:
        f.write(ATTRIB)
        f.write('// MR (not CT): dims=[x(LR),y(AP),z(SI)], intensity percentile-normalised to 0..255.\n')
        f.write(f'const GBM3D_VOL={meta};\n')
        f.write(f"GBM3D_VOL.atlas='data:image/png;base64,{mr_b64}';\n")
    bits_json = ', '.join(f'"{k}": {v}' for k, v in bits.items())
    lbl_meta = (f'{{"dims": [{OX}, {OY}, {OZ}], "spacingMm": [{iso_sp:.4f}, {iso_sp:.4f}, {iso_sp:.4f}], '
                f'"tilesPerRow": {TILES_PER_ROW}, "bits": {{{bits_json}}}, "isoIdx": [{iso[0]}, {iso[1]}, {iso[2]}]}}')
    with open('gbm3d_labels_data.js', 'w') as f:
        f.write(ATTRIB)
        f.write('// GBM labels: GTV (enhancing lesion + necrotic core), peritumoral edema, external head/body contour.\n')
        f.write(f'const GBM3D_LABELS={lbl_meta};\n')
        f.write(f"GBM3D_LABELS.atlas='data:image/png;base64,{lbl_b64}';\n")
    print('wrote gbm3d_data.js + gbm3d_labels_data.js')
    print('QC: /tmp/gbm_mr_qc.png  /tmp/gbm_lbl_qc.png')

if __name__ == '__main__':
    main()
