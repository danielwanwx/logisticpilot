# Receiving evidence v8: Opus 4.6 candidate addendum

Prepared September 12, 2026. This addendum supersedes the stopped Nova model configuration in the [paired-evaluation protocol](2026-09-12-paired-evaluation-protocol.md) for a new development candidate. It does not revise the question, business schema, source tools, prompts, evaluator, fixed Graph, or selection criteria.

## Status and boundary

Nova Pro development stopped after two single-investigator attempts exhausted the frozen input allowance during repeated structured-output repair. The private v5–v7 run records and the append-only v5 durable ledger are retained. The development record is documented in the [receiving-evals audit](../audits/2026-09-12-receiving-evals-development.md).

Version 8 changes only the explicitly pinned model configuration to `us.anthropic.claude-opus-4-6-v1` in `us-west-2`, with profile `missing20-sandbox` and temperature `0`. Both the single investigator and every Graph node use that one model ID. There is no fallback, general routing, or automatic promotion. This configuration change is not evidence of an architectural gain.

No held-out case has been authored or run. The planned 32 held-out model workflows remain conditional on development acceptance and the remaining durable budget.

## Frozen v8 resource allowance

The v8 manifest records the model ID, region, profile, temperature, per-request output limit, and both token prices. It keeps the prior request and time limits:

| Constraint | v8 allowance |
| --- | ---: |
| Provider requests per workflow | 8 |
| Input tokens per workflow | 32,000 |
| Output tokens per workflow | 6,000 |
| Output tokens per request | 1,024 |
| Wall-clock time | 180 seconds |
| Graph stage request allocation | 3 receiving / 3 fulfillment / 2 coordinator |

The price basis is USD 0.0000055 per input token and USD 0.0000275 per output token: USD 5.50 and USD 27.50 per million tokens, respectively. At the workflow ceilings, the conservative estimate is `32,000 × 0.0000055 + 6,000 × 0.0000275 = USD 0.341`; the durable reservation is USD 0.35 per model workflow. The source is Anthropic's [May 27, 2026 price list, page 5](https://www-cdn.anthropic.com/files/4zrzovbb/website/3684c2faafb97418665782cea0001f439f74b1d2.pdf), which specifies those Bedrock Geo Cross-Region rates for Opus 4.6.

The USD 3 experiment ceiling remains unchanged. The same append-only v5 ledger carries forward USD 0.0461952 of measured Nova development cost; it is never reset for v8. Unknown provider usage remains charged to the full pre-request reservation.
