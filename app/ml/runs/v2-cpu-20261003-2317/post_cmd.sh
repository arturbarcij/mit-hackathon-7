set -e
cd /workspace
RUN=app/ml/runs/v2-cpu-20261003-2317
PY=.venv-ml/bin/python
$PY app/ml/calibrate.py --ckpt $RUN/best.pt --manifest app/ml/manifest_v2.csv --splits val uganda_calib \
  --target 0.95 --fallback-target 0.90 --threads 4 --workers 2 --batch-size 64 --out $RUN/calibration.json
$PY app/ml/export.py --ckpt $RUN/best.pt --calibration $RUN/calibration.json --manifest app/ml/manifest_v2.csv \
  --quant auto --version v2-2026-10-04 --out-dir $RUN/model --parity-dir $RUN/parity_samples --report $RUN/export_report.json
$PY app/ml/evaluate.py --model-dir $RUN/model --calibration $RUN/calibration.json --export-report $RUN/export_report.json \
  --manifest app/ml/manifest_v2.csv \
  --sets in_domain_test heldout_uganda_test heldout_rocole rocole_red_spider_mite synthetic_blank_pages \
  --out $RUN/eval_v2/metrics.json --fig-dir $RUN/eval_v2/figures
echo POST_DONE
