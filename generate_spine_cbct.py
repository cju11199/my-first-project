#!/usr/bin/env python3
"""
generate_spine_cbct.py
Rebuild the **CBCT Spine SBRT** case (`spine3d_data.js` + `spine3d_labels_data.js`) from the same
full-resolution diagnostic chest CT as the 2D Spine case (TCIA NSCLC-Radiogenomics R01-076, 0.8 mm),
replacing the older 2.2 mm atlas. Structures come from **TotalSegmentator** run on this exact CT
(spinal_cord / esophagus / aorta / lung lobes / thoracic vertebrae); the **PTV** is synthesised as
the target vertebra (T7) + 4 mm carved around the cord, and **body** is thresholded from the CT.

The trainer reslices this volume live in-browser, so it is rebuilt at a **moderate 1.6 mm** (NOT the
source 0.8 mm — full-res would be ~30 MB and janky in the MPR). Output matches the tiled-atlas
format the trainer's `decodeVol` / `_decodeSpineLabels` expect (z-major tiles, X=LR cols, Y=AP rows;
density 0..255 with HU=density*(2000/255)-500; label voxels carry an OR of the structure bits).

Resampling is done in **world (patient) coordinates** via affines, so any orientation/flip between
the pydicom CT stack and TotalSegmentator's nifti masks is handled correctly: every output voxel maps
to an LPS world point, sampled trilinearly from the CT and nearest-neighbour from each mask.

Licence: TCIA NSCLC-Radiogenomics, CC BY 3.0 — attribute doi:10.7937/k9/tcia.2017.7hs46erv.
Needs pydicom / nibabel / numpy / scipy / pillow (+ TotalSegmentator masks pre-generated).
"""
import os, glob, io, base64, json
import numpy as np
import pydicom, nibabel as nib
from scipy import ndimage
from PIL import Image

CTDIR = ('scratchpad/nsclc_spine/nsclc_radiogenomics/R01-076/'
         '1.3.6.1.4.1.14519.5.2.1.4334.1501.137912259338324725690543803674/'
         'CT_1.3.6.1.4.1.14519.5.2.1.4334.1501.201809319317668346803592237989')
TSDIR = 'scratchpad/ts_spine'
OUT_MM = 1.6                       # atlas isotropic spacing (in-browser reslice budget)
TARGET = 'vertebrae_T7'           # target vertebra for iso + PTV
SI_MM, AP_MARGIN, LR_MARGIN = 290.0, 12.0, 12.0   # crop: SI window (mm) on the spine, in-plane body+margin

# ── Load the CT (pydicom) → array[z,y,x] HU + its voxel→LPS-world affine ──────
sl = [pydicom.dcmread(f) for f in glob.glob(os.path.join(CTDIR, '*.dcm'))]
sl.sort(key=lambda d: float(d.ImagePositionPatient[2]))
ct = np.stack([s.pixel_array.astype(np.float32)*float(s.RescaleSlope)+float(s.RescaleIntercept) for s in sl])
DZ, DY, DX = ct.shape
ipp0 = np.array(sl[0].ImagePositionPatient, float)            # LPS world of [row0,col0] of most-inferior slice
psy, psx = [float(v) for v in sl[0].PixelSpacing]
dz = abs(float(sl[1].ImagePositionPatient[2]) - float(sl[0].ImagePositionPatient[2]))
print(f'CT {DX}x{DY}x{DZ}  vox x={psx:.3f} y={psy:.3f} z={dz:.3f} mm  HU[{ct.min():.0f},{ct.max():.0f}]')

def ct_world_to_idx(wx, wy, wz):                              # LPS world → (col x, row y, slice z) fractional
    return (wx-ipp0[0])/psx, (wy-ipp0[1])/psy, (wz-ipp0[2])/dz

# ── Load TotalSegmentator masks (nibabel, RAS affine) ────────────────────────
def load_mask(name):
    p = os.path.join(TSDIR, name+'.nii.gz')
    if not os.path.exists(p): return None
    return nib.as_closest_canonical(nib.load(p))             # RAS+ orientation

