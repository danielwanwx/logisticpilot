# `/operations` control readiness map

Scope: the current `workspace/distributor-operations.html` and
`workspace/distributor-operations.js` entry, its
`/api/v1/distributor-operations` boundary, and the current runbook/claim
boundary. This is an inventory of the controls a judge can see; it does not
select the proposed story. `Critical` and `Optional` in the last column mean
relevance to a story that uses that part of the operations surface, not a
commitment to use that story.

The page has three in-page views (`dashboard`, `agent`, `operations`). The
initial read is `GET /api/v1/distributor-operations` with no query parameters.
With an explicit current ERP source, the projection is `available: true` and
`actions_enabled: true`; a retained projection is available when durable state
exists but has `actions_enabled: false`; no case configuration returns the
disabled projection. `Retry` and the 30-second visibility polling use the same
GET. The server is a loopback local HTTP server.

The test-evidence column cites the pre-existing source and test names used for
this inventory. The focused JavaScript and Python suites were rerun today; they
are source/unit/HTTP checks and remain separate from browser acceptance.

## Control inventory

| Visible control | Handler and API | Side effect | State preconditions | Test evidence | Story |
| --- | --- | --- | --- | --- | --- |
| **Skip to operations** (`#main-content`) | Native anchor; no JS/API | Moves focus/viewport to main content | Page loaded | Markup at `workspace/distributor-operations.html:15`; no dedicated browser test | Optional |
| **LogisticPilot brand**, **Dashboard**, **Investigation**, **Operations**, and **Open Agent board** links | `data-ops-view-link` listener → `history.pushState` → `setOpsView`; no API | Changes the in-page view and optional scroll target; reloadable URL is written | Any page state; unknown view falls back to `dashboard` | `tests-js/distributor-operations.test.cjs` checks view-link markup; no end-to-end navigation assertion | Critical |
| **Retry** in the source-unavailable strip | Click → `refresh()` → `GET /api/v1/distributor-operations` | Replaces the projection and status/error presentation. In retained mode it rereads only local durable evidence; in live mode it rereads the ERP adapter | Source strip is visible; no operation write is attempted | `tests-js/distributor-operations.test.cjs` covers source-unavailable/retained labels; `tests/test_distributor_operations.py::test_get_derives_deadline_alerts_without_inventing_loss_or_starting_a_write` covers read-only GET semantics | Critical |
| **Open evidence details** (photo-panel icon) | Click → `openEvidenceDrawer` | Opens the modal, renders case/PO/freshness/quantity/photo/handoff facts, and moves focus to Close; no API | Any rendered projection, including unavailable | Markup and drawer behavior strings in `tests-js/distributor-operations.test.cjs`; no full browser assertion | Critical |
| **Close evidence details**, backdrop click, and **Escape** | `closeEvidenceDrawer` / `keydown` listener | Hides drawer/backdrop, restores the trigger focus; no API | Drawer is open | `tests-js/distributor-operations.test.cjs` checks Escape handling and dialog markup; no full browser assertion | Critical |
| **Open full operations evidence** in drawer | Click → `openFullOperationsEvidence` → `history.pushState` → `setOpsView("operations")` | Closes drawer, writes `?view=operations#ops-details`, scrolls to details; no API | Drawer open | Markup at `workspace/distributor-operations.html:242`; no dedicated routing test | Critical |
| **Focus active alert**, **Ask the read-only agent**, **Review manager gate** overview links | `.ops-overview-links a` listener → `history.pushState` → `focusOpsTarget`/`setOpsView` | Changes view and hash to `ops-alerts-panel`, `ops-chat-panel`, or `ops-evidence-panel`; no API | Overview rendered; target exists | Markup at `workspace/distributor-operations.html:120`; no dedicated browser navigation test | Critical |
| Dynamic **ERP evidence** and Airtable/Jira/Slack/Celigo source nodes in the cross-system graph | `networkNode` click → `focusOpsTarget(target)` → `setOpsView` | Reveals the Documents or Cross-system readback panel; no API | A source record/handoff group exists in the GET projection | Graph construction and source grouping covered by `tests-js/distributor-operations.test.cjs`; **actual-browser observation:** Airtable was tested from Dashboard; ERP/Jira/Slack were tested from Investigation. Each switched the visible panel while retaining the originating `?view=dashboard`/`?view=agent`; only Investigation reload was directly verified to restore Investigation and discard the visible destination | Critical |
| Dynamic **Agent board** and **Manager gate** graph nodes | Same `networkNode`/`focusOpsTarget` path | Reveals Investigation or Process evidence panel; no API | Graph is rendered | `tests-js/distributor-operations.test.cjs` checks agent/manager labels and proposal strings; no browser routing test | Critical |
| Dynamic stage **View evidence** links | Native `href="#ops-alert-N"`; no custom handler | Changes the URL hash and jumps to the alert when the target is on the current view; no API | An open alert is associated with that stage | `activeAlertStages`/flow rendering is covered by `tests-js/distributor-operations.test.cjs`; no browser assertion of cross-view behavior | Optional |
| **Resolved evidence history** summary | Native `<details>/<summary>` toggle | Expands/collapses the retained resolved-alert list; no API | Resolved alerts exist; the details element is hidden otherwise | Markup at `workspace/distributor-operations.html:207-210`; no dedicated test | Optional |
| **Ask about this operation** text input and **Ask** submit | Form submit handler → `POST /api/v1/distributor-operations/ask` with `{question}` | Read-only `DistributorOperations.ask`: reads the projection and, when configured, makes one real model call; stores/returns conversation display state, not an event or ERP/SaaS write. Retained mode still makes a paid real Bedrock call and does not query ERP/SaaS. | Non-empty trimmed question, `projection.available`, source strip hidden, not already asking; server accepts only `question` and up to 500 characters | `tests-js/distributor-operations.test.cjs` covers conversation projection, current/retained context, provider labeling and source semantics; `tests/test_distributor_operations.py::test_native_ask_packet_is_current_read_only_and_static_ui_files_are_allowed`, `::test_native_ask_maps_provider_failures_to_safe_actionable_unavailable`, and model-selection tests cover the server/model boundary. **Manual gap:** with `novalidate`, an empty field returns before the request and gives no feedback; no `/ask` call occurs and the instructional paragraph remains | Critical |
| **Dictate in English** | `voiceController.toggleDictation()` using browser SpeechRecognition; no API | Starts/stops microphone recognition and appends transcript to the question input; it never submits automatically | Browser exposes SpeechRecognition and microphone permission is granted; otherwise disabled/status says typing remains available | `tests-js/distributor-operations.test.cjs` voice tests cover append-without-send and unsupported-browser fallback | Optional |
| **Read answer** | `voiceController.readAnswer()` using SpeechSynthesis; no API | Speaks the currently rendered answer; a changed answer cancels the old utterance | SpeechSynthesis available and a non-empty answer is rendered; disabled otherwise | `tests-js/distributor-operations.test.cjs` voice test covers read/cancel state | Optional |
| **Stop reading** | `voiceController.stopReading()`; no API | Cancels SpeechSynthesis and hides the stop control | SpeechSynthesis is active | `tests-js/distributor-operations.test.cjs` voice test covers cancellation | Optional |
| **Evidence template** selector | `change` listener → `renderTemplateFields` | Chooses one server-approved event template and creates its required fields; no API until submit | Live projection, `actions_enabled !== false`, and at least one template; retained/unavailable projections clear/disable it | `tests-js/distributor-operations.test.cjs` covers five event payload shapes and template-field preservation; `src/the_missing_20/adapters/distributor_operations.py::_event_templates` defines `arrival`, `inspection`, `picked`, `carrier_pickup`, `delivery` | Critical |
| Dynamically created event fields for **arrival** | Field `input/change` → `updateEventButton`; form submit later builds the payload | Collects cartons, expected parts/carton, parts counted, item code, and lot; no API per field | Same live-action conditions; all values required and non-negative/validated on submit | `tests-js/distributor-operations.test.cjs::arrival event contains only the reviewed typed fields and is explicitly synthetic`; server `_validate_event` validates exact fields | Critical |
| Dynamically created event fields for **inspection** | Same form path | Collects lot, PASS/FAIL, SAMPLE/WHOLE_LOT, metric, measured value, report ID, and sample quantity; no API per field | Same live-action conditions; report ID and all typed fields are required; server enforces the configured quality policy | `tests-js/distributor-operations.test.cjs::inspection event requires a report reference and does not send a caller-supplied spec`; `tests/test_distributor_operations.py` quality-hold/release tests | Critical |
| Dynamically created event fields for **picked** | Same form path | Collects customer order, lot, quantity, and pick evidence ID; no API per field | Same live-action conditions; positive quantity and exact order/lot checks occur in server advancement | `tests-js/distributor-operations.test.cjs` payload tests; `tests/test_distributor_operations.py` picked/dispatch and quantity-conservation tests | Critical |
| Dynamically created **carrier pickup** and **delivery** fields | Same form path | Collects shipment ID; pickup and delivery remain separate typed events | Same live-action conditions; each event requires shipment evidence | `tests-js/distributor-operations.test.cjs::delivery is a separate event from pickup and both require shipment evidence`; `tests/test_distributor_operations.py` delivery/dispatch tests | Critical |
| **Evidence ID** input | Read by `buildEventPayload` during event-form submit | Becomes `event.evidence_ref`; no API per keystroke | Selected template and non-empty ID; server validates it | `tests-js/distributor-operations.test.cjs` arrival/inspection payload tests; adapter `_validate_event` | Critical |
| Optional **same-case photo** file input and preview | `change` listener validates MIME/size and creates a local object URL; form submit calls `uploadSelectedPhoto` → `POST /api/v1/distributor-operations/photo` with base64 image, then `POST .../prepare-proposal` with `photo_attachment_id` | First POST durably stores an operator-attached JPEG/PNG (≤5 MB), marked `NOT_ANALYZED`; it does not count, identify, inspect, or infer stock. Preview is local. | Live projection with actions enabled; JPEG/PNG, 1 byte–5 MB; attachment must match configured case and be unbound when attached to a proposal | `tests/test_distributor_operations.py::test_proposal_rejects_stale_case_and_manual_photo_stays_unanalyzed`; `tests-js/distributor-operations.test.cjs` checks manual-photo language and payload boundaries. The rendered image later reads `GET .../photo?id=...` | Optional |
| **Prepare for approval** | Event-form submit → `POST /api/v1/distributor-operations/prepare-proposal` | Validates and durably stores a non-mutating proposal bound to case ID and a source revision; binds the optional photo. It does not call native ERP operations | Live source (`CURRENT`), actions enabled, source strip hidden, selected template, valid exact event fields, matching case, and current ERP source available | `tests/test_distributor_operations.py::test_same_case_proposal_is_non_mutating_then_manager_approval_applies_once`; stale/photo test; JS event-payload tests | Critical |
| **Manager identity** input | `input` listener → rerenders approval button/summary; no API per keystroke | Supplies the explicit `manager_id` sent on approval | A prepared proposal is visible; non-empty text is required for an enabled button | Approval evidence assertions in `tests/test_distributor_operations.py`; no browser input test | Critical |
| **Approve and execute** (live) / **Confirm recorded completion** (retained) | Click → `POST /api/v1/distributor-operations/approve-proposal` with proposal ID, case ID, state revision, manager ID | Live: rechecks exact revision, calls `record_event`, and may create native ERP receipt/pick/dispatch/shipment effects; optional handoff sync runs only after the operation result. Retained: recovers/records a durable completed result and does not query ERP or execute a new native operation. Replays return the durable result. | Prepared proposal for same case, `PENDING_MANAGER_APPROVAL`, available projection, source strip hidden, manager ID. Live also needs current ERP and matching revision; retained success requires a recorded event/proposal result that can be confirmed. | `tests/test_distributor_operations.py` proposal, retained-confirmation, stale, replay, unknown-outcome and model tests; `tests/test_distributor_handoff_server.py::test_sync_safety_flag_keeps_retained_handoffs_visible_after_approval`; JS approval-readback tests | Critical |
| Dynamic **Review pending allocation** / **Reviewing pending allocation…** button | `reviewPendingAllocation()` → `POST /api/v1/distributor-operations/reselect-pending-allocation` with a browser-generated `retry_id` and the pending decision event ID, then silent GET refresh | Durably records one retry before selector/ERP work; rereads current source, recomputes the contract plan, and may issue one native `prepare_pick`. It never replays the physical event and does not itself dispatch. Same retry ID returns the saved result; feedback distinguishes APPLIED, BLOCKED, PENDING, UNKNOWN_OUTCOME, and UNAVAILABLE. | Live source, actions enabled, source strip hidden, visible v1 contract plan in `PENDING` state, pending decision has an event ID, and no matching retry is in flight | `tests-js/distributor-operations.test.cjs` pending-allocation eligibility/action/outcome tests; `tests/test_distributor_operations.py::test_pending_contract_reselection_uses_only_executable_b2_reference_and_replays` and blocked variant | Critical |
| Dynamic attached-photo **Expand attached photo / Collapse attached photo** button | `ops-photo-open` click toggles the card class/aria label; the image itself loads `GET /api/v1/distributor-operations/photo?id=<attachment_id>` | Expands/collapses the already stored image; GET is a case-scoped read and does not write or analyze | A projection contains a same-case attachment; missing ID returns not found | `tests/test_distributor_operations.py::test_proposal_rejects_stale_case_and_manual_photo_stays_unanalyzed` verifies stored/readable bytes; **manual observation:** retained 8930 Dashboard expand/collapse works | Optional |
| Dynamic **Verified evidence / Latest attempt evidence / Last verified evidence** handoff links | Native external anchors generated by `renderHandoffs`; no app API | Opens a safe retained provider URL in a new tab; no provider refresh | Handoff record has an `http(s)` or same-origin safe URL; external system may require its own login | `tests-js/distributor-operations.test.cjs` handoff grouping/safe-URL tests; `tests/test_distributor_handoff_server.py` GET/Ask retention and provider-failure tests | Optional |
| Dynamic ERP **Open record** links and financial order/invoice record links | Native safe anchors generated by `renderDocuments`/`renderFinancials`; no app API | Opens the source ERP record in a new tab; no write | Projection contains a safe URL; ERP access may require private credentials | `tests-js/distributor-operations.test.cjs` financial/document and safe-render assertions; `tests/test_distributor_operations.py` financial projection tests | Optional |
| Dynamic alert **Evidence** links | Native external/same-origin anchor only when the evidence value passes `safeHref`; otherwise text | Opens a supplied evidence URL; no API | Alert supplies an `http(s)`, `/...`, or `#...` value | `tests-js/distributor-operations.test.cjs` safe-URL test and alert-stage tests | Optional |
| Render-only **Source facts**, **Source activity**, **Agent evidence tools**, quantities, lots, allocations, alerts, benchmark, commercial evidence, and readback panels | No control handler; all are re-rendered from GET or the response projection. The four tool badges (`read_control_context`, `read_erp_evidence`, `read_collaboration_evidence`, `manager_gate`) are capability labels, explicitly not an executed tool trace | No side effect; they expose source-backed state, handoffs, and statuses. `Ask` is the only control that invokes the read-only agent | A projection is available for data; unavailable/retained states are rendered as such | JS projection/financial/handoff tests; server packet/current-vs-retained tests in `tests/test_distributor_operations.py`; no test count is treated as UI acceptance | Critical |

