# /check-blob — verify allowlists & refresh the Blob store

<!--
  Codex custom prompt. Copy or symlink this file into `~/.codex/prompts/` to invoke it as
  `/check-blob` inside Codex. Ported from `.claude/skills/check-blob/SKILL.md` — keep the two in sync.
-->

Verify every case-data file is wired into all three Phase-2 allowlists, then (re-)upload the case
data to the private Vercel Blob store. Use after merging a new case, or any time you suspect the blob
is stale / a case 404s live.

The paid case data is served only through `/api/asset` from a **private Vercel Blob** store.
A case is live only if its `*_data.js` files are (a) in all three Phase-2 allowlists and
(b) actually uploaded to the blob. This prompt checks (a) and does (b).

## Steps

1. **Make sure you're on `main` and up to date** (the blob should reflect what's deployed):
   ```bash
   git fetch origin main -q && git switch main && git pull --ff-only origin main
   ```
   If the user wants to check a branch instead, skip this and note which ref you're on.

2. **Run the allowlist sync check:**
   ```bash
   node scripts/check-allowlists.mjs
   ```
   This compares the `*_data.js` files in the repo root against the three lists that must
   stay in lockstep:
   - `scripts/upload-to-blob.mjs` → `DATASETS` (what the Action uploads)
   - `api/asset.mjs` → `DATASETS` Set (what `/api/asset` will serve)
   - `.vercelignore` (keeps the data OFF the public CDN)

   - **If it reports problems** (missing or stale entries): STOP and fix the lists first — a
     case missing from all three 404s live (or, worse, a missing `.vercelignore` entry ships
     private data to the public CDN). Add the file to each list, commit, and only then upload.
   - **If it's all in sync:** continue.

3. **Trigger the upload Action** (`.github/workflows/upload-blob.yml`, needs the repo secret
   `BLOB_READ_WRITE_TOKEN`). Use the GitHub MCP tools:
   - `actions_run_trigger` with `method: "run_workflow"`, `workflow_id: "upload-blob.yml"`, `ref: "main"`.

4. **Confirm it succeeded.** Poll the run's jobs and verify the `Run node scripts/upload-to-blob.mjs`
   step `conclusion: "success"`:
   - `actions_list` → `list_workflow_runs` for `upload-blob.yml` to get the newest run id.
   - `actions_list` → `list_workflow_jobs` for that run id; check the `upload` job's steps.
   - (The list payloads can be large — if a result is truncated to a file, parse it with a small
     python/jq slice rather than reading the whole thing.)

5. **Report** the result to the user: in-sync count, the run URL, and pass/fail. If anything was
   out of sync or the upload failed, say exactly what and what you did about it.

## Notes
- The upload is **idempotent** (`allowOverwrite:true`), so re-running is always safe.
- This is the standard **post-merge** step for any new case — the data files are `.vercelignore`d,
  so merging alone never refreshes the blob; this Action is the only thing that does.
