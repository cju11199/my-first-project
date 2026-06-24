# Cohorts + Leaderboard — Implementation Plan

> Planning doc only. No application code changes. Grounded in the current `main` code
> (`clerk-auth.js`, `trainer.html`, the `api/` serverless pattern).

## 0. How the app works today (the ground truth)

**Identity / auth — Clerk, client-side gate.**
- `clerk-auth.js` host-detects prod vs dev Clerk keys, gates pages with `<body data-require-auth>`,
  and exposes `window.RTAuth` (`ready`, `hasActiveSub()`, `PLAN_KEY='full_access'`, `profile`).
- Plan check: `session.checkAuthorization({ plan: 'full_access' })`; comp/free tiers via
  `isComped()` (owner emails + `COMP_DOMAINS` institution domains like `stonybrook.edu`).
- A session JWT is available client-side via `Clerk.session.getToken()`.
- **No Clerk Organizations are used today.**

**Progress / scoring — entirely client-side, persisted to Clerk metadata.**
- `rtRecord(mode, caseKey, {accepted, mag, timeMs})` (`trainer.html` ~L2658) is called from all three
  scorers: `checkMatch()` (2D, ~L2413), `CBCT.check()` (~L3736), `FID2D.check()` (~L1576).
- It computes **XP** (base 4; +60 first clear; +20 accept; +15 if `<30 s`; +20 if residual `<0.5 mm`;
  +15 strict / −10 relaxed — ~L2664-2676), **level** `floor(sqrt(xp/40))+1` (~L2629), a daily streak,
  a 24-entry recent ring, per-case bests (`bt` time, `br` residual), and a 13-badge catalogue `RT_ACH`.
- It is stored in **Clerk `unsafeMetadata.rt`** (`clerk-auth.js` ~L165-275): debounced, merge-safe save
  via `user.update({ unsafeMetadata })`. `unsafeMetadata` is **writable from the client** and ~8 KB-capped.

**The case "truth" (correct answer) is generated and graded client-side.**
- 2D DRR cases: a hidden offset `hidden` is set by `randomizeShift()` (~L2360) using `Math.random()`.
- CBCT cases: `CBCT.randomize()` (~L3722) sets `hidden` + an off-bone `targetDrift`.
- 2D fiducial (prostate): `FID2D.randomize()` (~L1563) sets `Qtrue`/`hiddenE`.
- Grade = `shift − hidden` compared to `rtTol()` thresholds (`RT_DIFF` ~L2626). The reported `mag`/`timeMs`
  are computed client-side and written to client-writable metadata.

**Serverless pattern that already exists** (the template for new endpoints): `api/*.js` Vercel
functions using `@clerk/backend` `createClerkClient().authenticateRequest()` to verify a `Bearer`
token, then `auth.has({ plan })`. (See the `api/unlock.js`/`api/asset.js` R2-gate functions.)

### Two facts that drive every decision below
1. **`unsafeMetadata` is client-writable** → today's XP/stats are trivially forgeable. **A leaderboard
   must NOT rank on metadata.** It must rank on values recorded **server-side** in a real DB.
2. **The case truth must be client-side to render the misaligned image** (the moving DRR/MPR is drawn
   offset by `hidden`). Server-side validation can stop *fabricated* submissions but **cannot fully
   hide the answer** from a determined user. Be honest about this (§3).

---

## 1. Cohorts

### Option A — Clerk Organizations (recommended primary)
Model: **cohort = Clerk Organization**, **instructor = `org:admin`**, **student = `org:member`**.
- **Pros:** invitations, join, roles, and membership management are **built in** — Clerk ships the
  invite email flow, role enforcement, and an `<OrganizationProfile>`/`<OrganizationSwitcher>` UI you can
  mount the same way `clerk-auth.js` already mounts Clerk widgets. The session token carries `org_id` +
  `org_role` claims, so server endpoints authorize cohort access from the **verified JWT** (no extra
  lookup). A student in multiple classes = multiple orgs (native). Reuses the identity layer you already run.
- **Cons:** adds a Clerk **pricing** consideration (see §5) and a dependency; the active-org concept adds a
  little client state; overkill if you'll only ever have a couple of classes.

### Option B — Cohort membership in the app DB + join codes (recommended fallback / MVP-friendly)
Model: `cohorts` + `memberships` rows in our own DB (see §2); instructor generates a **join code**; a
student enters it to enroll; `memberships.role` holds `instructor|student`.
- **Pros:** zero added cost/dependency, full control over enrollment UX, no Clerk tier change, trivially
  supports join codes/CSV import.
- **Cons:** you **build** invitations/roles/management yourself; role checks need a DB lookup per request
  (cheap with an index); no managed invite emails.