The server also exposes `POST .../events` and `POST .../reconcile-receive`, but
the current `/operations` controls do not call either route directly. Native
event execution is reached through approval; receive reconciliation remains an
API-only recovery route in this UI. `GET .../photo?id=...` is the only image
read route used by the current page.

## Access readiness for a judge

The current claim manifest says the visible PO20 page is a retained-evidence
review, not a continuously refreshed cross-app dashboard, and that no public
video URL or free judge-access route has been verified. The clean clone has no
case config or local records, so it can render only the disabled shell. These
are access blockers, not missing UI controls.

### Retained mode (`MISSING20_DISTRIBUTOR_RETAINED_PROJECTION=1`)

Required for a truthful retained review:

1. The existing private case JSON matching the intended purchase order,
   customer orders, lots, warehouses, and contracts. It is outside Git.
2. The matching private local runtime journal, including
   `distributor-operations.sqlite3`. The runbook says to use SQLite's backup
   API for an inspection copy so an active WAL is included; copying only the
   database file is insufficient.
3. Real AWS/Bedrock credentials and model permission for **Ask**. Retained
   mode does not query ERP or SaaS, but a question still makes a paid real
   Bedrock call. The runbook selects `opus46` explicitly; there is no scripted
   fallback answer.
4. An optional private handoff destination map plus matching retained handoff
   journal if Airtable/Jira/Slack-via-Celigo cards are part of the review. Keep
   `MISSING20_DISTRIBUTOR_HANDOFF_SYNC=0`; the cards are historical readback,
   not fresh provider calls.

