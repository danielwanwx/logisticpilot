# ROI research collection and review record

September 13, 2026 UTC / September 12 Pacific. Documentation-only research milestone. No application code, UI unit tests, ERP writes, new tenant fixtures, supplier communications, claims, or payments were created for this research.

## Deliverables

- [Business-value research](../research/2026-09-13-distributor-agent-roi-research.md)
- [64-metric requirements catalog](../research/2026-09-13-roi-metric-catalog.md)
- [30-metric repository feasibility inventory](../research/2026-09-13-roi-data-feasibility.md)
- [Small-distributor positioning](../research/2026-09-13-small-distributor-positioning.md)
- Repository `AGENTS.md` records the user's no-new-UI-unit-tests rule, final user UI review, and small hackathon scope.

## Collection and source selection

The Research Engine ran from its canonical checkout with `--pack auto --depth deep --report-mode summary`. Its topic covered industrial parts distribution, incoming quality, fulfillment, supplier recovery, working capital, user feedback and enterprise competitors. The local run ID was `2026-09-12-industrial-parts-distributors-incoming-quality-exceptions-order-`; raw artifacts remain outside Git under `/private/tmp/logisticpilot-roi-research-20260913/`.

The engine completed with warnings. `research_summary.json` reported 225 total rows, 55 claim-eligible rows, zero supported claim buckets, 20 invalid rows and 150 discovery-only rows. `evidence_quality.json` reported 88 unique evidence/content entries and 18 duplicate clusters. These are engine row/content counts, not numbers of independent validated studies. Its 12 recorded collection requests are not a page-count or exhaustive search count. The engine loop ended at authenticated-browser recovery; no credentials were supplied and that recovery step was not pursued.

The engine's generic ranking included secondary marketing lists and did not adequately cover alternatives and risks. Its automated quality labels were not accepted as proof. Independent public web searches and direct page reads supplied the primary-source verification and filled these gaps. Search themes included cost of quality, supplier quality chargebacks, distributor holds, credit-block agents, freight invoices, supplier collaboration, ERPNext finance/quality semantics and SMB pricing. Anonymous discussion threads were used only as qualitative discovery, with promotional motives and unverified identities disclosed.

The main report uses 18 numbered sources. The SMB supplement adds four pricing references. Duplicate domains/pages are deliberate where their distinct claims matter; they are not counted as independent corroboration. Oracle, Microsoft, Celonis and SourceDay capability descriptions are not hands-on product tests. No external success percentage was adopted as LogisticPilot's own baseline or ROI.

Dow's original 2024 pilot story describes expected scale-up savings; a 2026 summary makes stronger claims without a settlement ledger available here. The report preserves that distinction. Odoo pricing was visible in the official search index, but direct extraction failed; only the qualitative existence of free-single-app and paid plans was used, with no price or integration-tier inference. Blocked, inaccessible or unattributed numerical claims were not used to manufacture a common industry benchmark.

## Independent repository assessment and adversarial review

The implementation coordinator performed read-only code/manifest inspection and authored the one-file feasibility inventory. The primary agent read that actual artifact and checked its relative links. Current input support, legacy code, possible ERP fields and populated tenant evidence are separately labeled.

The award reviewer independently challenged the business thesis and then read the three initial research files. The initial review failed on actionable metric and claim issues: returns must not mechanically recreate fulfillment obligations; negative invoices must not be deducted twice; disposal must account for prior impairment; supplier total cost must avoid counting the same product loss twice; observed case quantities must not be described as measured productivity. Those definitions were corrected. The review also prompted the SMB scope clarification and the optional supplier-rebate opportunity.

The scope intentionally does not implement the 64 metrics, a full data warehouse or a four-arm production experiment. The catalog and comparison proposals support selection of one valuable demo slice. No current performance or ROI claim is inferred from these designs.

The independent reviewer reread the corrected definitions and SMB supplement and returned PASS with no blocking corrections. That pass applies only to this research and positioning package, not feature implementation, customer ROI or demo acceptance.

## Verification boundary

Document checks cover metric ID completeness/uniqueness, numbered source references, local link existence, exact staged paths and whitespace. Financial example arithmetic is illustrative and explicitly labeled; it is not a new ERP result. No application regression or UI unit suite is warranted by this documentation milestone. Final visual and interaction review belongs to the user; actual backend connectivity and authoritative readback remain necessary for future implemented demo changes.

The pre-existing tracked change to `src/the_missing_20/agents/live_advisory.py` and unrelated untracked artifacts are excluded from the milestone. Raw research dumps, credentials, session URLs and runtime databases are not staged.
