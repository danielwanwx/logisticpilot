# Receiving evidence: real development runs

September 12, 2026, Pacific. These are development runs on the explicitly synthetic split-receipt/pending-quality case, not held-out accuracy measurements or ERP executions.

## Outcome

The Nova candidate is stopped before held-out evaluation. Two single-investigator attempts exhausted the frozen input allowance during repeated structured-output repair. No comparison or multi-agent improvement is established. The existing application remains on its separately verified Opus 4.6 path.

| Candidate version and start | Provider requests | Input / output tokens | Estimated USD | Outcome |
| --- | ---: | ---: | ---: | --- |
| v5 single | 0 | 0 / 0 | 0 | Installed BedrockModel rejects simultaneous `region_name` and `boto_session` |
| v6 single, environment check | 0 | 0 / 0 | 0 | Isolated environment lacked AWS CRT required by the existing AWS login provider |
| v6 single, real run | 6 | 19,003 / 1,705 | 0.0206584 | Input reservation cap stopped repeated structured-output cycles |
| v6 Graph, real run | 4 | 5,773 / 762 | 0.0070568 | Specialist identity mismatch; coordinator did not run |
| v7 single, real run | 5 | 15,956 / 1,786 | 0.0184800 | Repeated invalid nullable quantity output; same stop rule reached |

Total measured provider usage: 15 requests, 40,732 input tokens, 4,253 output tokens, estimated USD 0.0461952. Zero completed model decisions across these five workflow starts. This denominator includes startup failures; it is not a task-accuracy rate. Offline rules executions and tests are separate.

The budget check reserves serialized request bytes as a conservative input upper bound before each call. Consequently it can stop before actual cumulative input reaches 32,000 tokens. No underestimation was reported. All attempts remain in private versioned run files and the same append-only v5 experiment ledger; no budget reset occurred. Raw model conversations, login data and local runtime files are excluded from Git.

## Diagnosis and bounded repairs

The installed Strands 1.53.0 constructor accepts the explicit boto session, which already pins the application profile and Oregon region. Removing the duplicate region argument fixes construction. AWS CRT 0.36.2, matching the working application's installed version, was added only to the isolated environment and documented in its setup instructions.

The first Graph run also exposed incomplete tool interfaces. The specialist was required to return an exact actor identifier without receiving that identifier. Both specialists tried SQL-like queries against a substring matcher. Version 7 discloses actor identity and the actual query semantics, including the existing `all` query; it adds no expected business answers. Final native `Agent.messages` are now captured privately, including SDK validation feedback on failures. Fourteen offline tests and Ruff lint/format checks pass for these repairs.

The v7 trace shows a separate unresolved behavior: a receiving lookup by customer-order ID returned no matching receipt, and the model did not broaden that lookup. It then supplied the string `"null"` for nullable decimal fields. The native structured-output tool returned validation errors, but repeated calls retained the invalid strings. It also proposed a scalar citation for a list-valued prerequisite; final citation validation was never reached. More permissive parsing would conceal these errors, so it is not applied.

AWS documents a limited JSON Schema surface for Nova tool definitions and requires explicit tool semantics. That guidance supports checking model/schema compatibility; it does not by itself prove the cause of this specific nullable-field failure. [AWS Nova tool definition](https://docs.aws.amazon.com/nova/latest/userguide/tool-use-definition.html)

## Next candidate boundary

Retain the stopped Nova results. The next candidate will use the already authorized Opus 4.6 model with the same business schemas, read-only source access and strict evidence checks. AWS documents Converse, tool-compatible structured output and the US inference profile for this model. This is a new model configuration, not an architectural improvement inferred from changing models. [AWS Opus 4.6 model card](https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-anthropic-claude-opus-4-6.html)

Before any Opus experiment call, freeze its model, price and per-workflow allowance separately. Anthropic's May 27, 2026 price list specifies USD 5.50 per million input tokens and USD 27.50 per million output tokens for Opus 4.6 on Bedrock Geo Cross-Region, which matches the `us.` profile. The original USD 3 cumulative experiment ceiling and ledger remain in force. These are list-price token estimates, not an account invoice. [Anthropic price list, page 5](https://www-cdn.anthropic.com/files/4zrzovbb/website/3684c2faafb97418665782cea0001f439f74b1d2.pdf)

The original 32-run held-out plan has not started. If the new candidate cannot finish its preregistered checks within the remaining allowance, report incomplete evidence and do not promote the Graph. Do not invent missing runs or label development results as held-out results.

## V8 checkpoint appendix

The two v8 development workflows in the same private run log both failed. No held-out
case was authored or run, and these results establish neither accuracy nor a
multi-agent gain. Further model calls stop for this delivery checkpoint pending a
design review. This is not a claim that the protocol's same-mechanism,
two-occurrence stop condition fired: the single and Graph workflows stopped at
different output-contract boundaries.

The single investigator made four provider requests, recorded 11,955 input and 1,120
output tokens, and incurred a USD 0.0965525 charge. It retrieved both `RCV-D2` and
`ORD-D2`, then reached native structured output. Its typed citations consistently
used paths rooted at `/fields/...`, including
`/fields/received_quantity/value`. The reader returns source records with a visible
`fields` wrapper, while its validator resolves citation paths relative to
`record.fields`; the model-visible citation schema supplies a JSON-pointer pattern
but does not define that relative root. The resulting path error is therefore a
source-representation/validator contract ambiguity, not evidence that the model
cited an unreturned record or that a business decision was correct.

The fixed Graph recorded six provider requests, 18,197 input tokens, and 1,697 output
tokens; its conservative charge is USD 0.1467510. The receiving specialist returned
`RCV-D2` after scoped reads but exhausted its three-request allocation without native
structured output, so the coordinator made zero requests. The fulfillment stage's
interrupted fifth attempt is retained as `unknown_usage:fulfillment:5`; its 1,024-token
reservation is included in the USD 0.1467510 charge and is not wholly reported provider
usage. The private trace and all failed records remain preserved outside Git.

V8's combined conservative charge is USD 0.2433035. Together with the retained Nova
development charge of USD 0.0461952, the unchanged durable ledger records USD
0.2894987 against the USD 3 ceiling. A later design review should decide how to make
the scalar source-citation pointer distinct from the typed answer quantity contract,
and how to enforce specialist native structured output within the existing budgets.