### Option C — cohort-ID in Clerk `publicMetadata` (not recommended)
Storing a cohort id on the user works for a single cohort, but `metadata` is ~8 KB, awkward for
many-to-many (a student in N cohorts, a cohort with M students), and you still need the DB for results.
Skip it as the source of truth; at most mirror the "active cohort" there for convenience.

### Recommendation
**Use Clerk Organizations as the cohort/role/identity primitive (Option A)** *if* the Clerk tier is
acceptable — it removes the most error-prone work (invites + roles). The **DB still stores all results**,
keyed by `clerk_org_id` + `clerk_user_id` read from the verified session. **If you want zero added cost
or expect very few cohorts, ship Option B** (DB cohorts + join codes) for the MVP and migrate to Orgs later
— the results schema is identical either way (a cohort is just an id), so this choice is reversible.

**Enrollment flow (either option):**
- *Instructor*: signs in → "Create cohort" (Org create, or DB row + generated join code) → gets an invite
  link / join code → shares with students. Instructor role = `org:admin` or `memberships.role='instructor'`.
- *Student*: signs in → accepts invite (Orgs) or enters join code (DB) → becomes `member`/`student`.
- Gate the instructor dashboard on the instructor role (JWT `org_role` or `memberships.role`).

---

## 2. Data store + schema

### Choice: **Neon Postgres via the Vercel Postgres integration** (with `@neondatabase/serverless`)
Compared for a **solo dev already on Vercel**:
- **Neon / Vercel Postgres (pick this):** one-click Vercel integration auto-wires `DATABASE_URL` into the
  same env system the `R2_*`/`CLERK_*` vars already use; an **HTTP/serverless driver** that fits Vercel
  functions (no connection-pool exhaustion); **scale-to-zero free tier** (~0.5 GB) that easily covers
  thousands of students; plain Postgres → no lock-in.
- **Supabase:** great product, but its headline feature is **auth**, which **Clerk already provides** —
  so you'd be paying complexity for a redundant auth stack, and wiring Clerk JWTs into Supabase RLS is
  extra work. Worth it only if you want its realtime/storage. Not for this app.
- **Net:** Neon/Vercel Postgres = least config, lowest cost, best fit. (Supabase is the runner-up if you
  later want realtime leaderboard pushes.)

### Schema (Postgres)
```sql
-- A cohort/class. clerk_org_id set when using Clerk Organizations (Option A); else NULL + join_code.
cohorts(
  id            uuid pk default gen_random_uuid(),
  clerk_org_id  text unique,            -- nullable; present in Org mode
  name          text not null,
  join_code     text unique,            -- nullable; present in DB-cohort mode
  created_by    text not null,          -- clerk_user_id of the instructor
  created_at    timestamptz default now(),
  archived      boolean default false
)

-- Who is in a cohort and their role. (Mirror of Clerk org membership, or the source of truth in DB mode.)
memberships(
  id          uuid pk default gen_random_uuid(),
  cohort_id   uuid references cohorts(id) on delete cascade,
  clerk_user_id text not null,
  role        text not null check (role in ('instructor','student')),
  joined_at   timestamptz default now(),
  unique (cohort_id, clerk_user_id)
)

-- The raw, server-recorded attempt log — the ONLY trustworthy source for the leaderboard.
attempts(
  id           uuid pk default gen_random_uuid(),
  clerk_user_id text not null,
  mode         text not null,           -- '2d2d' | 'cbct'
  case_key     text not null,           -- 'pelvis','brain','spine','breast','prostate','lung',...
  difficulty   text not null,           -- 'relaxed'|'standard'|'strict'
  accepted     boolean not null,
  residual_mm  numeric(6,2),            -- translation residual magnitude (the 'mag')
  rot_residual_deg numeric(6,2),        -- where applicable (CBCT/FID)
  time_ms      integer,
  xp_awarded   integer not null default 0,  -- server-computed (mirror of the client formula)
  seed_id      uuid references case_seeds(id), -- links to the issued truth (validation phase)
  validated    boolean not null default false, -- true once server-graded against the seed
  client_meta  jsonb,                   -- difficulty, view, input-event count, solve path summary
  created_at   timestamptz default now()
)
create index on attempts (clerk_user_id, case_key);
create index on attempts (case_key, created_at);
create index on attempts (accepted, residual_mm);

-- Server-issued case truth (validation phase, §3). One row per "start", consumed on submit.
case_seeds(
  id            uuid pk default gen_random_uuid(),
  clerk_user_id text not null,
  mode          text not null,
  case_key      text not null,
  difficulty    text not null,
  truth         jsonb not null,         -- {hidden:{x,y,z,roll,pitch,yaw}, targetDrift?, Qtrue?}
  issued_at     timestamptz default now(),
  consumed_at   timestamptz             -- set on submit; reject if already set (one attempt per seed)
)

-- Denormalized per-(user,case) bests for fast leaderboards. Upserted on each validated submit.
user_case_best(
  clerk_user_id text not null,
  case_key      text not null,
  best_residual_mm numeric(6,2),
  best_time_ms     integer,
  clears        integer not null default 0,
  attempts      integer not null default 0,
  total_xp      integer not null default 0,
  updated_at    timestamptz default now(),
  primary key (clerk_user_id, case_key)
)
```
Leaderboards read from `user_case_best` (overall = aggregate across cases) joined to `memberships`
for cohort scope. At small scale plain indexed queries suffice; if it grows, add a **materialized view**
refreshed every few minutes. Personal stats/badges can stay in `unsafeMetadata` for instant UX, but the
**authoritative** numbers live in `attempts`/`user_case_best`.

