# LogisticPilot current recording architecture

This describes the connected 25-part receiving case. It supersedes PO20 diagrams
for this recording; the older assets remain historical evidence.

```mermaid
flowchart LR
  Human[Operator: photo, lot, inspection input] --> UI[Dashboard ↔ Operations<br/>Shared case and selected lot]
  UI --> Coordinator[Operations coordinator]
  ERP[(ERPNext demo tenant)] -->|Current case read| Coordinator
  Coordinator -->|Bounded evidence packet| Agent[Strands assistant<br/>Bedrock Opus 4.6]
  Agent -->|Photo analysis request| Vision[Existing image reader]
  Vision -->|Observation, not quality clearance| Coordinator
  Agent -->|Explanation or supported draft| Coordinator
  Coordinator --> Gate[Quantity, evidence and revision checks]
  Gate --> Confirm[Exact-action human confirmation]
  Confirm --> Executor[Bounded ERP executor]
  Executor -->|Approved operation| ERP
  ERP -->|Native record readback| Result[Verified document status and quantities]
  Result --> UI
```

The assistant's current read tool returns the prefetched case packet. It is not
an independent external RPC. Structured drafts do not authorize writes. The
application enforces the current source and exact proposal scope before execution.

The verified reference case recorded 20 dispatched and five held. That proves
demo ERP behavior, not physical shipment, payment or production impact. Photo
fixtures and business inputs are disclosed POC evidence. AgentCore, historical
multi-agent experiments and earlier SaaS handoffs are not on this runtime path.
