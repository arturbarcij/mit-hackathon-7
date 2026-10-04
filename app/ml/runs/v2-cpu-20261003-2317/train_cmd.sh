cd /workspace && .venv-ml/bin/python app/ml/train.py --manifest app/ml/manifest_v2.csv --init app/ml/runs/v1-cpu-e3/best.pt \
  --train-splits train uganda_train --val-splits val uganda_calib --max-train-per-class 2500 --uncapped-sources bracol plantdoc \
  --max-val-per-class 0 --composite-p 0.6 --field-bg-p 0.3 --plantdoc-crop-p 0.6 --synthetic-not-leaf 400 --not-leaf-share 0.125 \
  --source-weight uganda=2 --select mean_f1 --epochs 5 --patience 2 --samples-per-epoch 24000 --lr 3e-4 --device auto --out app/ml/runs/v2-cpu-20261003-2317
