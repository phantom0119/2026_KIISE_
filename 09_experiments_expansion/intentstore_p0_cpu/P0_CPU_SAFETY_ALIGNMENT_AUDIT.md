# P0-C 입력 정합성 감사

> 판정: **`ALIGNMENT_PASS`**

| dataset | queries | clips | qrel outside | clips w/o frames | frames/clip | frame norm | query norm | missing text ranks | exact old-text matches | min cosine |
|---|---:|---:|---:|---:|---|---|---|---:|---:|---:|
| VRU | 85 | 1000 | 0 | 0 | 4–4 | 1.000000–1.000000 | 1.000000–1.000000 | 0 | 15 | 1.000000 |
| AIHUB | 18 | 269 | 0 | 0 | 4–4 | 1.000000–1.000000 | 1.000000–1.000000 | 0 | 0 | n/a |

동일 문구가 과거 CLIP query index에도 존재하는 경우 새 CPU embedding과 기존 embedding의 cosine을 확인했다. AI Hub 비순환 질의는 문구가 모두 바뀌어 exact-text 재현 셀이 없지만 norm·coverage 검사는 통과해야 한다.
