# Incident context and goods-first Operations acceptance

Scope: the current PO25 / SO19 demo on port 8933. Review date is September 14 UTC / September 13 Pacific. This continues the [independent interaction review](2026-09-14-operations-interaction-review.md), with implementation delegated and actual diff/browser acceptance owned by the primary reviewer. No UI unit tests were added.

## Established runtime evidence

- Actual browser question: `For LOT-B5: Why is this held?` The existing `/assist` returned that five units require a diameter inspection in the 9.9–10.1 mm range, and requested measurement and sample quantity. It did not release inventory or prepare another dispatch.
- The active-incident link preserved LOT-B5 when moving from Dashboard into Operations. Browser back restored LOT-B5 after selecting A20. Initial source reads can take tens of seconds; load before recording.
- The new ERP record drawer returned actual case links for PO25, SO19, receipts 27/28, inspection 21, Delivery Note 24, Pick List 22, Shipment 22 and Stock Entry 22.
- Clicking Delivery Note 24 in the in-app browser opened the correct ERP route but required login. The existing signed-in Chrome profile opened it successfully: quantity **20**, status **To Bill**. Shipment 22 was **Submitted** and linked to Delivery Note 24. No credentials were searched for or copied.
- Current business state is still **20 dispatched / 5 held**. Shipment creation is not a physical carrier booking or delivery confirmation. No second dispatch was approved during this acceptance.

## Defects found and returned to implementation

| Problem | Required correction |
| --- | --- |
| A20 selection could retain a B5 Agent photo. | Reconcile linked photo context on lot changes and before `/assist`. |
| A20 card showed the case total of 25. | Read the selected lot's received quantity: A20 has 20. |
| Dashboard stage link lost its lot after alert normalization. | Resolve the raw alert before creating the Operations link. |
| Check ERP remained disabled after initial loading. | Restore the control after the request finishes. |
| Earlier photo analysis appeared under a current ERP heading. | Show a photo-check note only when the linked analysis is current. |
| Separate Item/Lot/Quantity fields did not communicate a task. | Present one selectable goods card per batch and reveal its next step. |
| Full-height edge drawers obscured the workspace. | Use inset rounded floating panels with bounded height and close controls. |

## Verification boundary

New image acquisition and API analysis are separate from a browser file-chooser test. The recording may use already attached public photographs with the documented POC association. Microphone capture, a fresh-case approval take, public judge access and final video playback are separate outstanding checks. Historical duplicate chat messages are retained history, not new model responses.

## Final browser acceptance

The goods-v15 build was loaded in the real browser. The following are observed UI results, not unit-test assertions:

- Dashboard **Review hold** opened Operations with `lot=LOT-B5` and its selected goods card.
- **Needs attention** contained B5, its rusted-parts photograph, 5 received and 5 held. **Inspection passed** contained A20, its separate clean-fastener photograph and 20 received. A20's group comes from its APPLIED PASS inspection event; the photograph does not grant that status.
- **Review this batch** selected the matching photo: `demo-rusted-fasteners-20260914` for B5 and `demo-clean-fasteners-20260914` for A20. Switching cards cleared the incompatible upload preview. Back navigation across batches also cleared it.
- The selected A20 view did not show B5's inspection card or claim its backorder as an A20 defect. Case-wide orders remain explicitly labeled.
- **Check ERP** completed and re-enabled. Batch details and Inspection details remained expanded across that live refresh.
- ERP records appeared in a centered, rounded 560px desktop dialog with surrounding page visible. The close control returned to the workspace. A 390×844 mobile review showed an inset rounded Agent dialog, visible composer/close controls and no horizontal card overflow.
- Expanded decision and execution details separated the APPLIED 20-unit operation from the evidence needed for another dispatch. No empty model-comparison panel was presented as an execution failure.
- Selected batch photo history showed the current rusted image first, with prior source-state observations retained as history. The full case history remains a separate disclosure. Both new photographs completed actual Bedrock analysis; see the [photo input evidence](../demo-inputs/photo-intake/README.md), including the first ERP-read failure and one successful recovery.
- Final goods-v16 targeted browser check: the selected B5 photo still displays **Damage flagged**, its actual rust observations and inspection recommendation. The irrelevant identity panel is omitted for detail/overview photos whose identity checks are all NOT_APPLICABLE with no observed identity. Meaningful identity checks are preserved by the reviewed guard. The preview was left on the goods cards with live data loaded.

## UI skill quick review

Scope: goods cards, selected-batch details, ERP dialog and mobile Agent dialog; vanilla JavaScript and the existing plain CSS. No new styling or animation framework.

| Category | Evidence inspected | Result |
| --- | --- | --- |
| Typography | Desktop/mobile screenshots; task titles and goods quantities | Clear task verbs; quantities grouped with their goods |
| Surfaces | Card selection and dialog screenshots at 1440×1000 and 390×844 | Rounded inset dialogs and readable grouped cards |
| Animations | No new animation introduced | Slow-motion animation inspection not performed |
| Icons | Existing Phosphor icons in action/close controls | Consistent existing icon system |
| Performance | Live refresh, selection and disclosure persistence | No UI unit tests; API latency remains variable |

| Severity | Location | Before | After | Why |
| --- | --- | --- | --- | --- |
| HIGH, fixed | Operations goods selector | Separate Item/Lot/Quantity blocks | One card with photograph, item, batch and quantity | Clear object grouping and entry point |
| HIGH, fixed | Selected photo intake | Old batch image survived a switch | Incompatible linked selection cleared for cards and history navigation | Prevent acting on the wrong goods |
| MEDIUM, fixed | ERP and Agent overlays | Full-height edge drawer | Inset rounded dialog | Preserve workspace context and clear boundaries |
| MEDIUM, fixed | Expanded details | Refresh collapsed dynamic content | Stable disclosure identity | Avoid interrupting reading |

Considered but rejected: replacing the styling system would disrupt the approved visual direction; classifying apparently clean photographs as quality-passed would invent an inspection result. Existing accepted inspection records determine that grouping instead.

Verdict: the inspected primary goods flow passes. Browser file upload/camera, voice capture, fresh-case approval and public judge access remain outside this acceptance, as stated above. Source delays can exceed the browser's 45-second read timeout while other API work is active; preload the case and complete model work before recording. This is a POC acceptance, not a production or award-readiness certification.