LUNGS = ['lung_upper_lobe_left','lung_lower_lobe_left','lung_upper_lobe_right',
         'lung_middle_lobe_right','lung_lower_lobe_right']
masks = {n: load_mask(n) for n in [TARGET,'spinal_cord','esophagus','aorta']+LUNGS}
print('masks present:', [k for k,v in masks.items() if v is not None])

def sample_mask(m, wx, wy, wz):                              # LPS world → nearest mask voxel value
    inv = np.linalg.inv(m.affine)
    rx, ry, rz = -wx, -wy, wz                                # LPS → RAS (negate x,y)
    i = inv[0,0]*rx+inv[0,1]*ry+inv[0,2]*rz+inv[0,3]
    j = inv[1,0]*rx+inv[1,1]*ry+inv[1,2]*rz+inv[1,3]
    k = inv[2,0]*rx+inv[2,1]*ry+inv[2,2]*rz+inv[2,3]
    d = m.get_fdata(); S = d.shape
    ii, jj, kk = np.round(i).astype(int), np.round(j).astype(int), np.round(k).astype(int)
    ok = (ii>=0)&(ii<S[0])&(jj>=0)&(jj<S[1])&(kk>=0)&(kk<S[2])
    out = np.zeros(ii.shape, np.uint8)
    out[ok] = (d[ii[ok],jj[ok],kk[ok]]>0.5).astype(np.uint8)
    return out

# ── Target vertebra centroid (LPS world) → defines the crop box ──────────────
tm = masks[TARGET]; td = tm.get_fdata()
ti,tj,tk = np.where(td>0.5)
# RAS centroid → LPS
ras = tm.affine @ np.array([ti.mean(),tj.mean(),tk.mean(),1.0])
tgt_lps = np.array([-ras[0], -ras[1], ras[2]])
print(f'{TARGET} centroid LPS = {tgt_lps.round(1)}')

# Body bbox in world (from CT body threshold) to frame the in-plane crop
body = ndimage.binary_fill_holes(ct > -350)
lab,n = ndimage.label(body); body = lab==(1+int(np.argmax(ndimage.sum(np.ones_like(lab),lab,range(1,n+1)))))
bz,by,bx = np.where(body)
wxmin,wxmax = ipp0[0]+bx.min()*psx, ipp0[0]+bx.max()*psx
wymin,wymax = ipp0[1]+by.min()*psy, ipp0[1]+by.max()*psy
x0w,x1w = min(wxmin,wxmax)-LR_MARGIN, max(wxmin,wxmax)+LR_MARGIN
y0w,y1w = min(wymin,wymax)-AP_MARGIN, max(wymin,wymax)+AP_MARGIN
z0w,z1w = tgt_lps[2]-SI_MM/2, tgt_lps[2]+SI_MM/2
print(f'crop world  x[{x0w:.0f},{x1w:.0f}] y[{y0w:.0f},{y1w:.0f}] z[{z0w:.0f},{z1w:.0f}] mm')

# ── Build the output 1.6 mm grid (dims X=LR, Y=AP, Z=SI) and resample ────────
GX = int(round((x1w-x0w)/OUT_MM)); GY = int(round((y1w-y0w)/OUT_MM)); GZ = int(round((z1w-z0w)/OUT_MM))
xs = x0w + (np.arange(GX)+0.5)*OUT_MM
ys = y0w + (np.arange(GY)+0.5)*OUT_MM
zs = z0w + (np.arange(GZ)+0.5)*OUT_MM
WX,WY,WZ = np.meshgrid(xs,ys,zs,indexing='ij')               # [GX,GY,GZ] world coords
flatW = (WX.ravel(),WY.ravel(),WZ.ravel())
print(f'atlas grid {GX}x{GY}x{GZ} @ {OUT_MM}mm = {GX*GY*GZ/1e6:.1f}M voxels')

# CT density (trilinear) on the grid
cx,cy,cz = ct_world_to_idx(*flatW)
hu = ndimage.map_coordinates(ct, [cz,cy,cx], order=1, mode='constant', cval=-1000.0).reshape(GX,GY,GZ)
dens = np.clip((hu+500.0)*(255.0/2000.0), 0, 255).astype(np.uint8)

