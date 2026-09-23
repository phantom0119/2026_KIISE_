# Advanced Ablation Summary

created_at: `2026-07-07T11:16:19.433838+00:00`

## 결론

추가 보강 실험은 새 데이터셋을 무리하게 늘리는 대신, 현재 true multimodal testbed에서 심사 방어력이 큰 세 축을 점검했다.

1. visual encoder ablation: CLIP과 SigLIP을 비교해 결론이 단일 visual encoder에 과적합되지 않는지 확인했다.
2. frame budget ablation: clip당 keyframe 수가 text-to-video와 image-to-video 기능에 미치는 영향을 확인했다.
3. query difficulty stratification: metadata filter가 필요한 medium/strong 질의에서 M4의 개선이 어디서 발생하는지 확인했다.

## Visual Encoder Ablation

| Dataset | Encoder | M4 R@10 | M4 nDCG@10 | M6 R@10 | M6 nDCG@10 | IM1 R@1 | IM1 R@10 | Best RRF | Best Hit@1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| VRU | CLIP ViT-B/32 | 0.2467 | 0.2452 | 0.4928 | 0.6232 | 0.7550 | 0.9800 | RW_t4_v1 | 0.8443 |
| VRU | SigLIP base p16-224 | 0.2442 | 0.2229 | 0.4708 | 0.5826 | 0.8020 | 0.9910 | RW_t4_v1 | 0.8607 |
| AI Hub CCTV | CLIP ViT-B/32 | 0.7524 | 0.7437 | 0.8016 | 0.8951 | 0.8810 | 1.0000 | RW_t4_v1 | 0.9699 |
| AI Hub CCTV | SigLIP base p16-224 | 0.7304 | 0.6846 | 0.7921 | 0.8661 | 0.9145 | 1.0000 | RW_t4_v1 | 0.9774 |

해석: SigLIP은 text-to-video visual-only 성능은 낮지만, metadata prefilter를 결합한 M4와 weighted RRF의 최적 가중치 결론은 유지된다. 반대로 image-to-video에서는 SigLIP이 CLIP보다 높은 R@1을 보인다. 따라서 본 연구의 핵심 결론은 특정 visual encoder의 절대 성능이 아니라 metadata-aware query planning과 evidence selection 구조의 효과로 해석해야 한다.

## Frame Budget Ablation

| Dataset | Task | Budget | R@1 | R@5 | R@10 | MRR | nDCG@10 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| VRU | text-to-video M4 | K=1 seq2 | - | - | 0.2581 | 0.3417 | 0.2499 |
| VRU | text-to-video M4 | K=2 seq1,2 | - | - | 0.2554 | 0.3274 | 0.2505 |
| VRU | text-to-video M4 | K=4 all | - | - | 0.2467 | 0.3153 | 0.2452 |
| VRU | image-to-video IM1 | K=2 seq1,2 | 0.6370 | 0.8860 | 0.9210 | 0.7541 | 0.7938 |
| VRU | image-to-video IM1 | K=4 all | 0.7550 | 0.9660 | 0.9800 | 0.8567 | 0.8875 |
| AI Hub CCTV | text-to-video M4 | K=1 seq2 | - | - | 0.7555 | 0.7628 | 0.7446 |
| AI Hub CCTV | text-to-video M4 | K=2 seq1,2 | - | - | 0.7525 | 0.7408 | 0.7359 |
| AI Hub CCTV | text-to-video M4 | K=4 all | - | - | 0.7524 | 0.7616 | 0.7437 |
| AI Hub CCTV | image-to-video IM1 | K=2 seq1,2 | 0.8141 | 0.9554 | 0.9888 | 0.8782 | 0.9048 |
| AI Hub CCTV | image-to-video IM1 | K=4 all | 0.8810 | 0.9851 | 1.0000 | 0.9258 | 0.9442 |

해석: text-to-video M4는 대표 프레임 1~2개에서도 성능이 크게 무너지지 않는다. 하지만 image-to-video는 질의 프레임을 제외한 같은 clip의 다른 프레임을 찾아야 하므로 K=4가 K=2보다 안정적이다. 이는 운영 시스템에서 text-to-video 색인과 image-to-video 기능의 frame budget을 별도 설계해야 함을 보여준다.

## Query Difficulty Stratification

| Dataset | Encoder | Difficulty | Queries | M2 R@10 | M4 R@10 | Delta R@10 | M2 nDCG@10 | M4 nDCG@10 | Delta nDCG@10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| VRU | CLIP ViT-B/32 | weak | 39 | 0.0266 | 0.0266 | 0.0000 | 0.0897 | 0.0897 | 0.0000 |
| VRU | CLIP ViT-B/32 | medium | 119 | 0.0474 | 0.1675 | 0.1201 | 0.0873 | 0.1941 | 0.1068 |
| VRU | CLIP ViT-B/32 | strong | 86 | 0.0971 | 0.4562 | 0.3591 | 0.0892 | 0.3864 | 0.2973 |
| VRU | SigLIP base p16-224 | weak | 39 | 0.0099 | 0.0099 | 0.0000 | 0.0509 | 0.0509 | 0.0000 |
| VRU | SigLIP base p16-224 | medium | 119 | 0.0209 | 0.1847 | 0.1638 | 0.0371 | 0.1866 | 0.1495 |
| VRU | SigLIP base p16-224 | strong | 86 | 0.0071 | 0.4329 | 0.4258 | 0.0110 | 0.3511 | 0.3400 |
| AI Hub CCTV | CLIP ViT-B/32 | weak | 22 | 0.1289 | 0.1289 | 0.0000 | 0.2333 | 0.2333 | 0.0000 |
| AI Hub CCTV | CLIP ViT-B/32 | medium | 59 | 0.0595 | 0.7963 | 0.7368 | 0.1043 | 0.7647 | 0.6603 |
| AI Hub CCTV | CLIP ViT-B/32 | strong | 52 | 0.1337 | 0.9665 | 0.8328 | 0.1233 | 0.9358 | 0.8125 |
| AI Hub CCTV | SigLIP base p16-224 | weak | 22 | 0.0176 | 0.0176 | 0.0000 | 0.0632 | 0.0632 | 0.0000 |
| AI Hub CCTV | SigLIP base p16-224 | medium | 59 | 0.0406 | 0.7882 | 0.7477 | 0.0599 | 0.7189 | 0.6590 |
| AI Hub CCTV | SigLIP base p16-224 | strong | 52 | 0.0177 | 0.9665 | 0.9488 | 0.0210 | 0.9086 | 0.8876 |

해석: weak 질의는 metadata filter가 없으므로 M2와 M4가 동일하다. 개선은 medium/strong 질의에서 발생하며, 특히 AI Hub CCTV strong 질의에서는 CLIP과 SigLIP 모두 M4 R@10이 0.9665까지 상승한다. 이는 metadata prefilter가 단순 평균 성능 향상이 아니라 구조화 조건이 있는 운영 질의에서 효과를 내는 query planning 기법임을 뒷받침한다.

## 원고 반영 권고

- 본문에는 기존 결과표를 유지하되, 새 표 2개를 추가한다: visual encoder ablation, frame budget ablation.
- difficulty stratification은 지면이 부족하면 논의 문단 또는 부록성 표로 축약한다.
- 결론은 `CLIP이 최고`가 아니라 `metadata-aware retrieval과 weighted evidence selection이 encoder 교체 후에도 유지된다`로 써야 한다.
- K=1이 text-to-video에서 충분해 보인다는 결과를 과장하지 않는다. image-to-video와 service evidence에는 K=4가 더 안정적이다.
