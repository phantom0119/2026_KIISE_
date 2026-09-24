#!/bin/bash
set -e
SC=/tmp/claude-1000/-home-explorer-vectorDB-experiments-db-KIISE-datasociety/89f75197-8dd7-4e3a-8116-fba366aac4d8/scratchpad
PY=$SC/envs/hcbgen/bin/python
REPO=/hdd2/KIISE_datasociety/Datasets/public_fanns/p0_third_party/hardness_aware_fann_benchmarking
G1=/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/experiments_expansion/p0_validity_audit/g1
cd $REPO/HCBGen_v2
for C in A B; do
  echo "=== [$C] estimator on NATURAL arm $(date +%T) ==="
  $PY hardness_estimator/calculate_hardness_v5_1.py --data_dir $G1/$C/natural --save_dir $G1/$C/hardness_natural
  echo "=== [$C] generator MATCH_PDF $(date +%T) ==="
  $PY hardness_aware_generator.py \
    --base_vector_path $G1/$C/base.fvecs \
    --query_vector_path $G1/$C/queries.fvecs \
    --base_payloads_path $G1/$C/payloads.jsonl \
    --index Post_Filtering --save_dir $G1/$C/matched \
    --num_queries 1000 --query_complexity match_pdf \
    --target_hardness_json $G1/$C/hardness_natural/hardness_v5.1_1000.json \
    --num_bins 40 --dev_mode
  echo "=== [$C] estimator on MATCHED arm $(date +%T) ==="
  $PY hardness_estimator/calculate_hardness_v5_1.py --data_dir $G1/$C/matched --save_dir $G1/$C/hardness_matched
  echo "=== [$C] chain done $(date +%T) ==="
done
echo ALL_DONE