# Structure masks on the grid
def grid_mask(m):
    if m is None: return np.zeros((GX,GY,GZ),np.uint8)
    return sample_mask(m,*flatW).reshape(GX,GY,GZ)
vert = grid_mask(masks[TARGET])
cord = grid_mask(masks['spinal_cord'])
esoph= grid_mask(masks['esophagus'])
aorta= grid_mask(masks['aorta'])
lung = np.zeros((GX,GY,GZ),np.uint8)
for L in LUNGS: lung |= grid_mask(masks[L])

# Anti-alias the NN-resampled masks: gaussian-smooth + re-binarize at 0.5 rounds off the order-0
# stair-steps so marching-squares draws smooth polylines; keep the largest CC to drop stray
# fragments. Sigma 0.7/0.5-threshold is centroid-preserving (<0.15mm shift) so nothing moves.
# Done BEFORE the PTV synth so PTV (dilate-vertebra / carve-cord) inherits the clean edges.
def clean(m, sigma=0.7):
    m = ndimage.gaussian_filter(m.astype(np.float32),sigma)>0.5
    l,n = ndimage.label(m)
    if n: m = l==(1+int(np.argmax(ndimage.sum(np.ones_like(l),l,range(1,n+1)))))
    return m.astype(np.uint8)
vert  = clean(vert)
cord  = clean(cord)
esoph = clean(esoph)
aorta = clean(aorta)
# LUNG is multi-lobe: smooth WITHOUT the largest-CC keep, or a lobe would be deleted.
lung = (ndimage.gaussian_filter(lung.astype(np.float32),0.8)>0.5).astype(np.uint8)
def _largest_cc(mask):                                       # keep the single largest connected component
    l,nn = ndimage.label(mask)
    if not nn: return mask
    return l==(1+int(np.argmax(ndimage.sum(np.ones_like(l),l,range(1,nn+1)))))
# Body: smooth+close the threshold, drop the couch (largest 3D CC), then fill PER AXIAL SLICE.
# A 3D fill cannot close lung/airway/bowel air (it leaks to the outside via the trachea/apertures),
# so those cavities reappear as interior holes in every 2D reslice -> stray green body speckle.
# Filling each axial slice (SI axis = last grid axis Z) makes a solid torso silhouette per plane.
bm = ndimage.gaussian_filter((hu>-350).astype(np.float32),0.8)>0.5
bm = ndimage.binary_closing(bm, iterations=2)
bm = _largest_cc(bm)
for k in range(bm.shape[2]):                                 # SI axis = Z = last axis
    sl = ndimage.binary_fill_holes(bm[:,:,k])
    sl = _largest_cc(sl)
    bm[:,:,k] = sl
bodyg = bm.astype(np.uint8)

# PTV = target vertebra + 4 mm, carved 2 mm around the cord (cord-avoiding SBRT PTV)
r4 = max(1,int(round(4.0/OUT_MM))); r2 = max(1,int(round(2.0/OUT_MM)))
ptv = ndimage.binary_dilation(vert>0, iterations=r4)
ptv &= ~ndimage.binary_dilation(cord>0, iterations=r2)
ptv = ptv.astype(np.uint8)

# ── Pack label bitmask volume ────────────────────────────────────────────────
BITS = {'vertebra':1,'ptv':2,'cord':4,'esophagus':8,'aorta':16,'lung':32,'body':64}
lblvol = np.zeros((GX,GY,GZ),np.uint8)
lblvol |= BITS['body']*bodyg
lblvol |= BITS['lung']*lung
lblvol |= BITS['aorta']*aorta
lblvol |= BITS['esophagus']*esoph
lblvol |= BITS['vertebra']*vert
lblvol |= BITS['ptv']*ptv
lblvol |= BITS['cord']*cord

iso = [int(round((tgt_lps[0]-x0w)/OUT_MM)), int(round((tgt_lps[1]-y0w)/OUT_MM)),
       int(round((tgt_lps[2]-z0w)/OUT_MM))]
