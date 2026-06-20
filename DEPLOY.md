# Deploying to Vercel

This is a static site (a single `index.html` plus data `.js` files and images in
`/drr`). No build step is required — Vercel serves the files directly.

## 1. Import the repo into Vercel

1. Go to <https://vercel.com> and sign in with GitHub.
2. **Add New… → Project**.
3. Select the `cju11199/my-first-project` repository → **Import**.
4. **Framework Preset:** leave as **Other** (it's plain static).
5. Leave **Build Command** and **Output Directory** empty.
6. Click **Deploy**.

Vercel gives you a free URL like `my-first-project.vercel.app` once it finishes.

## 2. Connect the custom domain (rtimagematch.com)

After buying the domain at a registrar (e.g. Cloudflare or Namecheap):

1. In Vercel: **Project → Settings → Domains → Add**.
2. Enter `rtimagematch.com` and also add `www.rtimagematch.com` (Vercel will offer
   to redirect www → root, which is fine).
3. Vercel shows the DNS records to create. Typically:
   - `A` record for `@` → `76.76.21.21`
   - `CNAME` record for `www` → `cname.vercel-dns.com`
   (Use whatever values Vercel displays — they are authoritative.)
4. Add those records at your registrar's DNS settings.
5. Wait a few minutes; Vercel auto-issues the HTTPS certificate. Done.

## 3. Updates

Every push to the production branch redeploys automatically. Pull requests get
their own preview URL.

## Notes

- `vercel.json` sets caching for the large data files and basic security headers.
- The paywall (auth + Stripe subscription) is a planned later phase and will
  require restructuring so the app is served only to authenticated subscribers.
