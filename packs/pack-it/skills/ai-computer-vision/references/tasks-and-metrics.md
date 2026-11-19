# Vision tasks and metrics

The state from a search on 2026-10-17 (the COCO definitions from secondary sources, the primary page was not opened).

## Task → metric
| Task | Model output | Basic metrics | Notes |
|---|---|---|---|
| Classification | a label | accuracy (balanced classes), precision, recall, F1, the confusion matrix | with a rare class accuracy is misleading (98% with 2% defects is "always OK") |
| Detection | boxes + class + confidence | AP/mAP, AP50, AP75, AP small/medium/large; precision and recall at a threshold | COCO: AP averaged over IoU thresholds 0.50–0.95 in steps of 0.05; AP50 close to PASCAL VOC |
| Semantic segmentation | a class per pixel | IoU per class (mIoU), Dice | Dice = 2·|A∩B| / (|A|+|B|); IoU = |A∩B| / |A∪B| |
| Instance segmentation | a mask per object | mAP on masks (mask IoU) | like detection, but IoU computed on masks |
| Keypoints | coordinates | OKS and AP on OKS, error in pixels | normalize to the object size |
| OCR / Document AI | text, fields | CER, WER, exact field match, field F1 | the edit distance counts; assess critical fields (amount, NIP — the Polish tax ID) separately |
| Video tracking | object tracks | tracking metrics (identity switches, continuity) + detection | [unverified] check the metric names in the documentation of the chosen library |

## Definitions
- IoU = the area of the intersection of the boxes divided by the area of their union. A detection is a hit when IoU ≥ the threshold and the class matches.
- AP is the area under the precision–recall curve for a class, mAP is the average over classes. In the COCO context "mAP" usually
  means AP@[.50:.95]. When giving a result, always state which variant and which threshold.
- COCO divides objects by area: small < 32², medium 32²–96², large > 96² pixels.
- CER = (substitutions + deletions + insertions) / the number of characters in the reference; WER the same on words.

## Assessment pitfalls
- The result depends on the confidence threshold and the NMS threshold; freeze them before the final test.
- A small test set gives a wide interval: report the interval (bootstrap) and the number of examples in the slice.
- Check the labels in the test set by hand; a wrong label lowers the model's result.
- Compare models on the same dataset, resolution and threshold; the input resolution changes the AP of small objects.
- A dataset from one day or camera inflates the result; test on a new camera, season, batch.
