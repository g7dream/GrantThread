# Cognito classic branding assets

`brand.png` is the 700 x 200 transparent logo for Cognito upload, scaling to 350 x 100. `brand.svg` is its editable vector source. `classic.css` contains only the supported classic branding selectors and properties. These files do not configure identity providers, registration, credentials, or OAuth behavior.

The network icon follows the exact Lucide Network geometry and 1.8 stroke weight already used by `Logo()` in `frontend/src/App.tsx`. The rounded teal mark, split wordmark weights, ink, sage and muted colours come from `frontend/src/styles.css`. The logo uses Arial for portable raster rendering; the application uses Inter. The subtitle is brand copy, not an extra authentication control. Lucide's required notice is retained in `LUCIDE-LICENSE.txt`.

PNG rendered locally from the SVG with Sharp 0.35.4. No generated imagery, external media, private account values, or user documents are included. The PNG was inspected visually; byte limits and CSS selectors/properties were checked locally. On 14 September 2026, the branding API accepted the logo, the applied CSS matched these settings, and the logo and teal button were verified visually on the hosted Cognito page.

Apply the PNG and CSS together to the intended app client's **Hosted UI (classic)** branding after reviewing its current settings. This is not a managed-login theme and makes no assumption about an enabled Google provider or self-registration. Provider and legal copy remain visible.

Reference: [AWS classic branding restrictions](https://docs.aws.amazon.com/cognito/latest/developerguide/hosted-ui-classic-branding.html), checked 14 September 2026. Cognito recommends a logo no larger than 100 KB and CSS no larger than 3 KB.
