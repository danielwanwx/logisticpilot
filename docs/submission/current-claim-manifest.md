# LogisticPilot — current TAKE05 claim manifest

## Current truth source

This is the claim boundary for the current public entry: **TAKE05**, a synthetic
POC receiving decision carried through live connected systems.

| Item | Current TAKE05 fact |
| --- | --- |
| Product | LogisticPilot, a receiving-decision agent for small distributors |
| Case | `M20-DIST-ECONOMIC-TAKE05-20260914` |
| Purchase order | `PUR-ORD-2026-00031` |
| Sales order | `SAL-ORD-2026-00025` |
| Before the approved operation | 25 received; LOT-A20: 20 usable and eligible; LOT-B5: 5 held for inspection; 0 dispatched |
| Recorded live-POC result | 20 dispatched; 5 held; 0 missing; 0 delivery-confirmed |
| Native ERPNext records | Delivery Note `MAT-DN-2026-00029`; Pick List `STO-PICK-2026-00027`; Shipment `SHIPMENT-00027` |
| Cross-app readbacks | Airtable `recvLP8rGtUddx875`; Jira `QRC-10`; Slack via Celigo `1789421153.659629` |

The final-film brief is [TAKE05-FINAL.md](video-v2/TAKE05-FINAL.md). The final file
is
`/Users/danielwan/Documents/LogisticPilot-media/logisticpilot-devpost-final-v1.mp4`.
It received a final PASS from independent review and is approved for publishing: SHA256
`9c6293e0780e0b3f56aab9ba20d5213b860b85a5bc178d72638bc58dc31df9bc`; 267.946 seconds;
H.264 1920 × 1080 at 30 fps with AAC audio; successful full decode; and no sensitive
leak or black interval. The off-camera approval-click limitation is disclosed and was
non-blocking in the review.

## Supported and unsupported claims

| Topic | Supported statement | Do not claim |
| --- | --- | --- |
| Receiving decision | LogisticPilot separates the 20 eligible LOT-A20 units from the 5 LOT-B5 units held for inspection, so the whole order need not wait for one uncertain lot. | That LOT-B5 is cleared, defective, or safe to dispatch. |
| Photo input | The operator used Chrome's actual file-selection flow, and Amazon Nova Pro performed live visible-evidence analysis. | That the image counted hidden contents, measured dimensions, cleared quality, or identified the lot by itself. |
| Agent reasoning | A Strands agent used direct Amazon Bedrock Claude Opus 4.6 for dialogue and contract reasoning. Its output is advisory. | That the model directly controlled quantities, gates, inventory writes, or record readback. |
| Operational control | Deterministic application code owns quantities, eligibility and evidence gates, execution, and native readback. | That chat or a model response authorizes an ERP operation. |
| Human approval | A human manager approval gated the live operation. The final edit shows the manager-ready state and a truthful runtime/readback confirmation cue. | That the confirmation click itself appears in the film; it is off-camera. |
| ERP result | The live POC recorded 20 dispatched, 5 held, 0 missing, and 0 delivery-confirmed, with the listed Delivery Note, Pick List, and Shipment. | Physical shipment, carrier delivery, or customer receipt. |
| Cross-app proof | The same case has visible readbacks in ERPNext, Airtable, Jira, and Slack via Celigo, using the identifiers above. | A generic dashboard, agent answer, or unrelated historical record proves those readbacks. |
| Business value | The POC demonstrates a way to avoid holding an entire order for one uncertain lot and to reduce duplicate entry and reconciliation. | Measured time savings, production ROI, or a completed customer outcome. |
| Postage scenario | The $24.80 difference is a conditional scenario estimate, subject to its stated fit and release conditions. | Realized savings, purchased postage, or a carrier charge. |
| POC status | Purpose-built synthetic business records were executed through live connected systems. | Production deployment, physical shipment, delivery, earned revenue, or realized savings. |
| Platform scope | Amazon Nova Pro is part of the current visible-evidence flow, and Slack via Celigo is the current handoff and readback route. | That AgentCore powers the current TAKE05 path. AgentCore remains separate historical proof. |

## Recording and publication boundary

- The final edit preserves the causal boundary: manager-ready review first, then a
  concise runtime/readback confirmation cue, followed by native and cross-app
  records. It does not show the approval click.
- “Dispatched” means a recorded demo-system state. “Delivery-confirmed: 0” means the
  film does not establish a completed delivery.
- The independently reviewed final export is 267.946 seconds and under five minutes.
  Its SHA256 identifies the exact PASS-reviewed MP4 for publication.
- The connected tenant, credentials, and matching runtime journal are private. A
  clean clone can run repository checks but cannot replay this live business event.

## Historical evidence boundary

PO20 and the earlier PO25 and PO26 cases are retained historical evidence only. They
must not be presented as the TAKE05 case, its approval, its photo upload, or its
cross-app proof. Historical AgentCore, multi-agent, and integration experiments have
their own dated records and do not establish the current path.

The project was formerly called The Missing 20. Retained package names, audit paths,
and older records use that name for traceability. All enterprise records are
purpose-built POC data; third-party photo assets retain their recorded licenses.