---

## 3. Score submission + server-side validation

### The hard truth (be honest)
The moving image is **rendered offset by the answer**, so the client must know the offset. Therefore:
- A server can stop **fabricated** scores ("I POSTed 0.0 mm without playing").
- A server **cannot** stop a determined user who reads `hidden`/`Qtrue` from memory and submits the exact
  answer. Browser memory is inspectable. **This is a good-faith competitive leaderboard, not an exam.**
- True exam-grade integrity would require **server-side rendering** of the moving DRR/MPR at a secret
  offset (stream frames; kills the interactive viewer) or a **proctored mode** — out of scope.

### Recommended flow ("server-issued seed + server-authoritative grade")
1. **Start:** `POST /api/attempt/start { mode, caseKey, difficulty }` → server generates the hidden offset
   server-side (the logic currently in `randomizeShift`/`CBCT.randomize`/`FID2D.randomize`), stores it in
   `case_seeds`, returns `{ seedId, truth }` (the client needs `truth` to render the misalignment).
2. **Play:** client renders + lets the user register, exactly as today. Client-side grading stays for
   **instant feedback** (no UX regression).
3. **Submit:** `POST /api/attempt/submit { seedId, shift, timeMs, inputEvents }` → server loads the seed
   (reject if `consumed_at` set), **recomputes** `residual = shift − truth` and grades against `rtTol`
   server-side, computes `xp_awarded` with the same formula (port of L2664-2676), writes `attempts` +
   upserts `user_case_best`, marks the seed consumed. The **server's grade is authoritative** for the board.

### What has to change in the app (future code work, not now)
- `randomizeShift` / `CBCT.randomize` / `FID2D.randomize`: when signed in + leaderboard-enabled, fetch the
  offset from `/api/attempt/start` instead of `Math.random()` (keep `Math.random()` fallback for ungated/
  offline play).
- `checkMatch` / `CBCT.check` / `FID2D.check`: after local grading, `POST /api/attempt/submit`. Keep
  `rtRecord()` for local/personal stats; the **leaderboard reads the DB**, not metadata.
- New endpoints reuse the existing `@clerk/backend` Bearer pattern; same-origin `/api`, so the trainer CSP
  `connect-src 'self'` already permits them (no CSP change, unlike the R2 work).

### Anti-cheat heuristics (raise the cost; don't pretend to eliminate it)
- One result per issued `seedId` (consume the token); reject replays.
- Server-side **minimum plausible solve time** + rate limiting per user.
- Submit a compact **input-trajectory summary** (drag/scroll event count, total displacement); flag
  zero-interaction "instant perfect" submissions.
- **Statistical outlier flagging** for instructor review (e.g. impossible residual/time combos), rather
  than hard auto-bans.
- Leaderboard tie-breakers reward *consistency over many attempts*, which is harder to fake than one run.

---

## 4. Leaderboard — endpoints + UI

### Endpoints (all verify the Clerk session; cohort scope verifies membership)
- `GET /api/leaderboard?scope=overall|cohort|case&cohortId=&caseKey=&window=all|30d|7d|today&metric=accuracy|speed|xp|clears`
  → ranked rows `{ rank, userLabel, value, caseKey?, attempts }`. Server enforces: for `scope=cohort`,
  the requester must be a member; student labels visible to cohort-mates and instructors only (privacy).
- `GET /api/cohort/:id/roster` (instructor only) → members + per-student aggregates.
- `POST /api/cohort` (create), `POST /api/cohort/:id/join` (join code), `POST /api/cohort/:id/role` (Org
  mode delegates to Clerk). 
