# P0-C 실제 저장량 감사

> 판정: **`STORAGE_AUDIT_PASS`**  
> 기존 파일의 byte 크기만 합산했다. 생성 GPU 비용, DB/FAISS 오버헤드, metadata/lineage 비용은 포함하지 않는다.

| dataset | arm | clips | total GiB | mean KiB/clip | median KiB/clip | p95 KiB/clip | raw/arm |
|---|---|---:|---:|---:|---:|---:|---:|
| AIHUB | raw_video | 269 | 12.9725 | 50567.54 | 42159.61 | 107343.77 | 1.00× |
| AIHUB | fusion_stack | 269 | 0.0504 | 196.56 | 194.37 | 296.86 | 257.26× |
| AIHUB | visual_4frame_stack | 269 | 0.0494 | 192.43 | 190.28 | 292.75 | 262.78× |
| AIHUB | center_frame_stack | 269 | 0.0128 | 49.96 | 51.17 | 73.18 | 1012.14× |
| AIHUB | caption_stack | 269 | 0.0011 | 4.13 | 4.12 | 4.23 | 12246.63× |
| VRU | raw_video | 1000 | 2.9822 | 3127.02 | 2247.97 | 8665.35 | 1.00× |
| VRU | fusion_stack | 1000 | 0.1287 | 134.96 | 132.43 | 193.85 | 23.17× |
| VRU | visual_4frame_stack | 1000 | 0.1240 | 130.05 | 127.56 | 188.71 | 24.04× |
| VRU | center_frame_stack | 1000 | 0.0307 | 32.17 | 31.56 | 46.59 | 97.20× |
| VRU | caption_stack | 1000 | 0.0047 | 4.90 | 4.91 | 5.16 | 637.54× |

## 해석

- `caption_stack`: UTF-8 caption + BGE-M3 float32 vector
- `center_frame_stack`: 중앙 JPEG 1장 + CLIP float32 vector
- `visual_4frame_stack`: JPEG 4장 + CLIP vector 4개
- `fusion_stack`: caption stack + visual 4-frame stack
- 저장 절감 가능성은 시스템 연구의 비용 동기를 확인하지만, 서비스별 표현 비지배성이나 온라인 제어기 이득을 대신 증명하지 않는다.
