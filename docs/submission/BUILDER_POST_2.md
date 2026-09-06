# Agents for Humans: Scoped Strands tools and explicit report sharing

Draft for AWS Builder Center. Not published. Local implementation evidence is recorded below; add a genuine AWS run trace before publishing this as a completed cloud-agent story.

The most useful architectural boundary in GrantThread is between a proposal and a confirmed fact. A model may identify a likely document match or suggest a useful report draft. That does not give it permission to alter an allocation or disclose an original invoice.

The deployment design serves a static React interface from cPanel and uses AWS for the application. Cognito establishes identity; the API resolves organisation membership on the server. DynamoDB stores scoped records, S3 holds private source files and SQS carries asynchronous job identifiers. A Strands worker uses Bedrock and a small set of domain tools. The local development path shares the Python domain layer with SQLite persistence.

The implemented agent tools have narrow responsibilities: list confirmed requirements, read an authorised evidence version, calculate allocations exactly, check readiness, suggest links, save review items and assemble supported report drafts. There is no email, payment, arbitrary SQL or unrestricted web tool. The worker derives actor scope from its saved job rather than trusting an organisation argument supplied by a model.

Integer minor units handle the financial values. A version accompanies the input facts. When an authorised reviewer applies a proposal, the deterministic endpoint must check that those facts are still current. A stale suggestion should be recomputed rather than applied to new data without review.

Report sharing is another explicit action. The grantee previews the recipient, version and selected attachments. The recipient reads that package through a scoped projection, including file downloads. A report's existence must never become permission to fetch unrelated evidence by changing an ID.

The source drawer makes a more modest promise than “the AI is right.” It shows the source version and page behind a proposal. The reviewer still needs to decide whether the evidence supports the interpretation.

The P0 workflow baseline passed 28 backend/worker tests. Among them were altered-tenant requests, stale/concurrent approval, exact evidence-link scope, replacement lineage, immutable snapshot downloads, duplicate worker delivery, expired-lease fencing and timeout preservation of confirmed data. The Strands 1.54.0 dispatch tests use controlled model inputs, so they exercise the SDK/tool boundary without proving Bedrock access. Python checks, CloudFormation lint and the frontend build also passed. A later deterministic response-calculator addition brings the current suite to 39 tests without adding another agent tool; see `docs/EVALUATION.md`.

The browser completed report sharing and a source-linked clarification through local server-authenticated identities. The package contained the two explicitly selected originals. Both PDF layouts were rendered and visually inspected. This is useful integration evidence for the local workflow; the Cognito, API Gateway, SQS and Bedrock path still needs an actual deployed run.

**Evidence to add before publication:** exported architecture diagram, verified model/region, genuine AWS job duration and tool results, cloud permission checks and the actual release URL. No deployed stack or successful Bedrock run is claimed. The prepared ZIP still needs AWS configuration and rebuilding.
