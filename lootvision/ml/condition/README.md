# Condition Assessment — Baseline vs. Trained Model

## Current state (baseline)
`HeuristicConditionScorer` in `condition_scorer.py` uses classical CV signals
(Laplacian variance, local contrast, left/right asymmetry) to produce an
explainable 0-100 score with zero training data required. This is intentional
per the project brief: implement a realistic baseline, design the interface so
a stronger model can be swapped in later.

## Upgrade path (`TrainedConditionScorer`)

**Option A — Supervised regression.** Collect N labeled photos with human-
assigned condition scores (0-100) into `data/metadata/condition_labels.csv`
with columns `image_path,condition_score`. Fine-tune a small CNN (e.g.
MobileNetV3-Small backbone + linear head) to regress the score directly.
~200-500 labeled images is a realistic student-project scope.

**Option B — Feature-space anomaly detection.** Collect only "good condition"
reference images (no labeling needed beyond that). Train an autoencoder (or
use CLIP embeddings + a one-class SVM / Mahalanobis distance in embedding
space) on those references only. At inference time, reconstruction error /
distance-from-normal becomes the anomaly signal, which maps to a condition
penalty. This avoids needing graded labels at all — only "this item is in
good condition" examples.

Option B is recommended as the stronger academic contribution: it's a genuine
anomaly-detection formulation (as suggested in the brief §8) rather than a
supervised regression, and ties into the same embedding infrastructure already
built for retrieval (`ml/embeddings/embedder.py`).

## Evaluation
Once either option is trained, evaluate with `ml/evaluation/metrics.py`'s
`condition_classification_report()` against a held-out labeled set — do not
report condition accuracy without held-out ground truth.
