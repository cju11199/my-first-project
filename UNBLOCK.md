# Getting rtimagematch.com unblocked on workplace / hospital networks

Corporate and hospital web filters block-by-default any domain they see as
**uncategorized / newly-seen**. The fix is not a code change — it's submitting the
domain to each major filter vendor and requesting an explicit category:

> **Primary category: Education**  ·  **Secondary: Health & Medicine**

Submissions are free and usually apply within 24–48h. Start with **Cisco Talos**
and **Zscaler** (the most common on hospital/enterprise networks).

## Vendor submission links

| Vendor | Submit at | Notes |
|---|---|---|
| Cisco Talos / Umbrella | https://talosintelligence.com/reputation_center/web_categorization | Needs a free Cisco account; track via "My Tickets". |
| Zscaler | https://sitereview.zscaler.com/ | Look up domain → "Submit for review." |
| Symantec / Blue Coat WebPulse | https://sitereview.symantec.com/ | Check category → suggest category → email. ~24–48h. |
| Palo Alto | https://urlfiltering.paloaltonetworks.com/ | "Test A Site" → request change (login required). |
| Fortinet FortiGuard | https://www.fortiguard.com/webfilter | Lookup → "Submit a URL for review." |
| McAfee / Trellix TrustedSource | https://trustedsource.org/ | Check + dispute category. |
| Webroot / OpenText BrightCloud | https://www.brightcloud.com/tools/url-ip-lookup.php | Lookup → "Request a change." |

For each: look up `rtimagematch.com`; if it shows uncategorized or wrong, request
**Education** and paste the description below.

## Ready-to-paste site description

> Suggested category: Education (secondary: Health & Medicine).
> RT Image Matching Trainer is an educational simulator for radiation-therapy
> students and clinical staff to practice image-guided radiation therapy (IGRT)
> setup — aligning treatment imaging (portal/CBCT) to reference data. It is a
> training tool for educational use only, with no patient data and no clinical
> decision-making. Public marketing/landing page with pricing, privacy policy,
> and terms; the interactive trainer is behind a sign-in.

## Support-email template (if a vendor stalls or for your own IT help desk)

> Subject: Web-category review request — rtimagematch.com (Education)
>
> Hello,
>
> I'm the owner of rtimagematch.com. It is a free educational simulator for
> radiation-therapy students and clinical staff to practice image-guided
> radiation therapy (IGRT) image matching. It contains no patient data and is for
> educational use only.
>
> The domain currently appears uncategorized in your filter and is being blocked
> on some networks. Please categorize it as **Education** (secondary: Health &
> Medicine). Domain: https://rtimagematch.com/
>
> Thank you,
> rtimagematch.com — support@rtimagematch.com

## Notes

- Many filters apply a **newly-registered-domain (NRD)** block for ~30 days; that
  ages out on its own, and the submissions above override it sooner.
- The landing page carries `EducationalApplication` / `EducationalAudience`
  schema plus `classification` / `category` / `rating` meta tags to reinforce the
  Education classification for automated categorizers and human reviewers.
</content>
</invoke>
