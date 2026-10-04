set -e
cd /workspace
RUN=app/ml/runs/v2-cpu-20261003-2317
PY=.venv-ml/bin/python
cp $RUN/calibration.json app/ml/calibration.json
rm -f app/ml/figures/*.png
$PY app/ml/export.py --ckpt $RUN/best.pt --calibration app/ml/calibration.json --manifest app/ml/manifest_v2.csv \
  --quant auto --version v2-2026-10-04
$PY app/ml/evaluate.py --manifest app/ml/manifest_v2.csv \
  --sets in_domain_test heldout_uganda_test heldout_rocole rocole_red_spider_mite synthetic_blank_pages
echo PUBLISH_DONE
