#!/usr/bin/env python3
"""
generate_hn_2d.py
Build the 2D/2D **Head & Neck** case: orthogonal-pair (AP + Lateral) bone-emphasised DRRs of the
WHOLE head + neck, ray-summed from a real diagnostic head-and-neck CT (TCIA **TCGA-THCA** patient
TCGA-DE-A4MA, "CT HeadNeck 3.0 B31s"). Shows the full cranium (closed cranial vault / vertex),
skull base, mandible and the entire cervical spine down to the clavicles/shoulders — the bony
landmarks the student aligns. Flat (tilt:null) orthogonal pair, riding the existing 2D/2D DRR
infrastructure like Femur / Spine 2D.

This series is a clean **axial HFS** acquisition (148 slices, 0.98 mm in-plane, uniform 1.5 mm,
220 mm SI span) with **NO burned-in de-ID redaction box** (verified box0px≈53 = background air,
nowhere near the thousands-of-pixels signature of a redaction block). So — unlike the earlier
sagittal varepop source — there is no box to inpaint and no orientation-agnostic resample needed;
patient axes are x=LR (cols), y=AP (rows), z=SI (stack), exactly like the Spine 2D case.

Rendering: a true Beer–Lambert path integral (two-segment HU→μ, bone-emphasised); the float
line-integral is LANCZOS-upscaled in 32-bit before quantising, a per-view percentile contrast stretch
windows soft tissue toward black so the cranium / cervical column / mandible read as the bright bony
landmarks, an unsharp mask crisps the edges, rendered at 768 px.

Output: appended to image_data.js (idempotent) as HN_AP_SRC / HN_LAT_SRC; prints CASES.hn iso.
Licence: TCIA TCGA-THCA, CC BY 3.0 — attribute doi:10.7937/k9/tcia.2016.9zfrvf1b.
Needs pydicom / numpy / scipy / pillow.
"""
import os, glob, io, base64, re
import numpy as np
import pydicom
from scipy import ndimage
from PIL import Image, ImageFilter

CTDIR = 'scratchpad/hn_thca'

# ── Load the CT volume (z,y,x) in HU — axial HFS, sort inferior→superior ──────
sl = [pydicom.dcmread(f) for f in glob.glob(os.path.join(CTDIR, '**', '*.dcm'), recursive=True)]
sl.sort(key=lambda d: float(d.ImagePositionPatient[2]))
vol = np.stack([s.pixel_array.astype(np.float32)*float(s.RescaleSlope)+float(s.RescaleIntercept) for s in sl])
DZ, DY, DX = vol.shape
psy, psx = [float(v) for v in sl[0].PixelSpacing]                 # row(y), col(x) spacing mm
dz = abs(float(sl[1].ImagePositionPatient[2]) - float(sl[0].ImagePositionPatient[2]))
print(f'CT {DX}x{DY}x{DZ}  spacing x={psx:.3f} y={psy:.3f} z={dz:.3f} mm  HU[{vol.min():.0f},{vol.max():.0f}]')

# ── Body mask: drop the couch/headrest + air so the lateral isn't summed through the table ──
body = ndimage.binary_fill_holes(vol > -350)
lab, n = ndimage.label(body)
sizes = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1))
body = lab == (1 + int(np.argmax(sizes)))                        # largest blob = patient
vol = np.where(body, vol, -1000.0)

# ── Crop in-plane to the patient bbox (+margin); keep the full SI extent (vertex→shoulders) ──
zz, yy, xx = np.where(body); M = 8
x0, x1 = max(0, xx.min()-M), min(DX, xx.max()+M)
y0, y1 = max(0, yy.min()-M), min(DY, yy.max()+M)
ct = vol[:, y0:y1, x0:x1].astype(np.float32)
print(f'body-cropped → {ct.shape[::-1]}')

