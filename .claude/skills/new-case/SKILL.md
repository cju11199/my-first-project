---
name: new-case
description: Build and ship a new RT Image Matching Trainer case end to end — source free CC-BY DICOM from the NCI Imaging Data Commons, write a reproducible generator, wire it into trainer.html, update the three Phase-2 allowlists, build-verify, and open a draft PR (plus the post-merge Blob upload). Use whenever the user asks to add a new 2D/2D or CBCT case.
---

# /new-case — add a trainer case end to end

This repo has shipped ~8 cases through the same pipeline. Follow it so nothing is half-plumbed.
Read `CLAUDE.md` first — it documents every existing generator and the exact wiring points.

There are **two case types**; pick the matching template:
- **2D/2D** (orthogonal-pair DRR match) — templates: `generate_femur_2d.py`, `generate_prostate_2d.py`.
- **CBCT** (3D volumetric 6DOF) — templates: `generate_pancreas_cbct.py`, `generate_liver_sbrt.py`
  (DICOM-SEG source), `generate_vs_mr.py` (MR, not CT).

## 1 — Source the data (free, commercially licensable)

TCIA's website is network-blocked here; use the **NCI Imaging Data Commons** public bucket
`s3://idc-open-data` via the `idc-index` PyPI package (also carries the authoritative licence):
```python
from idc_index import index
c = index.IDCClient(); df = c.index           # collection_id, PatientID, Modality, license_short_name, ...
# filter to a collection/modality, pick a patient, then:
c.download_from_selection(downloadDir=DEST, seriesInstanceUID=[...])
```
- **Licence must allow commercial use** — check `license_short_name` (want CC BY 3.0/4.0). Bake the
  attribution + DOI into the generated data-file header.
- Want a real target ROI (RTSTRUCT or DICOM-SEG) when possible; only synthesize a PTV if the
  collection has none, and tell the user that's what you're doing.
- For picking among candidate patients, an `ultracode` Workflow that builds + QC-renders several in
  parallel and judges the stills works well (see how the sarcoma/PTV cases were chosen).

## 2 — Write the generator

Copy the closest template. Output the same tiled-atlas format the others use (CBCT) or append
`*_SRC` base64 PNGs to `image_data.js` (2D, like femur). Always write **QC stills to /tmp** and
review them with the Read tool before wiring. Re-run is in-place / idempotent.
- HU↔density: `HU = density*(2000/255) - 500`. For DRRs prefer a true **Beer–Lambert** path
  integral (`∫μ·dl`, two-segment HU→μ) over a fake power curve — see `generate_femur_2d.py`.

## 3 — Wire trainer.html

**2D/2D case** (search for an existing key like `thorax`/`femur` and mirror it):
- `CASES.<key>` object (`ap:null, lat:null, iso:{...}, tilt:null|'<base>'`).
- `hydrate2DCases()` assignment (`CASES.<key>.ap = <KEY>_AP_SRC; …`).
- Start-screen picker: `CASE_LISTS['2d2d'].cases`.
- In-app dropdown: the `#caseSelect` `<option>`.
- `CASE_TOL['2d2d:<key>']` (translation/rotation accept+close, mm/°).
- If the file isn't `image_data.js`, update `file2dFor`/`ready2dFor`.

**CBCT case** (mirror an existing volumetric key like `lung`/`liver`):
- `VOLCASE.<key>` (filenames, `win:{l,w}`, `mr:true` if MR, optional `offBone` config).
- `CASE_TOL['cbct:<key>']`, `<CASE>_STRUCTS`, `<CASE>_LBL`/`<CASE>_ISO_IDX` vars, `_<case>CtrCache`.
- The four `cur*` switches (`curLBL`/`curStructs`/`curIsoIdx`/`curCtrCache`), the `loadLabelMPR`
  dispatch, the `_load<Case>LabelMPR` + `_decode<Case>Labels` pair, the `applyCase` contour-on list.
- Picker card in `CASE_LISTS['cbct'].cases`; legend rows + `applyCaseLegend` show() calls.

## 4 — Phase-2 allowlists (all three, or it 404s live)

Add every new `*_data.js` file to **all three**:
1. `scripts/upload-to-blob.mjs` → `DATASETS`
2. `api/asset.mjs` → `DATASETS` Set
3. `.vercelignore`

(A 2D case that only appends `*_SRC` to the existing `image_data.js` needs **no** allowlist change —
`image_data.js` is already listed — but the Blob still must be re-uploaded in step 7.)

Verify with: `node scripts/check-allowlists.mjs` (must report all in sync).

## 5 — Build-verify

```bash
node build-trainer.mjs --out && rm -f trainer.min.html clerk-auth.min.js
```
Must minify clean (terser parse + served-output gate invariants). The pre-push hook runs this too.

## 6 — Document, commit, push, draft PR

- Add a generator bullet to `CLAUDE.md` (and the case to the Cases list).
- Develop on a feature branch; commit with the standard co-author/session trailers.
- `git push -u origin <branch>` (the pre-push hook gates allowlists + build).
- Open a **draft** PR. Send the QC stills to the user. Note that **real-browser rendering still
  needs a check** (headless can't verify the live canvas).

## 7 — After merge: refresh the Blob

The data files are `.vercelignore`d, so merging never updates the blob. Run the **`/check-blob`**
skill (or trigger the "Upload data to Blob" Action from `main` and confirm success). Until then the
new case 404s live.