With no retained journal, the page must show unavailable evidence. A retained
projection disables event templates, photo upload, proposal preparation, and
new native operations. An existing durable completed proposal can be confirmed
through the manager gate without a fresh native execution; a pending proposal
with no recorded event result is not a way around the read-only boundary.

### Live mode (`MISSING20_DISTRIBUTOR_RETAINED_PROJECTION=0`)

In addition to the private case JSON and matching runtime journal, live mode
requires:

- ERPNext demo credentials and access to the private records named by the case
  config. The adapter must return `CURRENT` for the exact case/PO scope.
- The configured AWS profile chain (`missing20-sandbox` via
  `missing20-login` in the runbook), valid credentials, Bedrock model access,
  model permission, and paid inference. `MISSING20_NATIVE_RECEIVING_DIALOGUE=1`
  is required for the configured native read-only conversation and native
  allocation selector; `MISSING20_DISTRIBUTOR_MODEL=opus46` selects the
  intended model.
- Connected SaaS configuration/auth only where the proposed story claims fresh
  handoff reads or writes: Airtable token/base/table, Celigo endpoint/token and
  IDs, Jira project/cloud or legacy credentials, and Slack/Celigo destination
  settings. Missing provider access leaves a retained failure/unavailable
  handoff; it does not prove the ERP operation failed.

