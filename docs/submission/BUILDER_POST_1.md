# Agents for Humans: Keeping one clear thread across grant reports

Draft for AWS Builder Center. Not published. Add an actual screenshot and the verified release link before publication; remove this editorial line.

GrantThread starts with a simple situation: one organisation is reporting to several funders about work that overlaps. The workshop is one activity. The invoice is one expense. Each report still needs its own allocation, evidence and explanation.

Our locally verified demonstration uses fictional Bright Path Lab and three fictional grants. Five unique expenses add up to EUR 5,200. Someone proposes allocating EUR 700 of a EUR 1,000 venue expense to one grant and EUR 500 to another. That produces an exception of EUR 200. Another expense is recorded correctly but lacks the payment proof required by its configured fictional agreement.

These are different questions. The venue needs a judgement about how to split the original amount. Printing needs an additional document. Removing the printing expense from the ledger would obscure the problem, while silently accepting the venue split would change the facts.

The product workflow puts those questions in a review queue with their sources. The local checks confirmed that one authorised correction produces grant allocations of EUR 1,700, EUR 3,100 and EUR 400. These are verified synthetic financial results, not measured productivity benefits.

The deployed AWS agent has a limited job: organise evidence through scoped tools and prepare proposed work. On 14 September, a genuine regional Nova Lite Strands reconciliation made four model calls and eight successful tool calls, saved an incomplete report and correctly stopped at waiting_input for missing printing proof and allocation review. Actual hosted grantee sign-in/reload and financial XLSX readback now pass. A fresh portfolio-wide run separately reached its tool budget after nine model calls/eight tools, with one evidence rejection and no draft. Hosted sharing and a source-linked question/answer also pass. Hosted receipt-PDF values, the selected original download and funder acknowledgement are verified. Repeated judge demonstrations remain open. We chose a separation between model output and confirmed facts. The administrator decides consequential changes, and a shared report contains a deliberate snapshot.

A second useful boundary is activity counting. The same 24-person workshop can appear in two grant reports, but adding those reports does not produce 48 unique participants. GrantThread keeps the original activity identity alongside its grant links.

In the local browser, adding and approving printing proof changed the Digital Belonging report from 5 of 6 configured requirements to 6 of 6. The report downloaded as a PDF. A Northstar demo identity received one explicitly shared package and two selected original attachments; its source-linked question was answered and resolved through the two roles.

This is still a product hypothesis about reducing repeated work and making review questions clearer. We have not established customer adoption or time savings. Testing with administrators and funders is the next step after a reproducible synthetic workflow.

**Publication evidence to add:** actual portfolio/decision screenshot, verified release link, a redacted view of the recorded AWS run and an account of both distinct model outcomes and any unfinished receipt-PDF or funder checks. Link the later architecture and evaluation posts once they are public.