- Metrics: **accuracy** (min `best_residual_mm`), **speed** (min `best_time_ms` among clears),
  **XP** (sum), **clears** (count). Per-case and overall; time windows filter `attempts.created_at`.

### UI surfaces (future build)
- **Student leaderboard** — a new tab in the existing progress dashboard (`#rtProgModal`) or a `/leaderboard`
  page: toggles for Overall / My Cohorts / Per-Case and a time-window selector, with the student's own row
  highlighted. Reuses existing dashboard styling tokens.
- **Instructor dashboard** — a new gated page (e.g. `/instructor`), role-gated like `data-require-auth`
  but additionally requiring the instructor role: create/rename/archive cohorts, show join code / invite
  link, roster with per-student progress (attempts, clears, best residual/time, last active), CSV export,
  and an "outliers to review" list from the anti-cheat flags.

---

## 5. Phased build, effort, cost, risks

### Phases (solo-dev rough effort)
- **Phase 0 — Foundation & recording (MVP core).** Provision Neon; create `attempts` + `user_case_best`;
  add `POST /api/attempt/submit` (trust the client grade for now); wire `checkMatch`/`CBCT.check`/
  `FID2D.check` to also POST results. *Now there is trustworthy-enough data to build on.* **~2–4 days.**
- **Phase 1 — Cohorts.** Decide Orgs vs DB-cohorts; `cohorts`/`memberships`; create + join-code (or Org
  invites); instructor role gate; read-only instructor roster. **~3–5 days.**
- **Phase 2 — Leaderboard (MVP complete).** `/api/leaderboard` + student leaderboard UI
  (overall / cohort / per-case / windows). **~3–5 days.**
- **Phase 3 — Integrity.** Server-issued seeds + server-authoritative grading; `case_seeds`; anti-cheat
  heuristics + outlier flags. **~4–7 days.** (Honest: caps casual cheating, not determined.)
- **Phase 4 — Polish.** CSV export, cohort analytics, achievements board, managed email invites,
  optional realtime updates. **~3–5 days.**

**MVP = Phases 0–2** (record to DB, cohorts via join code or Orgs, basic leaderboard). Phase 3 makes the
board defensible; Phase 4 is nice-to-have.

### Cost (small/solo scale)
- **DB:** Neon / Vercel Postgres **free tier** (~0.5 GB, scale-to-zero) → **$0** for thousands of students;
  paid tiers only if you blow past free (~$19+/mo).
- **Clerk:** DB-cohort mode → **$0 extra**. Clerk **Organizations** mode → check current pricing: Orgs are
  included with limits on the free plan; **Pro (~$25/mo) + MAU-based usage** if you exceed them. *Verify the
  live Clerk pricing/limits before committing to Orgs — that's the one number that can change the rec.*
- **Vercel:** functions on the existing plan (Hobby free / Pro ~$20/mo) — already deployed.
- **Net MVP:** **~$0–25/mo.**

### Risks & integrity considerations
- **Cheating (primary):** see §3 — the answer is intrinsically client-visible; server validation stops
  fabrication, not memory-reading. Set expectations: this is competitive/good-faith, not proctored.
- **Don't trust `unsafeMetadata`:** it's client-writable, so the leaderboard must rank on **server-recorded
  DB rows**, never on the metadata XP. (Existing personal stats can keep using metadata for UX.)
- **Metadata 8 KB cap:** never store cohort rosters/membership lists in Clerk metadata — that's the DB's job.
- **Serverless DB connections:** use the HTTP/serverless driver (`@neondatabase/serverless`) to avoid pool
  exhaustion from many short-lived functions.
- **Student-data privacy (FERPA-adjacent):** storing identified student performance + cohorts is education
  data. Minimize what's stored, scope visibility (cohort-mates/instructor only), update the privacy policy,
  and consider per-institution agreements (ties into the existing `COMP_DOMAINS` institution model).
- **Reversibility:** the results schema is cohort-implementation-agnostic, so starting with DB-cohorts and
  later moving to Clerk Organizations is low-risk.

---

## TL;DR recommendations
- **Cohorts:** prefer **Clerk Organizations** (native invites/roles, JWT-scoped) if the Clerk tier is fine;
  otherwise ship **DB cohorts + join codes** for the MVP — the choice is reversible.
- **Store:** **Neon Postgres via Vercel Postgres** (Clerk already does auth, so Supabase is redundant weight).
- **Validation:** server-issues the seed and grades authoritatively; honest that it caps fabrication, not
  answer-reading — leaderboard ranks on **server-recorded** results, never client metadata.
- **Phasing:** record-to-DB → cohorts → leaderboard (MVP), then integrity, then polish. **~$0–25/mo.**
