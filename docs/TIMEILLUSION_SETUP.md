# Time Illusion hosting setup

Confirmed by the owner on 14 September 2026:

- Frontend URL and Cognito callback/logout URL: `https://timeillusion.com/grantthread/`
- API and S3 allowed origin: `https://timeillusion.com`
- Vite base path: `/grantthread/`
- Dedicated AWS stack name: `grantthread-demo` (proposed; check account before creating).

`infra/timeillusion.parameters.json` contains the two confirmed CloudFormation parameters only. It is not a complete deployment configuration. Region, account access, available model, Cognito domain prefix and budget recipient still need account verification/configuration.

`frontend/.env.production.local` records the confirmed base and callback. After deployment, use `scripts/configure_frontend.py --outputs FILE --site-url https://timeillusion.com/grantthread/` to prepare the public stack settings. Review and copy them into that file as described in [DEPLOYMENT.md](DEPLOYMENT.md), rebuild, and run `scripts/package_cpanel.py --site-url https://timeillusion.com/grantthread/`. Keep credentials out of every `VITE_` variable. Cloud packaging now refuses an unconfigured build; `--preview` deliberately creates the separate interface-only preview ZIP.

The existing uploaded ZIP has no backend configuration. Its login page reporting an API 404 is consistent with that missing setup. Changing cPanel rewrite rules cannot supply the AWS API or login service.

The AWS CLI is installed and a temporary login succeeded, but the connected account differed from the earlier GrantThread account screenshot. The owner paused account selection on 14 September. No AWS calls, deployment or credential changes were made during the subsequent local improvement pass. Confirm the intended account before any resource operation; do not infer permission from the stale browser sign-in page.

Follow [AWS_FIRST_STEPS.md](AWS_FIRST_STEPS.md), then [DEPLOYMENT.md](DEPLOYMENT.md). Intended-account verification, resource deployment, seeding and the hosted login/data/AI verification remain pending. The known domain settings alone do not establish a working deployment.
