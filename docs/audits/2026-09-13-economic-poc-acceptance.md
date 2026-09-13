# Economic POC: real advice, approved dispatch and ERP readback

Date: September 13, 2026. Implementation base: `4daba4d`.

**Accepted business result:** the browser compared two fulfillment choices with
real Strands/Bedrock calls, prepared an exact 20-unit action, and approved its
native ERP execution. Independent ERP GETs confirmed 20 units against the correct
sales order and batch. Five units remain held. No postage was purchased and no
physical shipment or customer receipt was verified.

## Isolated inputs

- Evidence-packet alias: `LP-POC-COST-01`.
- Runtime case: `M20-DIST-ECONOMIC-ECON-20260913`.
- Purchase order: `PUR-ORD-2026-00023`, 25 units, USD100 order value.
- Sales order: `SAL-ORD-2026-00017`, 25 units, USD150 order value.
- LOT-A20: whole-lot inspection passed; 20 available for dispatch.
- LOT-B5: a one-unit sample failed; all 5 held pending resolution. This does
  not establish that all 5 are defective.

Orders, contracts, physical observations, destination and package fit are
explicitly synthetic. The native ERP documents and model calls are real.
The story's September 13 09:00 Pacific evaluation snapshot is a synthetic business
timestamp; it is not the wall-clock time of the early-morning acceptance run.
The historical PO20 case and its port8930 runtime were not reset or rewritten.

First dispatch must meet the September 14 15:00 Pacific deadline; a split final
remainder is due September 16 15:00. Consolidation requires all25 qualified by
September14. These are dispatch deadlines, not arrival guarantees.

## What actually ran

| Step | Observed result |
| --- | --- |
| Provisioner review, dry and read modes | Fresh instance and distinct ERP identities checked before execute |
| Four synthetic receiving/inspection events | HTTP200; native receipts, quality inspections, A20 stock transfer and draft pick created |
| Browser **Compare with agent** | Real Opus4.6 via Strands/Bedrock; selected `split20` with four source citations; no proposal and dispatched0 |
| Browser **Prepare this dispatch** | Another real model call; exact20 pending proposal bound to current case revision |
| Deliberately stale approval | HTTP400, `proposal revision is stale`; no dispatch |
| Browser **Approve and execute** | Existing approval workflow applied exact20; remaining5 stayed held |
| Independent direct ERP GETs | Submitted pick, Delivery Note and Shipment; same sales order, batch, warehouse and20quantity |
| Server restart and fresh GET | Economic effect remains `APPLIED`, quantity20 with the exact three native refs; prior model decision is `HISTORICAL` |

Native readback:

- `STO-PICK-2026-00020`: docstatus1, Completed.
- `MAT-DN-2026-00022`: docstatus1, quantity20, linked to SO17 and Pick20;
  batch `M20-DIST-ECONOMIC-ECON-20260913-BATCH-A20` from the isolated accepted warehouse.
- `SHIPMENT-00020`: docstatus1, linked to DN22 and the synthetic destination.
  Carrier field explicitly says synthetic event feed, no carrier booking.
- `SAL-ORD-2026-00017`: ordered25; ERP `delivered_qty`20. Here ERP's delivery
  quantity records the submitted Delivery Note, not independent customer receipt.
- Final projection: received25, dispatched20, held5, allocated0, usable0,
  carrier-confirmed0. The complete25-unit order is still open.

## Real model evidence and failed attempts

Configured model: `us.anthropic.claude-opus-4-6-v1`, Bedrock `us-west-2`.
The economic agent reads four actual tool results: contract, quality, cost and
operational snapshot. Candidate definitions are supplied; the model is not given
the deterministic feasibility verdict or a precomputed preferred answer.

The first two probes returned no structured decision after tool reads. Inspection
of the installed Strands event-loop source established that `Limits.output_tokens`
is cumulative across the invocation: the original256 allowance was too small.
The fix uses bounded2048output/16384total tokens and records the SDK stop reason;
a budget stop is reported as such rather than replaced with a scripted answer.

After that correction, real baseline calls selected `split20`. An initial
counterfactual was inconsistent (`QUALIFIED` instead of runtime `USABLE`), and the
model deferred. Correcting that probe input produced `consolidation25` with source
citations when25 units were usable. The corrected counterfactual took about20.7s;
it changed evidence only in memory and created no ERP release or25-unit action.
Failed and successful raw runs remain local acceptance artifacts.

This is a small mechanism check, not an accuracy benchmark or a measured advantage
over a rules-only system. In the economic slice there is one Strands selection
agent; this audit does not claim a new multi-agent benchmark.

## Business value and limits

Two assumed Medium Flat Rate boxes cost an estimatedUSD49.60; one costsUSD24.80,
using the [USPS Notice123](https://pe.usps.com/text/dmm300/Notice123.htm) rate checked
September13, effectiveJuly12. The USD24.80 difference is postage-only scenario
arithmetic. Package fit is synthetic, the second dispatch is conditional, and
there is no paid saving, recovered revenue or profit measurement. Order values
are not financial benefit.

The demonstrated usefulness is a traceable choice under quality and contract
constraints, followed by an actual bounded ERP result. Consolidation is advice
only; there is no native25-unit preparation in this slice. Quantities and case
choices are intentionally fixed for this POC, not a general routing optimizer.
Standalone comparisons are held in process memory. An approved proposal's
existing journal snapshot can supply its prior recommendation after restart;
this is not a general durable model-history feature. The economic card reads
execution status and native references from the same persisted proposal/event
journal, and labels a recommendation historical when current evidence changes.
This fixes an observed acceptance defect where the economic card initially
continued to say pending after the native action had already succeeded. Native
references retained with an event describe its execution-time evidence; the
independent fresh ERP read above owns the current document-status assertions.

Focused business/server/provisioning checks passed during implementation; final
economic tests, Python lint/format, JavaScript syntax and diff checks were also
run. No UI unit tests were added. Browser checks cover functional integration;
the user retains final visual review. Screenshots were inspected during browser
acceptance. Public judge access, video quality and prize readiness are outside
this acceptance claim.

## Reopen this accepted local run

Open `http://127.0.0.1:8931/operations?view=dashboard#ops-economic-panel`.
The retained PO20 workspace stays on8930. This completed instance should remain
completed; do not erase its event history merely to repeat a video take.

The local run uses configuration
`/private/tmp/logisticpilot-economic-config-20260913.json` and runtime directory
`/private/tmp/logisticpilot-economic-runtime-20260913`. They are local runtime
artifacts, not repository fixtures. Start `scripts/decision_workspace_server.py`
with `--port 8931`, `--distributor-operations-config` and `--runtime-directory`
pointing to those paths, using the existing demo Bedrock environment, native
receiving dialogue enabled, distributor model `opus46`, and retained projection,
handoff sync and live-source autostart disabled.

For a new take, the provisioner now supports `--scenario economic-poc` with a
fresh uppercase `--instance` and `--date 2026-09-13`. Review its `--mode dry` and
`--mode read` output before the explicit `--mode execute --execute` operation.
Its output contains the isolated configuration and ordered synthetic activation
events. Do not point a fresh case at this accepted runtime or mix its records
with historical PO20.
