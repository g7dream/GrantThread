# 0.1.0 — local P0 candidate

Implemented the synthetic grantee → evidence → human decision → two report formats → controlled funder package → clarification workflow. The public interface is prepared for a dedicated cPanel path, with an AWS SAM application and genuine Strands integration awaiting account/model configuration.

Verified locally: 39 targeted checks (17 workflow gates, 11 worker tests and 11 response-estimate tests); TypeScript/Vite build; Python compilation and dependency consistency; CloudFormation lint; complete browser workflow including a saved PDF; two rendered report layouts; narrow-screen overflow fix; three isolated service-layer benchmark journeys. See docs/EVALUATION.md for the exact scope and remaining gates.

Added a read-only Response estimates calculator using fixed simulated funder histories. It is separate from the seven Strands tools and makes no model calls or database changes. Its tests cover date arithmetic, sparse/missing histories, conditional remaining waits and access scope. Verified browser examples show Northstar's seven-day wait as 5–15 more days (median 11), clear the old result when changing grants or dates, and show Riverbend's default as 11–23 more days (median 18). Sparse/longest-history states withhold a countdown. Desktop, 390px layout and native keyboard interactions were checked. These are fictional scenario ranges, not measured predictions or guaranteed funder deadlines.

Important changes found through testing included atomic batch review, immutable document replacement lineage, stale report/proposal handling, scoped signed downloads, safe failed-upload recovery, a required Cognito access scope, and isolated mobile table scrolling.

Not yet released publicly. Cloud integration, real Bedrock execution, live judge access, public GitHub push, final video and competition publication are outstanding. No real-world user-validation or time-savings claims are made.
