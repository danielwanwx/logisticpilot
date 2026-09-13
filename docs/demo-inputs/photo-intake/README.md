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

This is a development example, not a held-out benchmark, an accuracy estimate,
or a demonstration that phone camera capture has been tested on hardware.
