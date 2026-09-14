# Photo intake demo input

`input-01.jpg` is an unmodified public photograph, not a photograph of our demo
warehouse or its inventory. It is a POC stand-in for an operator's incoming
carton photograph. The model receives normalized image bytes and a generic
inspection prompt; this description, source title and expected observation must
not be passed as image evidence.

## Attribution

Photo: **Damaged Cardboard Box Labelled Fragile**, by **Meanwell Packaging**.
Source: [Wikimedia Commons file page](https://commons.wikimedia.org/wiki/File:Damaged_Cardboard_Box_Labelled_Fragile.jpg).
Original: [Flickr](https://www.flickr.com/photos/195311218@N08/52160346520/).
Author website: [Meanwell Packaging](https://meanwell-packaging.co.uk/).
License: [Creative Commons Attribution 2.0](https://creativecommons.org/licenses/by/2.0/).
No edits were made to the stored photograph. The application's normal image
preprocessing strips metadata and resizes/re-encodes bytes for model input.
This photograph is licensed separately from the repository's software.

## Additional public fastener references

`input-02.jpg` and `input-03.jpg` are unmodified public photographs selected
for a detail-photo POC. They are reference images, not photographs of the
demo warehouse or verified arrivals. They come from different public sources
and show visually different fasteners; no common SKU, package, lot, or
physical relationship between them has been verified.

| File | Selection and source | Attribution and license | Stored bytes |
| --- | --- | --- | ---: |
| `input-02.jpg` | **Clean fastener detail reference.** [Silver and black metal tools](https://unsplash.com/photos/silver-and-black-metal-tools-qHhJkxare7A), retrieved 2026-09-13 (America/Los_Angeles) as the source server's 3000w JPEG rendition. No local edits. | Edge2EdgeMedia, [Unsplash License](https://unsplash.com/license) | 539,107 |
| `input-03.jpg` | **Visible-corrosion detail reference.** [Bolts and nuts](https://commons.wikimedia.org/wiki/File:Bolts_and_nuts.jpg), retrieved 2026-09-13 (America/Los_Angeles). The stored file is the unmodified original. | Star61, [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) | 418,275 |

The exact stored JPEG bytes are identified by these SHA-256 digests and were
checked with `file` after copying:

| File | Dimensions | SHA-256 |
| --- | ---: | --- |
| `input-02.jpg` | 3000 × 1997 | `51dd00adbf63aff4dc23a198add1699b1c0c82dd64ddf01c6f71320d52b8f17a` |
| `input-03.jpg` | 2812 × 2000 | `ae1b30f76715bca99cb84b04badb415bb7df9e76be099e1ed8b869d305ff8a03` |

For the POC association, `input-02.jpg` is explicitly selected for `LOT-A20`
and `input-03.jpg` is explicitly selected for `LOT-B5`. These are operator
scenario links only. The photographs do not identify the demo SKU or lot, do
not establish an accurate quantity or size, and do not prove that either
public photograph depicts the associated ERP goods.

## Bounded live API verification

The stored bytes were attached and sent to the existing local
`/api/v1/distributor-operations` photo and `analyze-photo` endpoints on
2026-09-13 (America/Los_Angeles). The calls were sequential and used only
photo attachment plus read-only analysis. No event, proposal, approval,
receipt, inventory mutation, or quality release was requested.

The clean reference upload returned HTTP 200 in 14,891 ms. Its analysis
returned HTTP 200 in 25,964 ms with `advisory_current=true`, `linked_lot=LOT-A20`,
and `purpose=detail`. The stored model observation was `status=COMPLETE`,
`visible_condition=no_visible_damage`, and an empty `issues` list; the model
also requested a sharper view of the blurred peripheral fasteners. The API
returned model `us.anthropic.claude-opus-4-6-v1` through Bedrock
(`strands_multimodal`), with `source_status=CURRENT`. Its recommendation was
`NO_VISIBLE_DAMAGE_NOT_QUALITY_CLEARANCE`: a clean-looking detail is not a
quality release or stock disposition.

The rust reference upload returned HTTP 200 in 26,212 ms. Its first analysis
returned HTTP 200 in 34,248 ms but was `status=UNAVAILABLE` with
`advisory_current=false` and no linked lot because current ERP evidence was
temporarily unavailable; no model observation was returned. A read-only
current-state check then returned HTTP 200 in 35,547 ms with
`evidence_mode.status=CURRENT`. The one authorized retry of the same analysis
returned HTTP 200 in 44,762 ms with `advisory_current=true`,
`linked_lot=LOT-B5`, `purpose=detail`, and `status=COMPLETE`. It reported
visible widespread rust, pitting, flaking/material loss, rough rust-coated
threads, failed coating, and loose oxide debris. The actual model was again
`us.anthropic.claude-opus-4-6-v1` through Bedrock; `source_status=CURRENT`.
Its recommendation was `REQUIRE_INSPECTION`: visible exterior damage needs
operator-confirmed inspection and is not a quality disposition.

`CURRENT` is the API's freshness status at each read; the source supplied no
effective timestamp (`evidence_mode.as_of=null`). It does not turn these
public reference photographs into current warehouse evidence. Both completed
analyses reported source revision
`d377d37913944134379b9f69ed82e5c1f65d6bcc5f7b99425a34879047ca5946`. The raw
responses remain outside the repository in `/private/tmp`:

- `/private/tmp/logisticpilot-photo-api-20260913-input-02-upload.json`
- `/private/tmp/logisticpilot-photo-api-20260913-input-02-analyze.json`
- `/private/tmp/logisticpilot-photo-api-20260913-input-03-upload.json`
- `/private/tmp/logisticpilot-photo-api-20260913-input-03-analyze.json`
- `/private/tmp/logisticpilot-photo-api-20260913-input-03-recovery-status.json`
- `/private/tmp/logisticpilot-photo-api-20260913-input-03-recovery-analyze.json`

## What the demonstration can establish

A real image model may flag visible packaging damage or request another view.
That is a reason to inspect the associated goods. It cannot establish hidden
contents, internal defects, dimensions, cause of damage or lot-wide quality.
The carton has no verified demo SKU or lot label. A user-selected LOT-B5 link
is an explicit synthetic scenario association, not a model identification.
Five associated units come from the demo ERP records, not a count through a
closed carton.

The original economic demo's 10.3 mm sample measurement was a synthetic manual
inspection input. It must never be presented as extracted from this photograph.
Any subsequent manual measurement or quality disposition remains a separate
step. A clean-looking image likewise does not authorize a quality release.

The clean and rusted fastener responses above are model observations attached
to operator-selected LOT-A20 and LOT-B5 scenarios. They are not same-SKU
verification, physical count or size measurement, and the response's lot link
does not establish that the public photograph came from that lot.

This is a development example, not a held-out benchmark, an accuracy estimate,
or a demonstration that phone camera capture has been tested on hardware.