Live event/proposal/approval controls can create real demo-tenant ERP effects.
The runbook's read-only audit boundary is to use only projection GET and Ask;
do not invoke event/proposal/approval endpoints during that audit.

## Smallest local access routes without deployment

- **Retained judge review:** run the exact command in
  [`docs/runbooks/current-operations.md`](../runbooks/current-operations.md)
  with the existing private case path supplied as
  `--distributor-operations-config` and the matching private runtime supplied
  as `--runtime-directory`, retaining the documented Bedrock/model flags and
  opening `http://127.0.0.1:8930/operations?view=dashboard`. Add
  `--distributor-handoff-config` only when the retained handoff cards are
  needed. This is a local loopback route and needs no deployment.
- **Live verification:** use the same local command and private paths with
  `MISSING20_DISTRIBUTOR_RETAINED_PROJECTION=0`, after validating ERP and
  Bedrock access. For a read-only judge walkthrough, stop at GET and Ask; the
  event controls are effect-bearing.
- **Shell-only fallback:** start the server without the private case config.
  `/operations` remains reachable, but `GET /api/v1/distributor-operations`
  returns the disabled projection. It is useful for inspecting layout only and
  cannot substantiate the case, model, ERP, or cross-system claims.

## P0/P1 gaps

**P0**

- There is no verified public/free judge route. A clean clone lacks the
  private case config and runtime journal; live claims additionally require
  private ERP records/credentials, Bedrock authentication/model permission and
  paid inference, and any claimed SaaS auth/config. Until an authorized host
  supplies those dependencies, a judge cannot independently reproduce the
  current case from the repository.
