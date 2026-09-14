# Operations with a contextual Agent

Approved by the user on September 13, 2026, following review of the cluttered
Operations form and the separate Investigation view.

## Outcome

An operator works on one receiving exception in Operations while an Agent reads
the connected evidence, asks for missing information, prepares a specific action,
and explains the result. The operator should not need to understand ERP event
templates or move between Investigation and Operations to complete the task.

## Navigation and layout

- Keep two destinations: Dashboard and Operations. Map legacy Investigation links
  to Operations with the Agent open.
- Preserve the approved Dashboard composition and its expanded benchmark history.
  Ask Agent opens a contextual sidebar without discarding the current case.
- Operations uses an approximately 65/35 workspace/sidebar split on desktop with
  aligned tops, generous spacing and the existing green/neutral visual language.
  The sidebar becomes a drawer on narrow screens.
- Left workspace: Receiving (photos, item, lot, quantities), Findings (exceptions
  and affected orders), Next action (recommendation, draft and execution result).
- Right sidebar: shared conversation, uploads, concise task progress, missing-data
  questions and the exact-action confirmation card.
- Manual entry remains available under Edit details. Detailed sources are opened
  from the relevant result, not printed as long default-view explanations.

## Real data and action flow

1. The operator uploads a receiving photo or asks a question about the active order.
2. The Agent uses the current ERP context and available photo evidence. Missing or
   ambiguous lot identity requires clarification. No invented measurements or
   inferred quality clearance.
3. The Agent returns a structured, allowlisted draft or a concrete clarification.
   The left workspace and conversation reflect the same case and source revision.
4. Preparation reuses the existing backend proposal mechanisms. Model output never
   directly executes an inventory or fulfillment write.
5. The operator confirms the exact proposed action in the sidebar. Existing approval
   validation and ERP readback remain authoritative for execution and completion.
6. Both views reflect the returned projection. Conversation history is case-scoped;
   switching views must not lose the task or mix records from another case.

The existing read-only ask route remains compatible. Any added assistant route
must expose actual structured model behavior rather than keyword-based demo replies.
Synthetic historical benchmarks remain separate from real current-order results.

## Failure behavior

- Unavailable ERP/model: concise actionable error, no fabricated answer or draft.
- Missing evidence: ask for the specific missing photo or measurement.
- Stale source or proposal: refresh/reprepare before confirmation; never silently
  execute a different quantity or action.
- Unknown execution result: show the unresolved state and use existing readback;
  do not represent a request being sent as completed execution.

## Acceptance

Verify the two navigation destinations, legacy links, Dashboard drawer, persistent
Operations sidebar, narrow layout and unchanged benchmark through the browser.
Exercise an actual Bedrock turn, a clarification, a structured draft, preparation,
explicit confirmation and ERP readback against the authorized demo environment.
Use focused backend checks for draft bounds and approval invariants. Do not add UI
unit tests. The user owns final visual review. Review and commit/push each coherent
implementation milestone without including unrelated working-tree changes.
