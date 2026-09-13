# Operations navigation and empty-question acceptance

September 13, 2026 UTC. Scope: two defects reproduced in the [control inventory](2026-09-13-control-readiness-map.md), independently of the expanded business-impact design awaiting approval. Luna Max implemented the changes under the coordinator; root reviewed the actual diff and tested the running retained PO20 interface at port 8930.

## Changes

- Source, agent and manager graph nodes now update both the visible view and its URL/hash. Overview and drawer links use the same destination behavior; repeated selection of an identical destination does not add history entries. Back/forward and reload synchronize the view and target.
- Empty or whitespace-only Ask shows a polite accessible status, focuses the question and marks it invalid. It leaves existing answer content intact. Entering non-whitespace text clears this validation without submitting; a valid submission keeps the real `/ask` path.

## Evidence

The coordinator inspected the final diff and ran `node --test tests-js/distributor-operations.test.cjs`: **48 passed, 0 failed** after the last correction. Tests cover destination view/hash, preservation of unrelated query parameters, whitespace rejection with zero request callbacks, and valid trimmed input forwarding. `git diff --check` passed. These focused tests do not establish fresh model or ERP execution.

Root's actual-browser checks on the final behavior:

| Action | Observed result |
| --- | --- |
| Dashboard → Airtable | `?view=operations#ops-handoffs-panel`; visible readback; reload retained the destination; Back once restored Dashboard. |
| Investigation → ERP evidence | `?view=operations#ops-documents-panel`; reload retained the destination; Back once restored Investigation. |
| Investigation → Jira and Slack | Each opened `?view=operations#ops-handoffs-panel`; Back once restored Investigation. |
| Agent board | `?view=agent#ops-chat-panel`; Back once restored the original Investigation URL. |
| Manager gate, selected twice | `?view=agent#ops-evidence-panel`; Back once restored the original URL, demonstrating no duplicate entry for the repeated destination. No approval was submitted. |
| Whitespace Ask | Visible `Enter a question before asking.`, focus on `ops-question`, `aria-invalid=true`, status role; existing instructional content unchanged. |
| Type a nonempty question | Feedback became hidden/empty and the validation attributes cleared; no automatic submission or answer replacement was observed. |
| Empty Ask with existing provider-error content | Feedback appeared and provider-error content remained intact. [Screenshot](assets/2026-09-13-judge/ui-empty-question.png). |

One batched browser check timed out and reset its control session. Its unreturned observations were not counted; the checks listed above were subsequently observed in separate completed calls.

During the later screenshot check, an Ask request occurred after the input-clear action; the returned UI showed **model credentials unavailable or expired**, with no fallback answer. This is a failed real-question attempt, not successful model acceptance. Subsequent explicit empty-input verification confirmed the validation behavior. The browser tool's earlier fill/observation sequence was insufficient to establish an empty field before that click; the final check read the empty field first. Restoring AWS credentials is required before a successful fresh-model acceptance claim. No new ERP or SaaS operation was performed by this UI audit.

The page was returned to Dashboard. Broader business-impact investigation, trend queries, new-case execution, efficiency comparisons and free judge access remain incomplete; this milestone fixes only the two existing interaction defects.

## Subsequent authentication recovery

Later on September 13 UTC, a direct AWS CLI identity request confirmed the source login had expired. A fresh same-device login reused the existing project IAM-user browser session and the CLI exited successfully. The configured-account identity preflight then passed. No browser security setting was changed; the browser callback error page was not treated as the authority for CLI completion.

One real Ask through the existing running application then succeeded with the displayed provider `bedrock · us.anthropic.claude-opus-4-6-v1`. It returned: “All 40 Nos have been dispatched (25 Nos for SAL-ORD-2026-00015 and 15 Nos for SAL-ORD-2026-00016), per retained evidence bounded by RETAINED_AS_OF 2026-09-11T05:51:50 UTC (live ERP was not queried).” This closes the credential-recovery check only. It does not establish new ERP execution, fresh source data, or the proposed agent-value improvement. Authentication URLs and credentials are not retained in the repository.
