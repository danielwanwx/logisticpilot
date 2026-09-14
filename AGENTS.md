# Project delivery requirements

## Minimal product copy — explicit user requirement

- Default views show functional titles, essential business values/statuses,
  labeled inputs and actions. Remove nonessential explanatory small print,
  repeated eyebrows, instructions, disclaimers about implementation, and
  descriptions of what a module does.
- Explain a module, case, part or decision only after the user explicitly
  opens its details. Do not turn a single expanded section into a report of
  every supporting explanation; use focused business details.
- Backend plumbing (model identifiers, tokens, source revisions, transport,
  internal case hashes and implementation narratives) does not belong in
  customer-facing default views. Keep diagnostics in backend/audit records.
- Preserve meaningful values, honest concise estimate/conditional labels,
  actionable errors, explicit requested agent answers, and the order/lot/
  quantity needed to approve an action. Do not hide these with blanket CSS.
- Keep the approved visual composition and live backend behavior unchanged
  when simplifying copy. The user owns final visual review; no UI unit tests.
- Slow initial reads must show a clear loading layout, not a blank workspace.
  Bound read requests and expose a concise retry state on failure. Never fill
  loading cards with invented case quantities or enable actions before data loads.

## Approved visual direction — do not replace (September 13 user correction)

- Preserve Claude's approved dashboard composition in
  `docs/design/approved-dashboard/dashboard-look-1.jpg` and
  `docs/design/approved-dashboard/dashboard-look-2.jpg`.
  The layout is journey and a compact KPI strip beside recent events, then a
  large receiving photo beside a deep-green impact card, followed by a visible,
  always-expanded benchmark section. Preserve the three existing workspace views.
- Benchmark history is explicitly authorized to use consistent synthetic weekly
  records and trend charts, with a concise visible `Demo history` label. Keep
  these separate from current-order metrics read from the real backend; do not
  imply the illustrative trend proves measured agent savings or improvements.
- Feature work must fit that composition. Do not turn the product into an audit
  report, add walls of explanation, introduce nested outlined cards, or remove
  benchmark access. Keep generous spacing and concise product language.
- Keep provenance, synthetic-input explanations, raw traces, source revisions,
  and detailed conditions in evidence drawers or expandable details. Do not
  repeat them across the main dashboard. The demo presenter explains the POC;
  the product presents the actual connected case state. Retain accurate source
  records and label estimates as estimates, without fabricating metrics.
- Photo analysis, order quantities, economic decisions, and actions must remain
  connected to the real backend. A visual restoration must not restore old
  hardcoded scenario data. Verify with the browser; the user owns visual approval.
- Keep workspace responsibilities distinct: Dashboard shows current status,
  journey/KPIs, photo summary, business impact and benchmarks. Investigation owns
  agent reasoning, evidence comparison, candidate decisions and follow-up Q&A.
  Operations owns photo/evidence capture, inspection, exact-action confirmation,
  execution and readback. Share one case context and route handoffs between views;
  do not duplicate complete forms, investigation panels or approval controls.

## Small-business hackathon scope and UI review (user steering, September 12)

- Focus LogisticPilot on a small parts distributor with limited operations
  staff and no dedicated supply-chain analyst. Prove one useful receiving
  exception workflow with real evidence and business outcomes; do not expand
  the entry into an enterprise suite or production-hardening program.
- Treat the broad ROI metric catalog as research and a selection aid, not an
  implementation checklist. Prefer a few visible, defensible outcomes.
- Do not add UI unit tests. The user owns final visual and interaction review.
  Verify that the selected demo flow actually calls the backend and reads back
  its business result; do not replace this with component-level test volume.
- Use narrowly scoped checks where changed business calculations, inventory
  state, approval boundaries, or actual failures warrant them. Avoid redundant
  tests, exhaustive UI edge cases, and broad repeated regression runs.
- Preserve honest labels, real integrations, and reviewed milestone commits.
  A hackathon scope does not permit fabricated execution or ROI claims.
- Synthetic POC business evidence is explicitly authorized: combine public
  reference rates or document layouts with consistent fictional orders,
  waybills, cost statements and contract terms. Label the business scenario
  and simulated savings; keep actual model calls and ERP execution real.
  Real customer paperwork is not a prerequisite for this demo. Do not mistake
  synthetic business inputs for permission to mock the agent or backend.
- The user explicitly authorizes sending business evidence from this POC's
  connected ERP and other demo systems to the existing AWS Bedrock integration
  for agent analysis and end-to-end verification. These sources are part of the
  intended connected demo ecosystem. Reuse this authorization for the same scope;
  do not repeatedly ask whether the demo ERP evidence may be sent to Bedrock.
  This does not require sending credentials or changing platform security controls.

## Competition demo priority (user steering, September 9)

- Prioritize one visible same-order business path through receiving, supplier
  billing, ERP readback and useful multi-turn explanation. Reuse accepted
  components and implement complete vertical slices.
- The user accepts minor defects and limited rare-edge recovery for the demo.
  Do not expand production reliability, framework abstractions, exhaustive
  counterexamples or full-regression reruns before every small integration.
  Keep quantities, amounts, case identity and claims about actual actions true.
- Use focused checks and one independent review for each complete demo slice;
  verify the real interface and external records. Broaden testing when a
  concrete failure warrants it. Record deferred limitations without turning
  each into a new precondition for demonstrating the business path.
- Existing commit/push verification and protection of unrelated work still apply.

## Delivery

- After each completed optimization, run the relevant verification, commit the
  completed changes, and push to the project's intended Git remote. The user has
  authorized this routine delivery step; do not ask for approval each time.
- Verify the push result. Report the commit and any push failure accurately;
  a local commit alone does not satisfy delivery.
- Stage only reviewed, task-relevant changes. Preserve unrelated work. Never
  include credentials, local runtime databases, private session data, or sensitive
  artifacts merely because they appear in the working tree.
- Do not force-push, rewrite shared history, or claim incomplete work is verified.

# Research-led agent improvements

- For a repeated agent reasoning or workflow failure, preserve the failing case
  and pause expansion of that candidate. Investigate the failure mechanism and
  current SDK capabilities before adding another prompt, validator or state layer.
- Compare a small set of materially different approaches against the same task:
  the retained baseline, a native/existing-component approach, and another
  plausible alternative when evidence supports one. Prefer official source code,
  maintained repositories and maintainer discussions. Record versions, licenses,
  integration requirements and what each component does not solve.
- Freeze inputs, expected outcomes, model/configuration, budgets and stop rules
  before a comparison. Keep expected outcomes and review rubrics outside model
  inputs. Keep memory, answer quality, workflow recovery and real ERP
  effects as separate acceptance dimensions. A historical baseline is not a fresh
  paired measurement; scripted or fake-service results are not real-model or ERP
  acceptance. Preserve every failed attempt and the held-out set.
- If a mechanism fails the agreed stop rule, return to research and choose a
  different supported approach. Do not keep layering exceptions to fit that case.
  Ordinary implementation defects still receive a bounded fix and regression;
  a new framework is not required for every bug.
- Terra Max implements coupled/core work; Luna Max implements narrow changes with
  stable interfaces. The primary agent owns hypotheses, selection, coordination,
  verification and release. Existing authorized independent review remains required.
- Run candidates in isolated experiments before changing the product. Promote
  only independently reviewed improvements with demonstrated task benefit and
  acceptable integration cost. Continue the original commit/push verification
  requirements for each accepted deliverable.
