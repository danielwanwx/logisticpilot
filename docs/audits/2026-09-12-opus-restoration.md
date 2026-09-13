# Opus 4.6 access and application verification

September 12, 2026, Pacific. This follows the [Nova runtime restoration](2026-09-12-runtime-restoration.md). Opus access is now verified with the original application role, not with root credentials in the application.

## Verified access

The original `missing20-sandbox` profile, assuming `Missing20DeveloperRole` in `us-west-2`, returned real results from:

- `Converse`: 10 input / 5 output tokens; response `OK.`.
- `ConverseStream`: 10 input / 5 output tokens; response `OK.`.
- `GetInferenceProfile`: `ACTIVE` for `us.anthropic.claude-opus-4-6-v1`; destinations `us-east-1`, `us-east-2`, and `us-west-2`.

Before restoration, the role's invocation was explicitly denied for lack of an identity-policy allow. The administrator console was inspected, and a separate Opus-only inline policy was prepared at the review step. The existing permissions boundary already excluded Bedrock invocation from its regional deny and did not need modification. After the user's completion message, the console page was signed out and the three API checks above succeeded. The agent did not itself submit the policy, and the final policy document was not read back. Effective access is verified; the exact administrator change is not claimed as an agent-executed mutation. Account identifiers and private session artifacts remain outside Git.

The browser authentication problem was handled separately by starting a fresh AWS console login in the existing Chrome profile. The earlier screenshot alone did not establish a bad password. The backend CLI session remained valid during that recovery.

## Real application check

The isolated workspace at port 8930 now explicitly selects `MISSING20_DISTRIBUTOR_MODEL=opus46`, retaining the reviewed history-compaction fix. Retained mode and disabled handoff sync preserve the original business case. The application displays the actual model ID; it does not silently fall back to Nova.

The first real browser question used exactly the earlier delivery/payment question. Opus correctly distinguished synthetic delivery confirmations from independently proven customer receipt, named shipments 16–19 and PO20/customer orders, and separated order-line USD150/USD90 values from invoices or revenue. It preserved the retained timestamp `2026-09-11T05:51:50.322138+00:00`. The native session records 24,046 input / 1,035 output tokens for this answer. This request answered from the supplied source snapshot and made no additional source-tool call.

The next question asked whether a two-part shortage establishes supplier fault and whether a failed sample establishes all 18 units defective. Opus rejected both inferences and cited receipt `MAT-PRE-2026-00020`, initial inspection `MAT-QA-2026-00015`, whole-lot retest `MAT-QA-2026-00016`, and release `MAT-STE-2026-00017`. It labeled the inspection measurements as declared reports, not physical tests performed by the agent.

The third consecutive question asked for total received/dispatched quantities, customer split, source mode and date. It returned 40 Nos received and dispatched, A25/B15, `RETAINED_AS_OF` and the correct effective date. It named purchase receipts 19–21 and delivery notes 18–21. All three browser requests completed under the explicitly displayed Opus provider, using the same retained case and bounded conversation history. No operation approval or ERP write was invoked.

These checks establish connectivity and correct core conclusions on this case. They do not establish a population accuracy rate, superiority to Nova, or benefit from multi-agent orchestration. The two models were not run in identical conversation histories and question order here, so this is not the preregistered paired comparison.

## Remaining product and evaluation work

Opus's answers are substantially longer and include Markdown tables that the current answer panel displays as plain text. Answer usability still needs attention. The inspection answer also describes each sampled/retested unit as having the scalar recorded measurement; the available report is not a per-unit measurement distribution. Preserve that distinction in semantic evaluation rather than treating detailed prose or valid record IDs as proof of every statement.

The separate Graph/Evals harness has only offline development results so far. Its existing Nova freeze must not be relabeled as an Opus experiment. Any Opus candidate comparison requires a new frozen configuration and verified pricing/budget before paid runs; no multi-agent capability is promoted by this access restoration.