print('isoIdx (T7):', iso, ' structure voxel counts:',
      {k:int((lblvol & v).astype(bool).sum()) for k,v in BITS.items()})

# ── Encode tiled atlases (z-major; tile = X cols × Y rows) ───────────────────
def atlas_png(vol3d):                                        # vol3d[X,Y,Z] uint8 → tiled PNG dataurl
    X,Y,Z = vol3d.shape
    tpr = 12; rows = (Z+tpr-1)//tpr
    A = np.zeros((rows*Y, tpr*X), np.uint8)
    for z in range(Z):
        tc,tr = z%tpr, z//tpr
        A[tr*Y:tr*Y+Y, tc*X:tc*X+X] = vol3d[:,:,z].T        # tile rows=y, cols=x
    im = Image.fromarray(A,'L'); buf=io.BytesIO(); im.save(buf,'PNG',compress_level=9)
    return 'data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode('ascii'), tpr, rows

dens_url, tpr, rows = atlas_png(dens)
lbl_url, _, _ = atlas_png(lblvol)
physMm = [round(GX*OUT_MM,1), round(GY*OUT_MM,1), round(GZ*OUT_MM,1)]
zR = [round(z0w,1), round(z1w,1)]

vol_meta = {"dims":[GX,GY,GZ],"spacingMm":[OUT_MM]*3,"physMm":physMm,"tilesPerRow":tpr,"tileRows":rows,"zRange":zR}
lbl_meta = {"dims":[GX,GY,GZ],"spacingMm":[OUT_MM]*3,"tilesPerRow":tpr,"bits":BITS,"isoIdx":iso,"target":"T7"}

HDR = ('// Thoracic-spine CT for the CBCT Spine SBRT case, re-sourced from a full-resolution\n'
       '// diagnostic chest CT (TCIA NSCLC-Radiogenomics R01-076, 0.8 mm) and rebuilt at 1.6 mm.\n'
       '// dims=[x(LR),y(AP),z(SI)]  Licence CC BY 3.0 — doi:10.7937/k9/tcia.2017.7hs46erv\n')
with open('spine3d_data.js','w') as f:
    f.write(HDR); f.write(f'const SPINE3D_VOL={json.dumps(vol_meta)};\n')
    f.write(f"SPINE3D_VOL.atlas='{dens_url}';\n")
with open('spine3d_labels_data.js','w') as f:
    f.write('// Thoracic-spine SBRT structures (TotalSegmentator on NSCLC-Radiogenomics R01-076:\n')
    f.write('// vertebra T7/cord/esophagus/aorta/lung; PTV=T7+4mm carved around cord). CC BY 3.0.\n')
    f.write(f'const SPINE3D_LABELS={json.dumps(lbl_meta)};\n')
    f.write(f"SPINE3D_LABELS.atlas='{lbl_url}';\n")
print('wrote spine3d_data.js + spine3d_labels_data.js')
print('sizes MB:', round(len(dens_url)/1.37e6,2), round(len(lbl_url)/1.37e6,2))

# QC: a few axial/coronal/sagittal stills through iso
def save_qc(vol3d, idx, axis, path):
    sl = {0:vol3d[idx,:,:],1:vol3d[:,idx,:],2:vol3d[:,:,idx]}[axis]
    Image.fromarray(np.rot90(sl.astype(np.uint8)),'L').save(path)
save_qc(dens, iso[2], 2, '/tmp/spinecbct_axial.png')         # axial at iso z
save_qc(dens, iso[1], 1, '/tmp/spinecbct_coronal.png')       # coronal at iso y
save_qc(dens, iso[0], 0, '/tmp/spinecbct_sagittal.png')      # sagittal at iso x
# label overlay (cord+ptv+vertebra) on axial
ax_lbl = np.rot90(lblvol[:,:,iso[2]])
Image.fromarray((ax_lbl*40).astype(np.uint8),'L').save('/tmp/spinecbct_axial_lbl.png')
print('wrote QC stills to /tmp/spinecbct_*.png')