# ── Beer–Lambert DRR: integrate linear attenuation along each ray (two-segment HU→μ, bone-bright) ──
MU_W, BONE_GAIN = 0.206, 3.0
mu = np.where(ct < 0.0, MU_W*(1.0 + ct/1000.0), MU_W*(1.0 + (ct/1000.0)*BONE_GAIN))
mu = np.clip(mu, 0.0, None)
def project(axis, dl_mm):
    A = (mu.sum(axis=axis) * (dl_mm/10.0))[::-1].astype(np.float32)      # flip z → superior(head) at TOP
    pad = max(6, round(A.shape[0]*0.06))                                 # black margin so the vertex isn't flush
    return np.pad(A, ((pad, pad), (0, 0)), mode='constant')
# render at PHYSICALLY-correct aspect: rows are z (dz mm/px), cols are in-plane (col_mm/px); the
# anisotropic z vs in-plane spacing would otherwise stretch the anatomy horizontally ~1.5x.
def render(A, col_mm, target_h=768):
    h, w = A.shape
    mm_h, mm_w = h*dz, w*col_mm
    tw = max(1, round(target_h * mm_w/mm_h))
    U = np.asarray(Image.fromarray(A, 'F').resize((tw, target_h), Image.LANCZOS), np.float32)
    lo, hi = np.percentile(U, 45), np.percentile(U, 99.7)
    d = np.clip((U - lo)/(hi - lo + 1e-6), 0, 1) ** 0.9
    im = Image.fromarray((d*255).astype(np.uint8), 'L').filter(ImageFilter.UnsharpMask(radius=2.0, percent=120, threshold=1))
    buf = io.BytesIO(); im.save(buf, 'PNG', compress_level=9)
    return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode('ascii'), im.size
ap_url, ap_sz   = render(project(1, psy), psx)   # sum over y(AP) → rows=z(SI), cols=x(LR)
lat_url, lat_sz = render(project(2, psx), psy)   # sum over x(LR) → rows=z(SI), cols=y(AP)
print(f'AP png {ap_sz}  LAT png {lat_sz}')

# ── iso = cervical column (bone centroid, posterior-central, mid-z) ───────────
CH, CY, CX = ct.shape
pad = max(6, round(CH*0.06)); HT = CH + 2*pad                    # match the rendered z padding
bone = ct > 250
col = np.zeros_like(bone)
col[:, int(CY*0.50):, int(CX*0.32):int(CX*0.68)] = bone[:, int(CY*0.50):, int(CX*0.32):int(CX*0.68)]
bz, by, bx = np.where(col)
fy = round((pad + (CH - 1 - bz.mean()))/HT, 3)                   # flip(z)+pad → fractional row of iso
iso = {'ap':  {'x': round(float(bx.mean())/CX, 3), 'y': fy},
       'lat': {'x': round(float(by.mean())/CY, 3), 'y': fy}}
print('CASES.hn iso:', iso)

# ── Append to image_data.js (idempotent) ──────────────────────────────────────
with open('image_data.js') as f: cur = f.read()
cur = re.sub(r'\n// ── Head & Neck 2D/2D case .*?const HN_LAT_SRC="[^"]*";\n', '', cur, flags=re.S)
block = ('\n// ── Head & Neck 2D/2D case ────────────────────────────────────────────────\n'
         '// AP + Lateral bone-emphasised DRRs ray-summed from a diagnostic head-and-neck CT (TCIA\n'
         '// TCGA-THCA TCGA-DE-A4MA, "CT HeadNeck 3.0 B31s"; full cranial vault + neck to shoulders,\n'
         '// clean axial HFS, no de-ID box). Cervical-spine / mandible / skull-base bony match.\n'
         '// CC BY 3.0 — doi:10.7937/k9/tcia.2016.9zfrvf1b.\n'
         f'const HN_AP_SRC="{ap_url}";\nconst HN_LAT_SRC="{lat_url}";\n')
with open('image_data.js', 'w') as f: f.write(cur + block)
print('wrote HN_AP_SRC / HN_LAT_SRC to image_data.js (idempotent)')
Image.open(io.BytesIO(base64.b64decode(ap_url.split(',')[1]))).save('/tmp/hn_ap_qc.png')
Image.open(io.BytesIO(base64.b64decode(lat_url.split(',')[1]))).save('/tmp/hn_lat_qc.png')
print('wrote /tmp/hn_ap_qc.png  /tmp/hn_lat_qc.png')
