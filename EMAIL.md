# Domain email setup

How email for **rtimagematch.com** is configured.

## Current setup: Cloudflare Email Routing (forward-only)

- **Address:** `support@rtimagematch.com` — referenced in `terms.html` and `privacy.html`.
- **Provider:** Cloudflare Email Routing (DNS for the domain is managed in Cloudflare).
- **Behavior:** incoming mail to `support@` is **forwarded** to a personal destination inbox. This is receive-only — it does **not** send outbound *as* `support@rtimagematch.com`.

### Where to manage it
Cloudflare dashboard → `rtimagematch.com` → **Email → Email Routing**.
- Destination inboxes and custom-address rules live here.
- DNS records (MX + SPF TXT) were added automatically by Email Routing; they live under **DNS → Records**.

### To test
Send an email to `support@rtimagematch.com` from any other account — it should arrive in the destination inbox within seconds. The Email Routing page shows an activity log of received mail.

## If we ever need to *send* from the address

Cloudflare Email Routing can't send outbound. To reply *as* `support@rtimagematch.com`
(with valid SPF/DKIM so mail isn't spam-flagged), switch to a real mailbox:

- **iCloud+ Custom Email Domain** — included with any paid iCloud+ plan; real send/receive via Apple Mail.
- **Google Workspace / Microsoft 365** — ~$6–7/mo.
- **Zoho Mail** — has a free tier with a real mailbox.

Switching means replacing the Cloudflare MX records with the new provider's (they can't coexist).

## DNS records (reference)

- **MX** → Cloudflare's `route1/2/3.mx.cloudflare.net` (added automatically by Email Routing).
- **SPF (TXT)** → added automatically by Email Routing.
- **DMARC (TXT, optional)** → `_dmarc` = `v=DMARC1; p=none; rua=mailto:support@rtimagematch.com`
  (only relevant once sending outbound).