- Any story claiming a new ERP or cross-SaaS effect needs a live run with the
  exact case scope and credentials. Retained evidence is not a substitute for
  fresh external execution/readback.

**P1**

- Dynamic ERP/Airtable overview source nodes focus the visible panel without
  `pushState`; the Airtable check from Dashboard and the ERP/Jira/Slack checks
  from Investigation retained the originating `?view=dashboard`/`?view=agent`.
  Only Investigation reload was directly verified to return to Investigation
  and discard the visible destination. This is a navigation/deep-link state
  gap in the `networkNode`/`focusOpsTarget` path observed on retained 8930.
- Empty Ask input is silently ignored: the form is `novalidate`, the submit
  handler returns before `POST /ask`, and no validation/status feedback is
  shown. The instructional answer paragraph remains.
- Existing checks are focused helper, projection, adapter, and HTTP-boundary
  checks; they do not constitute browser acceptance of every listed control.
  The dynamic graph navigation and empty-Ask behavior above remain manually
  observed gaps.

## Actual-browser spot checks (retained 8930)

These observations are separate from the code/unit-only evidence in the table:

- Photo expand/collapse works for an attached photo.
- The Manager gate graph button scrolls the completion panel into view (about
  256 px from the top) and does not mutate state.
- Open evidence details opens the dialog and focuses Close; Open full operations
  evidence closes it and correctly updates the URL to
  `?view=operations#ops-details`.
- Airtable was checked from Dashboard; ERP/Jira/Slack were checked from
  Investigation. Each retained its originating URL; only the Investigation
  reload was directly verified to restore the originating view. This graph
  source behavior and empty-Ask behavior are the reproduced P1 gaps listed
  above.
