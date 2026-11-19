---
name: ai-computer-vision
description: Use for designing a vision solution — choosing the task and approach, the dataset and annotations, a leak-free split, metrics, errors by slice, image privacy, drift.
metadata:
  review: "2027-04-17"
  catalog: "Use when you must design or assess an image and video recognition system — formulating the task (classification, detection, semantic and instance segmentation, keypoints, OCR and Document AI, video tracking), choosing the approach (a ready or foundation zero-shot model, a vision-language model, fine-tuning a pretrained backbone, training from scratch rarely) by data, latency and device, building the dataset (collection, class balance, edge cases, annotation guidelines, label checks), augmentation by deployment conditions, a leak-free split (the same scene, patient, camera in one set), metrics (accuracy and F1, mAP at IoU thresholds, IoU and Dice, CER and WER), error analysis by slice, evaluation on deployment data, edge device constraints, image privacy (faces, plates), image drift. Not for quantization and ONNX/TensorRT export (ai-model-optimization), the mechanics of fine-tuning (ai-fine-tuning), the method of evaluating LLM features (ai-evals), the model pipeline in production (ai-mlops), the legal bases of RODO/GDPR (arch-privacy-compliance) or hosting LLMs (ops-ai-inference)."
  keywords: "computer vision, widzenie komputerowe, rozpoznawanie obrazu, detekcja obiektów, klasyfikacja obrazów, segmentacja, YOLO, mAP, IoU, Dice, OCR, CER, WER, faktury skany, adnotacja, etykietowanie zdjęć, zbiór zdjęć, augmentacja, wyciek danych, kamera, linia produkcyjna, kontrola jakości wizyjna, wykrywanie wad, tablice rejestracyjne, twarze, anonimizacja obrazów, urządzenie brzegowe, edge, śledzenie obiektów, wideo, dryf obrazów, model wizyjno-językowy, image recognition, object detection, image classification, segmentation, invoice scans, annotation, photo labelling, image dataset, augmentation, data leakage, camera, production line, visual quality control, defect detection, licence plates, faces, image anonymization, edge device, object tracking, video, image drift, vision-language model"
---

# Vision solutions — from the task and data to an assessment on images from deployment

This skill designs **a vision solution**: the task, the approach, the data, the assessment, the risks. Shrinking and exporting the model
(quantization, ONNX, TensorRT) is **ai-model-optimization** (`.claude/skills/ai-model-optimization/SKILL.md`),
the mechanics of fine-tuning — **ai-fine-tuning**, the evaluation method and gates — **ai-evals**, the registry, the pipeline and drift
in production — **ai-mlops**, the legal bases — **arch-privacy-compliance**, hosting LLMs — **ops-ai-inference**.

## Procedure
1. **Deployment conditions.** Write down: who uses the result and which error hurts more (a false alarm or a miss),
   the camera or source, lighting, distance, resolution, the device (a GPU server, CPU, an edge device),
   the p95 latency budget. Without this neither the model nor the metric can be chosen.
2. **Formulate the task** (table and metrics: `references/tasks-and-metrics.md`). The simplest task that solves the problem:
   "is there a defect" is classification, "where is it" is detection, "what area" is segmentation, besides that keypoints,
   OCR and Document AI, video tracking. A harder task means more expensive annotations.
3. **Choose the approach, from the cheapest** (the next one only after a failure on the assessment set from step 5):
   - a ready or foundation zero-shot model (detection and segmentation from a description or a point) or a vision-language model
     (VLM) through an API: zero labels, good for a prototype and rare cases; slow, expensive per image and hard to
     run on a device;
   - fine-tuning a pretrained backbone on your own data (mechanics: **ai-fine-tuning**): the default choice
     with hundreds to thousands of labelled images and a hard latency limit;
   - training from scratch rarely: only for images very far from natural ones (e.g. specialized sensors) and a large amount of data;
   - a larger model can serve as a teacher or a pre-labelling tool, and a small student runs on the device.
   Check the licences of the weights and the data before choosing (commercial use is sometimes forbidden) [assumption: licences differ between models].
4. **The dataset.** Collect under deployment conditions (those cameras, times of day, backgrounds), not from photos on the web. Set the class balance
   and the edge cases (a rare class, a small object, occlusion, blur, glare, an "almost defect" object, empty frames
   without an object). Collect more of the rare classes deliberately, not only by weighting them in the loss.
5. **Annotations.** Written guidelines with pictures: what is an object, how to draw a box (tight, an object partially
   visible), what to do when in doubt (a separate "uncertain" label). A pilot on 50–100 images with two annotators,
   compute the agreement (box IoU, kappa for classes), discuss the disagreements and fix the guidelines. Label checks: a sample for
   re-review, and the images with the highest model loss you check for a wrong label before "fixing" the model.
