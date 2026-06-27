#!/usr/bin/env python3
"""De-ring the bladder in the pelvis CBCT volumes.

The bladder in the pelvis plan is a smooth, uniform synthetic fill (~0 HU). It is
ringed by a thin band of real perivesical fat (HU ~ -60..-110) before the bright
surrounding pelvic tissue. Because the bladder fill is so clean and the surroundings
are bright, that fat band reads as a stark dark *halo* hugging the bladder wall.

This in-place editor lifts ONLY the dark perivesical voxels in a thin shell around
the bladder label up toward the bladder's own gray, feathered by distance, so the
halo blends away. Bright tissue is never darkened, the bladder interior is untouched,
and the bladder contour (drawn from the label volume) is unchanged.

Re-runnable: reads each *_data.js, rewrites its `.atlas=` data-URI in place.
Needs numpy / scipy / pillow. Browser-verify the canvas result after running.
"""
import base64, io, re, sys
import numpy as np
from PIL import Image
from scipy import ndimage

# (volume data file, label data file, VOL global, LABELS global)
PAIRS = [
    ("pelvis3d_data.js",   "pelvis3d_labels_data.js",   "PELVIS3D_VOL",   "PELVIS3D_LABELS"),
    ("prostate3d_data.js", "prostate3d_labels_data.js", "PROSTATE3D_VOL", "PROSTATE3D_LABELS"),
]

SHELL_VOX   = 3       # de-ring within this many voxels of the bladder wall
FAT_DENS    = 62      # only lift voxels darker than this (HU ~ +5); fat is ~50-56
SMOOTH_SIG  = 0.8     # gentle blur inside the shell so the lift has no new hard edge


def _hdr_json(text, glob):
    """Return the JSON object literal assigned to `const <glob>={...};`."""
    m = re.search(r"const\s+" + re.escape(glob) + r"\s*=\s*(\{.*?\});", text, re.S)
    if not m:
        sys.exit(f"could not find header for {glob}")
    import json
    return json.loads(m.group(1)), m


def _atlas_datauri(text, glob):
    m = re.search(re.escape(glob) + r"\.atlas\s*=\s*'(data:image/png;base64,[^']+)'", text)
    if not m:
        sys.exit(f"could not find atlas for {glob}")
    return m.group(1), m


def _decode(datauri, dims, tpr):
    X, Y, Z = dims
    b64 = datauri.split(",", 1)[1]
    img = Image.open(io.BytesIO(base64.b64decode(b64)))
    arr = np.asarray(img.convert("RGB"))                 # (H, W, 3); density in R (grayscale)
    vol = np.zeros((Z, Y, X), np.uint8)
    chan = arr[..., 0]
    for z in range(Z):
        tc, tr = z % tpr, z // tpr
        vol[z] = chan[tr * Y:(tr + 1) * Y, tc * X:(tc + 1) * X]
    grayscale = bool(np.array_equal(arr[..., 0], arr[..., 1]) and np.array_equal(arr[..., 1], arr[..., 2]))
    return vol, (arr.shape[0], arr.shape[1]), grayscale


def _encode(vol, atlas_hw, tpr):
    Z, Y, X = vol.shape
    H, W = atlas_hw
    canvas = np.zeros((H, W), np.uint8)
    for z in range(Z):
        tc, tr = z % tpr, z // tpr
        canvas[tr * Y:(tr + 1) * Y, tc * X:(tc + 1) * X] = vol[z]
    buf = io.BytesIO()
    Image.fromarray(canvas, "L").save(buf, format="PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def dering(vol, bmask):
    """Lift the dark perivesical fat shell around the bladder toward the bladder gray."""
    vol = vol.astype(np.float32)
    target = float(np.median(vol[bmask]))                # the bladder fill value (~64)
    # feather weight: 1.0 right at the wall -> 0 at SHELL_VOX away, restricted to outside the bladder
    dist = ndimage.distance_transform_edt(~bmask)
    w = np.clip((SHELL_VOX - dist) / SHELL_VOX, 0.0, 1.0)
    w[bmask] = 0.0
    shell = (w > 0) & (vol < FAT_DENS)                   # only the dark (fat) voxels in the shell
    lifted = vol.copy()
    lifted[shell] = vol[shell] + (target - vol[shell]) * w[shell]   # raise dark fat toward bladder gray
    # blur just the lifted region a touch so the transition is smooth, then keep max(orig, smoothed)
    sm = ndimage.gaussian_filter(lifted, SMOOTH_SIG)
    out = vol.copy()
    band = w > 0
    out[band] = np.maximum(vol[band], np.minimum(lifted[band], sm[band] + (target - sm[band]) * 0))
    out[band] = np.where(vol[band] < target, np.maximum(vol[band], lifted[band]), vol[band])
    return np.clip(out, 0, 255).astype(np.uint8), target, int(shell.sum())


def qc(vol0, vol1, bmask, cz, cy, tag):
    """Write a before/after QC strip of the bladder axial slice."""
    import json
    z = cz
    def norm(a):
        l, w = 40, 460
        g = np.clip((a.astype(np.float32) * (2000/255) - 500 - (l - w/2)) / w, 0, 1)
        return (g * 255).astype(np.uint8)
    a, b = norm(vol0[z]), norm(vol1[z])
    gap = np.full((a.shape[0], 6), 60, np.uint8)
    strip = np.concatenate([a, gap, b], axis=1)
    Image.fromarray(strip, "L").resize((strip.shape[1]*4, strip.shape[0]*4), Image.NEAREST).save(
        f"/tmp/claude-0/-home-user-my-first-project/6aa7a103-5fb7-5963-93a4-52f821502593/scratchpad/dering-qc-{tag}.png")


def process(vol_file, lbl_file, vol_glob, lbl_glob, write):
    vtext = open(vol_file).read()
    ltext = open(lbl_file).read()
    vhdr, _ = _hdr_json(vtext, vol_glob)
    lhdr, _ = _hdr_json(ltext, lbl_glob)
    dims, tpr = vhdr["dims"], vhdr["tilesPerRow"]
    vuri, vm = _atlas_datauri(vtext, vol_glob)
    luri, _ = _atlas_datauri(ltext, lbl_glob)
    vol, atlas_hw, gray = _decode(vuri, dims, tpr)
    lab, _, _ = _decode(luri, lhdr["dims"], lhdr["tilesPerRow"])
    bbit = lhdr["bits"]["bladder"]
    bmask = (lab & bbit) > 0
    ys, xs, zs = np.where(bmask.transpose(2, 1, 0))  # just for centroid
    idx = np.argwhere(bmask)
    cz, cy, cx = idx.mean(0).round().astype(int)
    out, target, nshell = dering(vol, bmask)
    qc(vol, out, bmask, cz, cy, vol_glob)
    changed = int((out != vol).sum())
    print(f"{vol_file}: dims={dims} grayscale={gray} bladder_vox={int(bmask.sum())} "
          f"target_gray={target:.0f} shell_dark_vox={nshell} voxels_changed={changed} "
          f"centroid=({cx},{cy},{cz})")
    if write:
        new_uri = _encode(out, atlas_hw, tpr)
        vtext2 = vtext[:vm.start(1)] + new_uri + vtext[vm.end(1):]
        open(vol_file, "w").write(vtext2)
        print(f"  -> wrote {vol_file} ({len(vtext2)} bytes)")


if __name__ == "__main__":
    write = "--write" in sys.argv
    for vf, lf, vg, lg in PAIRS:
        process(vf, lf, vg, lg, write)
    if not write:
        print("\nDRY RUN — QC strips written to scratchpad/dering-qc-*.png. Re-run with --write to apply.")
