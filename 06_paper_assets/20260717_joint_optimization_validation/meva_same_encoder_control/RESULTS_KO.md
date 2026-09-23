# MEVA 동일 인코더 외부 저장 표현 통제

- corpus: 985 clips, queries: 193, clusters: 57
- encoder: Qwen3-VL-Embedding-2B, 2,048d (query/caption/frame 동일)

Flat/B2 semantic nDCG@10은 caption 0.2827, frame 0.3066,
dual 0.3517였다. Frame-caption 차이는 +0.0239,
질의 bootstrap 95% CI [-0.0053, +0.0535],
activity×facet 군집 bootstrap 95% CI [-0.0292, +0.0813]이다.
Storage-family BH 보정 cluster q-value는 frame-caption 0.4008,
dual-caption <0.0001이다. Dual-caption semantic 차이는
+0.0690, 군집 CI [+0.0369, +0.1004]이다.

MEVA는 clip당 동결 대표 프레임이 하나이므로 multi-frame 저장 효과의 외부 검증이 아니라,
동일 encoder에서 caption 대 frame 표현 효과를 검증하는 실험이다.