6. **A leak-free split.** Split by **group**, not by image: the same scene, the same patient or study, the same
   batch, the same video (the frames are almost identical), the same camera where the deployment will include new cameras.
   Freeze the test set and do not use it for tuning; find duplicates and near-identical photos before the split
   (perceptual hashes or embedding distance). A validation set for tuning, a separate test set for the decision.
7. **Augmentation by deployment conditions.** Add only changes that will really occur: brightness and contrast with
   variable light, motion blur, noise, JPEG compression, shifts and scale. A horizontal flip breaks OCR, text,
   left and right sides (e.g. anatomy); a 90-degree rotation breaks objects that always stand upright. Apply augmentation
   after the split and only to the training set. Check a sample of augmented images by eye.
8. **Metrics and the threshold** (`references/tasks-and-metrics.md`). Tie the metric to the cost of the error from step 1, set the acceptance
   threshold before measuring. Report precision and recall at a specific confidence threshold, not mAP alone.
   For video, tracking metrics separately.
9. **Error analysis by slice.** The result broken down by: lighting, camera, object size (small, medium, large),
   distance, background, class. The average hides regressions. Look at the 30–50 worst errors and name their causes
   (label, data, model, conditions); each cause leads to a different fix (more data, guidelines, augmentation, model).
10. **Assessment on deployment data.** A dataset from the internet or a lab inflates the result. Before the launch run the model
    in shadow mode on the real stream and compare it with a human assessment of a sample (the method and gates: **ai-evals**).
11. **An edge device.** The latency and memory budget determine the model size and the input resolution; measure
    the whole pipeline (decoding, scaling, NMS, tracking), not the model alone. Quantization and export:
    **ai-model-optimization**; after them repeat the assessment from step 9, because INT8 mainly breaks small objects and the tail of the distribution.
12. **Image privacy.** A face, a licence plate, a screen, a document with data are personal or sensitive data.
    Collect the minimum, anonymize (blur or mask) as early as possible before saving, limit the retention of raw frames,
    check access to the annotation dataset and to external labelling tools. The legal basis, DPIA, processors:
    **arch-privacy-compliance**.
13. **Drift and monitoring.** After deployment track the input distribution (brightness, sharpness, object size, embeddings),
    the distribution of confidence and of the number of detections per frame, and a sample with manual assessment; a change of season, camera, lighting
    or product batch are the typical sources. Alerts, retraining and the registry: **ai-mlops**.

## Result
The solution design (a fixed layout): the task and conditions · the approach with an alternative · the dataset plan (numbers, classes, sources,
guidelines) · the split rule · metrics and acceptance thresholds · the plan for assessment by slice and on deployment data ·
device constraints · privacy · monitoring · risks and the next step.

## Example
Input: "A stamping line, 3 cameras, approx. 800 photos of metal sheets, scratches in approx. 2% of the photos, a result in < 100 ms on an industrial
computer without a GPU."
Result:
- task: scratch detection (boxes), because the operator has to point to the place; "defect/OK" classification as a simple baseline;
- approach: a fine-tuned small backbone, a zero-shot VLM only for pre-labelling; the CPU candidate checked in ai-model-optimization;
- dataset: from approx. 16 photos with a defect, collect more up to min. 150 frames with a defect (deliberately inducing defects on samples), as many again "almost defects" (hairline scratches, dust) [example];
- split: by batch of sheets, not by photo; one camera (camera 3) only in the test set, to measure a new camera;
- metrics: defect recall ≥ 95% at precision ≥ 80% on the test set, mAP@[.5:.95] as an auxiliary; results separately per camera and shift (morning, evening);
- next step: an annotation pilot of 60 photos with two annotators, guidelines for hairline scratches.

## Checklist
- [ ] deployment conditions and the cost of the error written down before choosing the model
- [ ] the approach from the cheapest (zero-shot, VLM) to fine-tuning; licences checked
- [ ] annotation guidelines, a pilot with two annotators, label checks
- [ ] the split by group (scene, patient, camera, video); the test set frozen
- [ ] only augmentations that are real for the deployment, after the split
- [ ] metrics chosen for the task, the threshold before measuring, the result by slice
- [ ] assessment on deployment data (shadow mode), measuring the whole pipeline on the device
- [ ] anonymization and retention of images; drift monitoring with a manual sample

## Additional materials
- `references/tasks-and-metrics.md` — tasks, metrics (COCO), CER and WER, assessment pitfalls.

## Sources
- COCO, "Detection Evaluation" (cocodataset.org) and descriptions of the protocol in citing papers (e.g. arXiv 1804.07437):
  AP averaged over 10 IoU thresholds 0.50–0.95 in steps of 0.05, AP50, AP75, AP small/medium/large by area 32² and 96²;
  a search on 2026-10-17, the COCO pages were not opened [unverified in the primary source].
- The names of model families (YOLO, Segment Anything, CLIP) and the current versions: [unverified], check in the documentation before choosing.
Described in our own words.
