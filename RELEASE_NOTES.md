# 14 September 2026 — public editable demo update

Implemented public email/password signup, explicit personal-demo creation, grantee/funder role switching and version-checked Restore. Each new visitor receives a private fictional Bright Path copy with three grants and its Northstar view. Existing invited memberships retain their original scope. Restore rejects active jobs and stale versions, replaces scenario IDs, preserves sign-in and agent allowance history, and leaves other visitors unchanged. It is not permanent S3 deletion. Google federation is not configured; Gmail can be used as an ordinary email address.

**280 local tests pass** (190 backend, 52 scripts, 38 frontend API/auth), plus the production build. AWS reached `UPDATE_COMPLETE`; signup, health and role-header CORS settings are verified. All 16 hosted encoding/cache checks pass and the browser loads `index-C8T0tDcQ.js`. The new flow passes **18 actual browser checks**, including OAuth, copy creation, venue correction, report sharing, selected-source download, both roles, a resolved conversation and Restore with login/history retained after reload. **55 separate administrative cloud checks** pass for isolation and restoration boundaries. Accounts were confirmed administratively; real signup email delivery and code confirmation remain unverified. See [PUBLIC_DEMO.md](docs/PUBLIC_DEMO.md).

The browser-triggered review stopped at its budget after eight recorded tools: six succeeded and two already-confirmed evidence proposals were safely rejected; it created no report or proposal. A separate cloud review failed under model throttling after four successful tools. These are bounded outcomes, not successful automatic report completion. Exact counter semantics and earlier distinct runs are in [EVALUATION.md](docs/EVALUATION.md).

The earlier 244-test release and 49 administrative cloud checks below describe the invited-account workflow before this update. They do not establish the new signup or per-visitor restoration behavior.

# 14 September 2026 — earlier invited-account release

The regional `grantthread-demo` stack and separate USD 25 budget stack reached CREATE_COMPLETE. Those local suites passed **244 tests** (169 backend, 50 scripts, 25 frontend API), plus the production frontend build. **49 cloud application checks** passed using administrative Lambda invocation with trusted gateway claims, not public JWT/OAuth/CORS/browser testing.

A genuine regional Nova Lite Strands reconciliation made four model calls and eight successful tool calls in 8.59 seconds, saved an incomplete report and correctly reached `waiting_input` for missing printing proof and human allocation review. Real Lambda/S3 financial checks covered XLSX/text-bank-PDF imports, receipt conversion, payment matching, CAD 25→20 correction and XLSX/PDF exports. Genuine model-based bank extraction is not verified.

The final raw/gzip/Brotli checks match the configured build and the canonical browser loads the current bundle. Cognito returns to the app, and stale-cache validators now receive fresh 200 responses for the app index/manifest. Both CORS repairs are deployed; actual grantee login/reload, financial figures and XLSX download/readback now pass. A fresh portfolio-wide job used nine model calls/eight tool calls (seven successes and one evidence rejection), stopped at its budget and saved no draft. Hosted Youth Skills sharing with one selected source, recipient sign-in and a source-linked question/answer also pass. Hosted receipt-PDF values, selected source download and resolved funder clarification also pass. Repeated demonstrations and video remain pending. Source revision 3b4ceba is published at the public g7dream/GrantThread repository; README and MIT licence were independently verified. Submission has not occurred. User validation and time savings remain unmeasured. See [EVALUATION.md](docs/EVALUATION.md).

The earlier baseline below is historical, not current release status.

# 6 September 2026 — 0.1.0 local P0 baseline

Implemented the synthetic grantee → evidence → human decision → two report formats → controlled funder package → clarification workflow. The public interface is prepared for a dedicated cPanel path, with an AWS SAM application and genuine Strands integration awaiting account/model configuration.

Verified locally: 39 targeted checks (17 workflow gates, 11 worker tests and 11 response-estimate tests); TypeScript/Vite build; Python compilation and dependency consistency; CloudFormation lint; complete browser workflow including a saved PDF; two rendered report layouts; narrow-screen overflow fix; three isolated service-layer benchmark journeys. See docs/EVALUATION.md for the exact scope and remaining gates.

Added a read-only Response estimates calculator using fixed simulated funder histories. It is separate from the seven Strands tools and makes no model calls or database changes. Its tests cover date arithmetic, sparse/missing histories, conditional remaining waits and access scope. Verified browser examples show Northstar's seven-day wait as 5–15 more days (median 11), clear the old result when changing grants or dates, and show Riverbend's default as 11–23 more days (median 18). Sparse/longest-history states withhold a countdown. Desktop, 390px layout and native keyboard interactions were checked. These are fictional scenario ranges, not measured predictions or guaranteed funder deadlines.

Important changes found through testing included atomic batch review, immutable document replacement lineage, stale report/proposal handling, scoped signed downloads, safe failed-upload recovery, a required Cognito access scope, and isolated mobile table scrolling.

At this 6 September baseline, cloud integration, real Bedrock execution, live judge access, public GitHub push, video and submission were outstanding. The 14 September record above supersedes that status. No real-world user-validation or time-savings claims are made.
