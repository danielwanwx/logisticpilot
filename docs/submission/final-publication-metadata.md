# Final publication metadata — LogisticPilot TAKE05

Status: **independent film/claims review PASS for the resynchronized export; public upload and judging-access checks remain open.**
This file is the copy source for the public video and Devpost entry. It describes
TAKE05 only; earlier PO20, PO25, and PO26 cases are historical evidence.

## Publication asset

- Candidate video:
  `/Users/danielwan/Documents/LogisticPilot-media/logisticpilot-devpost-final-v1.mp4`
- Expected format: H.264, 1920 × 1080, 30 fps, AAC audio, under five minutes.
- Verified current export: SHA256
  `10aa5fddadf56c411b7bff8fcdba0d8eaf99aa7edcc739efe503053b3f53ea81`; 284.501 seconds
  (4:44.501); H.264, 1920 × 1080, 30 fps; AAC stereo; full-stream decode passed.
  Narration is resynchronized by semantic scene rather than a global 1.29× speed-up.
- Independent Astra film/claims review: **PASS** for this resynchronized export. The
  review confirmed semantic alignment at q2 (120s), q3 (140s), and Jira (216.1s), and
  retained the earlier clean ERPNext, Airtable, Slack, end-card, privacy, crop, and
  badge checks. Full decode passed; the known off-camera confirmation-click limitation
  remains disclosed.
- Current film facts and review boundary:
  [TAKE05-FINAL.md](video-v2/TAKE05-FINAL.md) and the
  [current claim manifest](current-claim-manifest.md).

## YouTube metadata

### Title

**LogisticPilot — A Receiving-Decision Agent for Small Distributors**

### Description

LogisticPilot helps a small distributor decide what can safely move when one
receiving lot is uncertain. In this synthetic POC, case
`M20-DIST-ECONOMIC-TAKE05-20260914` connects purchase order
`PUR-ORD-2026-00031` to sales order `SAL-ORD-2026-00025`.

The operator selects a receiving photo through Chrome. Amazon Nova Pro analyzes only
visible evidence; it does not count hidden contents, measure dimensions, clear
quality, or identify the lot. A Strands agent using direct Amazon Bedrock Claude Opus
4.6 advises on the evidence and contract context. Deterministic application code owns
quantity checks, gates, execution, and readback.

The live POC starts with 25 received units: 20 eligible in LOT-A20 and 5 held in
LOT-B5 for inspection. A human manager approval gates the 20-unit operation. The edit
shows the manager-ready state and a truthful runtime/readback confirmation cue; the
click itself is off-camera. The resulting records show 20 dispatched, 5 held, 0
missing, and 0 delivery-confirmed: ERPNext Delivery Note `MAT-DN-2026-00029`, Pick
List `STO-PICK-2026-00027`, Shipment `SHIPMENT-00027`; Airtable
`recvLP8rGtUddx875`; Jira `QRC-10`; and Slack via Celigo `1789421153.659629`.

The business point is to avoid holding a whole order for one uncertain lot and to
reduce duplicate entry and reconciliation. The $24.80 postage difference is a
conditional scenario estimate, not realized savings. The POC uses synthetic business
records in live connected systems; it makes no claim of physical shipment, completed
delivery, earned revenue, or measured savings.

Source code and current documentation:
https://github.com/danielwanwx/logisticpilot

### Tags

`LogisticPilot`, `AI agents`, `receiving operations`, `small distributors`,
`warehouse operations`, `Strands Agents SDK`, `Amazon Bedrock`, `Amazon Nova
Pro`, `Claude Opus 4.6`, `ERPNext`, `Airtable`, `Jira`, `Slack`,
`Celigo`, `human in the loop`, `supply chain`

## Devpost field map

| Devpost field | Value or action |
| --- | --- |
| Project name | `LogisticPilot` |
| Tagline | `A receiving-decision agent that keeps eligible stock moving.` |
| Track | `Professional Agents` — verify the selected track in the live form before submission. |
| Project description | Paste the YouTube description above, or use its first three paragraphs for a shorter field. Preserve the claim boundary in the final paragraph. |
| Repository | `https://github.com/danielwanwx/logisticpilot` |
| Video | Upload the independently reviewed TAKE05 file, then paste the verified public video URL. |
| Live demo | Leave blank unless a stable, freely accessible demo is independently verified for the full judging period. |
| AWS Builder ID | Enter it only in Devpost. Do not add an account email or Builder ID to the repository. |
| Testing instructions | Paste the instructions below. |
| Built with | Select the tags below. |

## Testing instructions

Run the repository quality gate from a clean checkout:

```bash
git clone https://github.com/danielwanwx/logisticpilot.git
cd logisticpilot
make bootstrap
make check
```

The captured TAKE05 operation uses a private demo tenant, authorized Bedrock access,
and a matching runtime journal. Those records are intentionally not in the clone, so
the commands above do not replay a live ERP operation. For the reviewable public
evidence boundary, read the README, the
[current claim manifest](current-claim-manifest.md), and
[TAKE05 final-video brief](video-v2/TAKE05-FINAL.md).

## Built with

- Strands Agents SDK
- Amazon Bedrock
- Amazon Nova Pro
- Claude Opus 4.6
- Python
- SQLite
- Server-Sent Events
- ERPNext / Frappe Cloud
- Airtable
- Jira
- Slack
- Celigo

## Final submission checklist

### Video

- [x] Verify the current resynchronized MP4: SHA256
  `10aa5fddadf56c411b7bff8fcdba0d8eaf99aa7edcc739efe503053b3f53ea81`; 284.501 seconds;
  H.264, 1920 × 1080, 30 fps; AAC stereo; and full-stream decode passed. This records
  stream metadata and decode, without claiming an audio-listening review.
- [x] Obtain and record an independent film/claims review of the resynchronized
  export, including semantic A/V sync. Astra review passed q2 at 120s, q3 at 140s,
  and Jira at 216.1s; prior ERPNext/Airtable/Slack, end-card, privacy, crop, and
  badge checks remained clean, and the off-camera confirmation-click limitation is
  recorded.
- [x] Verify the visible story uses only TAKE05:
  `M20-DIST-ECONOMIC-TAKE05-20260914` / `PUR-ORD-2026-00031` /
  `SAL-ORD-2026-00025`.
- [x] Verify the film shows the manager-ready state and readback cue without
  suggesting the off-camera confirmation click is visible.
- [x] Verify the photo language stays limited to actual Chrome selection and Nova
  Pro's visible-evidence analysis.
- [x] Verify “20 dispatched, 5 held, 0 missing, 0 delivery-confirmed” and all listed
  native and cross-app identifiers are readable and consistent.
- [x] Verify the impact copy makes no physical-shipment, delivery, revenue, realized
  savings, or invented ROI claim.
- [ ] Upload the reviewed video as public under the competition's access rules, and
  verify public playback while signed out.

### Devpost and repository

- [ ] Paste the current project description, repository URL, tags, and testing
  instructions into Devpost.
- [ ] Confirm the final title and selected competition track in the live form.
- [ ] Add the verified public video URL.
- [ ] Select every Built with tag above, including Amazon Nova Pro.
- [ ] Confirm that README, claim-manifest, TAKE05 brief, repository URL, and video
  URL open from a signed-out browser.
- [ ] Use Devpost preview to check English copy, links, video embed, and attachments.
- [ ] Complete entrant attestations and submit only after the current independent
  review and final preview pass.
