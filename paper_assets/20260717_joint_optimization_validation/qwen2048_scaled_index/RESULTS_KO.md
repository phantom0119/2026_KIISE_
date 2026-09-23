# Qwen3-VL 2,048차원 대규모 색인 검증

- corpus: 143,830 real frame vectors, query: 85 text vectors
- fixed construction seed: 20260717
- scale sweep: 10k, 50k, 100k, 143,830

## 최종 규모

- Flat: recall 1.0000, p95 123.437 ms, 1178.26 MB
- HNSW M16/ef256: recall 0.9859, p95 2.978 ms, speedup 41.5x
- HNSW M32/ef256: recall 0.9906, p95 3.561 ms, speedup 34.7x
- best observed PQ recall: 0.3094, size 20.85 MB

## 3개 구축 시드 강건성

- HNSW M32/ef256 recall: mean 0.9886, std 0.0018, range [0.9871, 0.9906]
- IVF-Flat nlist1024/nprobe128 recall: mean 0.9933, std 0.0036, range [0.9894, 0.9965]

어느 후보도 3개 시드 모두에서 recall 0.99 이상을 보장하지 않았다. 따라서 단일 시드 점 추정치를
고정 보장으로 표현하지 않고, 고정밀 배치에서는 시드별 검증 또는 더 큰 efSearch/nprobe가 필요하다.
또한 기존 CLIP-512의 ef64 설정을 Qwen-2048에 그대로 이전할 수 없었다.
