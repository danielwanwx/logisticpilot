# Receiving evidence v1

This is an isolated, read-only paired experiment. It compares a deterministic rules/form baseline, one Strands investigator, and a fixed native Strands Graph with receiving/quality and fulfillment/contract specialists followed by a guarded coordinator. It does not modify the product, ERP data, or promotion state.

Only four synthetic development cases are included:

- `DEV4-completed-simple` (schema wiring only; excluded from business-reasoning evidence)
- `DEV4-split-pending-quality`
- `DEV4-missing-unit-conversion`
- `DEV4-ambiguous-acknowledgement`

There are no held-out cases here. Author them only after the candidate freeze manifest is created and the development checks are accepted.

The development snapshots exercise schema wiring, not an eligibility solver. `DEV4-completed-simple` intentionally omits a precomputed `eligibility_state` and `eligible_quantity`; the rules baseline then returns `unknown`, an unknown eligible quantity with the requested unit, and the explicit missing prerequisite `mechanical eligibility state is absent`. The shared answer contract also permits `pending_evidence` or `unknown` with named prerequisites, so a model must cite enough raw source literals to support a disposition or preserve that uncertainty. For unresolved orders, deterministic scoring requires a nonempty missing-prerequisite field but does not judge its free prose; citation and state checks remain mechanical, while the reason's correctness is semantic review material. Held-out cases must use raw contracts, lot quality, and quantities rather than a precomputed feasible plan.

Use `/private/tmp/m20-evals-venv`; the project lock and application environment remain unchanged.

### Isolated environment

Create the scratch environment outside the repository. These are the exact package
versions verified for this experiment on Python 3.12.13; installing them does not
change the project dependencies or lock files.

```sh
python3.12 -m venv /private/tmp/m20-evals-venv
/private/tmp/m20-evals-venv/bin/python -m pip install \
  "boto3==1.43.93" \
  "botocore==1.43.93" \
  "pydantic==2.13.5" \
  "strands-agents==1.53.0" \
  "strands-agents-evals==1.2.0" \
  "strands-agents-tools==0.8.8"
```

```sh
/private/tmp/m20-evals-venv/bin/python experiments/receiving_evidence_v1/receiving_evidence.py \
  freeze --output /private/tmp/receiving-evidence-v1.freeze.json

/private/tmp/m20-evals-venv/bin/python experiments/receiving_evidence_v1/receiving_evidence.py \
  run \
  --case experiments/receiving_evidence_v1/dev_cases/DEV4-completed-simple.case.json \
  --key experiments/receiving_evidence_v1/dev_keys/DEV4-completed-simple.key.json \
  --candidate rules \
  --freeze-manifest /private/tmp/receiving-evidence-v1.freeze.json \
  --ledger /private/tmp/receiving-evidence-v1.ledger.jsonl \
  --run-log /private/tmp/receiving-evidence-v1.runs.jsonl
```

Every run needs an externally supplied case and key. Case inputs contain a synthetic snapshot envelope, semantic question, source packets, and a shared requested-output scope containing only requested quantity names and order IDs. It contains no expected values, verdicts, or rubric, and is passed to every candidate so exact output scope is not a hidden evaluator rule. A key holds expected typed quantities, order dispositions, citation requirements, and source coverage outside every agent prompt. The source envelope records `snapshot_as_of`; each source and record has its own nullable `as_of`, so stale and unknown evidence remains observable. A packet can be explicitly unavailable with zero records; a specialist can return zero literals only with a matching explicit source-read status and missing-evidence reason.

The Graph uses two actual entry nodes and two conditional edges. Since Strands Graph incoming edges are OR, both conditions read the completed native Graph state and require two independently parsed `SpecialistObservation` values before constructing one typed `JoinPacket`. The coordinator proxy ignores Graph's raw dependency text and receives that validated packet only.

The custom `ReceivingEvidenceEvaluator` subclasses the official `strands_evals.evaluators.Evaluator` and runs through an official `Experiment`. It scores identity, typed quantities, per-order disposition, citation membership, actor-local source scope and citation closure, source coverage, and the absence of authority/write claims. It is deterministic and not a paid LLM judge.

Model candidates are deliberately blocked unless `--execute-model` is supplied. That path uses only Nova Pro (`us.amazon.nova-pro-v1:0`, `us-west-2`, profile `missing20-sandbox`, temperature 0), sets `retry_strategy=None`, and creates its Bedrock client with `total_max_attempts: 1`. The model adapter lowers and verifies the delegate's `max_tokens` before every request, then reserves the same limit. It records unknown usage as the full reservation. The per-workflow limit is eight provider requests, 32,000 input tokens, 6,000 output tokens, USD 0.06, and 180 seconds. The fixed Graph splits this into 3/3/2 requests with 12k/12k/8k input and 2k output per node; its native `Limits` are supplementary only.

The append-only durable ledger reserves each model workflow against the USD 3 experiment ceiling before it starts and has no reset command. Private run JSONL and ledger files are created with mode `0600`. A run record includes usage, conservative reservations, errors, tool calls and returned record IDs, model attempt trace, Graph event summary, answer, evaluator result, and `NOT_AUTOMATICALLY_PROMOTED` status; partial model attempts and tool events are retained when a run fails.

To make semantic-review material after paired runs, export randomized A/B labels without candidate, provider, actor, or trajectory identity:

```sh
/private/tmp/m20-evals-venv/bin/python experiments/receiving_evidence_v1/receiving_evidence.py \
  export-blinded \
  --run-log /private/tmp/receiving-evidence-v1.runs.jsonl \
  --output /private/tmp/receiving-evidence-v1.blinded.json \
  --seed reviewer-batch-1
```

The export retains the question, structured answer fields, citations without actor names, and a source-packet reference. Mechanical trajectory review stays in the unblinded private log.

Focused no-network checks:

```sh
/private/tmp/m20-evals-venv/bin/python -m unittest \
  experiments/receiving_evidence_v1/test_receiving_evidence.py
```
