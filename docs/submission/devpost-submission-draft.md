# LogisticPilot — Devpost source of truth

Recording draft updated September 14 UTC / September 13 Pacific. This replaces the older PO20 story. It is not an online submission or a claim that judge access and the final video are complete.

## Project overview

**Name:** LogisticPilot

**Tagline:** A receiving problem shouldn’t stop every order.

**One sentence:** An AI order desk for small parts distributors: investigate affected stock, keep eligible orders moving, and verify the ERP result.

**Track:** Professional Agents

**Repository:** https://github.com/danielwanwx/logisticpilot

**Current stack:** Strands Agents SDK, Amazon Bedrock Claude Opus 4.6, ERPNext/Frappe Cloud, Python, JavaScript/CSS, Pydantic and SQLite. Historical AgentCore and other SaaS integrations are documented separately.

## Project story

### Inspiration

A small distributor may not have a supply-chain analyst. When a carton looks damaged, someone must connect the photo to a batch, check inspection records, understand the customer’s order terms, decide what can move, and verify the ERP paperwork. Holding everything is simple, but it can stop perfectly usable stock from serving a customer.

We built LogisticPilot around a narrower question: **Can we investigate one questionable batch while keeping the rest of the order moving?**

### What it does

LogisticPilot connects a receiving exception to its batch, order evidence and next action. Its contextual assistant uses real Strands/Bedrock calls to explain the case, ask for missing physical evidence, analyze an attached image, or request a supported action draft. The operator confirms a specific action; application checks and native ERP readback govern the result.

The verified reference case contains 25 parts. Twenty qualified parts from LOT-A20 were dispatched through the ERPNext demo tenant, while five from LOT-B5 remained held pending inspection. The application produced a Delivery Note, Pick List and Shipment, and a separate fresh read corroborated the quantities. Those records establish demo ERP execution, not physical delivery.

A photo can supply an observation about an outer carton. It cannot establish an unseen count, a diameter measurement or quality clearance. The operator supplies the batch context and any physical inspection evidence.

### How we built it

A Python operations coordinator reads the current ERP case and supplies a bounded evidence packet to a Strands assistant running Claude Opus 4.6 on Bedrock. Structured outputs select a supported explanation, clarification, photo analysis or draft path. The current assistant is a single agent; its read tool accesses the prefetched case packet rather than independently querying every service.

Application code calculates quantities, validates physical evidence and current source revisions, binds confirmation to the exact proposal, executes supported ERP actions, and reads back the native records. The model has no approval or payment authority. The frontend keeps detailed source information on demand and makes the actual business state visible.

### Challenges

The difficult distinctions are operational: a photo observation versus an inspection, a held batch versus defective units, available stock versus already-dispatched stock, and a cost estimate versus money saved. Long source reads and changing state also exposed UI issues, including stale answers and interrupted evidence review. We tested real browser flows and retained failures in dated audits.

### Accomplishments

The current connected workflow has real model calls, real image analysis and an explicitly confirmed ERP execution. The reference result is 20 dispatched and 5 held, with independently readable native documents. That is a concrete task outcome for a small operations team.

We also evaluated earlier investigation and multi-agent approaches. Those results remain attached to their original cases. We do not claim a current multi-agent accuracy gain or present an older AgentCore deployment as this local server’s runtime.

### What we learned

An agent is useful when it reduces the work between an uncertain observation and a checked result. More roles and tools are not automatically more useful. The product needs to make the affected object, missing evidence and next decision obvious.

Microsoft and Oracle already support quality workflows, contextual assistants and impact analysis. Our contribution is a small ERPNext-focused receiving workflow, not the invention of those categories or a claim to outperform enterprise suites.

### What is next

Complete the recording and free judge-access route, then test with small distributor teams. Measure review time, manual evidence lookups, correct escalations and duplicate actions before claiming production ROI. Extend the same pattern to returns or supplier-document exceptions only after defining their sources, policies and evaluation cases.

### Demo boundaries and provenance

Business records and inspection inputs are purpose-built POC data. Public photo fixtures retain source licenses and attribution. Real model calls, application checks and ERP effects are not mocked.

The shipping comparison uses a public $24.80 Medium Flat Rate Box rate with synthetic package-fit assumptions. Two packages are estimated at $49.60; one at $24.80. Consolidation depends on future release of held stock, and the demonstrated split shipment does not establish realized savings. Demo history charts are illustrative, not customer results. Order values are not revenue or payments.

LogisticPilot was formerly The Missing 20. Git history and the provenance ledger retain that relationship and disclose earlier influences. Historical PO20 fulfillment, invoice and cross-app demonstrations remain separate from this 25-part recording case.

## Recording and testing

Use [the current claim manifest](current-claim-manifest.md), [five-minute plan](../demo/five-minute-demo.md), and [interaction review](../audits/2026-09-14-operations-interaction-review.md). The reference PO25 is already dispatched; do not portray it as a fresh approval. A continuous before/after take needs a new isolated case with consistent IDs.

The local product is `/operations`, with Dashboard and Operations views. The private runtime requires authorized Bedrock and ERP credentials and matching case configuration. The browser chooser/upload still needs recording preflight; the existing image pipeline proof used API attachment.

A public YouTube/Vimeo video, free judge-access route, final architecture asset and entrant certifications must be checked before final submission. Localhost and a clean clone without private runtime data do not satisfy that access requirement by themselves. No online Submit action has been performed by updating this file.

## Evidence

- [Current assistant and real ERP acceptance](../audits/2026-09-13-operations-assistant-acceptance.md)
- [Independent interaction review](../audits/2026-09-14-operations-interaction-review.md)
- [Competition and competitor analysis](../research/2026-09-14-recording-readiness-and-competition.md)
- [Provenance](../provenance.md)
