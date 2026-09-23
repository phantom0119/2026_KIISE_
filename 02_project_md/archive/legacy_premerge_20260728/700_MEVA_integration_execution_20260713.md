# 700 — MEVA(WACV 2021) tri-source 통합 실행 로그 (2026-07-13)

상태: **소스분리·비순환(A6) 구조 검증 DONE(실데이터), 문서채널(VLM 캡션)만 GPU-대기.** 690 조사에서 채택한 해외 외적타당성 arm(MEVA)을 522와 동일 규약으로 통합 착수.

역할: **fit-2 외적타당성 arm** — 522 헤드라인(비순환 tri-source, prefilter 가치×결합도)의 국제 재현. 제2 헤드라인 아님(predicate가 522의 독립 신호센서 CSV가 아니라 capture 메타데이터라, 소스분리는 성립하나 분석자가 설계한 분리).

## 확보 (완료)
- 주석: Kitware GitLab `meva-data-repo` shallow-clone → `Datasets/external/meva/meva-data-repo/` (7.6G). KPF `annotation/DIVA-phase-2/MEVA/kitware-meva-training/<date>/<hour>/<clip>.{activities,geom,types}.yml`.
- 영상: 공개 S3 `s3://mevadata-public-01/drops-123-r13/<date>/<hour>/<clip>.r13.avi` (무서명 https, 한국 OK, CC-BY-4.0). 클립당 ~150–190MB(5분 HD 1920×1080). **avi는 프레임 추출 후 삭제** → 저장은 JPG만.
- 라이선스 재확인: CC-BY-4.0(NC·ND 없음) → 파생 VLM 캡션 재배포 합법.

## 파이프라인 (신규 스크립트 3종, 522 미러)
| 스크립트 | 역할 | 상태 |
|---|---|---|
| `build_meva_facets.py` | KPF 파싱 → clips + **predicate**(capture meta) + **relevance**(37 활동) facet + 결합도 | ✅ 실행 |
| `build_meva_trisource_canonical.py` | canonical(clips/documents/metadata/queries/qrels strict+semantic) + **A6 감사** | ✅ 구조 PASS(`--allow-no-doc`) |
| `build_meva_captions.py` | 문서채널: avi 다운→cv2 중간프레임→삭제→Qwen2.5-VL 캡션(추출/캡션 2-phase, 샤딩, resume) | 프레임추출 진행중, 캡션=GPU대기 |

산출: `Datasets/processed/meva_kf1/20260713/{clips,activity_presence,predicate_facets}.parquet`, `meva_independence.json`, `canonical_trisource/`, `frames/`, `captions/`.

## 소스분리 매핑 (비순환 핵심)
- **PREDICATE** = capture 메타데이터(time_of_day·location·hour, +camera context) — 파일명/clip-camera-time-table. producer=녹화리그. `facet_source=meva_capture_metadata`.
- **RELEVANCE** = DIVA 사람 활동주석 37클래스(희소 활동=헤드라인). producer=사람주석. `facet_source=meva_diva_activity`.
- **DOCUMENT** = VLM 캡션(픽셀만). producer=VLM. (GPU 대기)
- **규율**: 활동라벨은 relevance 전용, predicate 재주입 금지. UAV(이동) 제외.

## 실측 수치 (실데이터)
- 코퍼스 **1,443 주석클립**(961 활동≥1); 위치 school 711/bus 417/hospital 187/admin 128; 24 카메라.
- 관계 정의 **19 희소활동**(밀도 1.5–12%: person_loads_vehicle·vehicle_makes_u_turn·person_purchases…).
- **202 질의 전부 low-coupling(V<0.3, maxV=0.2138)** — 522(maxV 0.454)보다 더 깨끗한 분리. strict qrels 4,899 / semantic 19,714.
- **A6 구조 감사 6/6 PASS**: filter=capture-predicate ✓ / relevance=activity ✓ / **filter∩relevance disjoint ✓** / metadata에 relevance 없음 ✓ / 세 producer 분리 ✓ / relevance 희소(min<5%) ✓. (document_token_leak = 캡션 후 판정)

## 남은 단계 (GPU 여유 시 — task #18)
```bash
PY=Datasets/envs/kiise-vlmdb/bin/python
# 1) 프레임 추출: 현재 300-clip 백그라운드(extract_300.log). 전체는:
$PY 2026_KIISE/scripts/build_meva_captions.py --extract-only --n-clips 0
# 2) 캡션 (2-GPU 샤딩)
$PY 2026_KIISE/scripts/build_meva_captions.py --caption-only --device cuda:0 --shard 0/2 &
$PY 2026_KIISE/scripts/build_meva_captions.py --caption-only --device cuda:1 --shard 1/2 &
# 3) 병합 → 문서
$PY 2026_KIISE/scripts/build_meva_captions.py --merge-only
# 4) 전체 A6 (document 누출 감사 포함) → overall_pass=True 기대
$PY 2026_KIISE/scripts/build_meva_trisource_canonical.py
# 5) CLIP 임베딩 + B0–B5 검색 베이스라인 + 색인벤치 → 522 외적타당성 재현
```
현 상태: 프레임추출 PID 진행중(~1 clip/40s, 300≈3.3h; 전체 1443≈16h·245GB transfer, avi 즉시삭제). GPU 2장 busy(캡션 대기).

## 정직 한계
- predicate=capture 메타(카메라/시간/장소)는 522의 독립 신호센서 CSV와 달리 물리 계측기가 아님 → 소스분리는 성립하나 "제2 헤드라인" 아님(외적타당성 한정).
- kitware-meva-training(1,443)만 사용; kitware/·nist-kf1-json/ 추가 주석은 후속 확장 가능.
- modality 전부 EO(IR 클립은 이 subset에 없음) → modality predicate 폐기(522의 is_weekend와 동일 처리).
- 캡션 커버리지: 우선 300-clip 문서채널로 full A6 PASS 목표, 이후 스케일. 코퍼스=캡션된 클립.

---

# ⭐ 실행 결과 — 문서채널 완성 + 전체 A6 PASS + B0–B5 (파일럿, 2026-07-13) — ⚠️ SUPERSEDED (아래 스케일 결과가 정본; semantic B4−B2 유의성은 소표본 아티팩트로 판명)

프레임추출 8-shard 병렬(276/300 성공, 24 실패=구성 S3키 부재) → Qwen2.5-VL 2-GPU 캡션 276개(anti-leak 위반 0, 평균 501자, 픽셀-only 장면서술) → merge → **canonical FULL 재빌드**.

## 전체 A6 비순환 감사 = PASS (7/7)
`canonical_trisource/A6_trisource_audit.json`: filter=capture-predicate ✓ / relevance=activity ✓ / **filter∩relevance disjoint ✓** / metadata에 relevance 無 ✓ / 세 producer 분리 ✓ / relevance 희소 ✓ / **document_token_leak_zero=0 ✓**. 코퍼스 276, 질의 73(low 71/contrast 2), qrels strict 583 / semantic 1,563. bge-m3 1024-dim.

## B0–B5 (bge-m3, `results/meva_bgem3_b0_b5/`)
| strategy | strict nDCG@10 | semantic nDCG@10 |
|---|---:|---:|
| B0 metadata-only | 0.172 | 0.134 |
| B1 BM25 | 0.086 | 0.209 |
| **B2 vector(dense)** | **0.037** | **0.097** |
| B3 vector+postfilter | 0.166 | 0.137 |
| B4 prefilter+vector | 0.166 | 0.137 |
| B5 hybrid | **0.177** | 0.145 |

**B4−B2 (semantic nDCG@10, paired bootstrap 5000):** all n=73 **Δ=+0.0394 CI[+0.010,+0.068] (0 배제)**, sign 17/17/39; low-coupling n=71 **+0.0371 CI[+0.008,+0.066]**; contrast n=2 +0.120(참고).

## 정직 해석 — 522의 확장(반박 아님)
- **재현된 것**: strict에서 **B0 metadata(0.172) ≫ B2 dense(0.037)** — 약한 dense를 metadata/prefilter가 압도(522 동일 구조). dense가 약한 이유 = **VLM 캡션이 미세 DIVA 활동(person_reads_document·vehicle_reverses 등)을 거의 서술 못 함** = 522 "캡션 문서 맹점(주차 미서술)"과 동형.
- **다른 것**: 522 저결합 arm은 soft-intent에서 prefilter가 **HURT(−0.099)**였으나 MEVA는 **HELP(+0.037)**. 기전(해석) = base retriever(B2 dense)가 매우 약하면 prefilter의 **distractor 제거** 효과가 **relevant 제거** 효과를 압도 → prefilter 부호가 **결합도(522축)뿐 아니라 base-retriever 강도에도 의존**. ⇒ "soft-intent prefilter 가치는 결합도가 결정" 헤드라인에 **2번째 축(문서채널이 relevance 의미를 담는 정도)**을 추가하는 확장.
- **한계**: 276-clip 파일럿(1,443 annotated의 subset), 73질의, CI 겨우 0 배제 → **전체 스케일 재확인 필요**. contrast=2질의(참고용). 기전 주장은 해석(추가검증: dense를 강화한 조건에서 부호 반전 여부 테스트).

## 다음 (firm-up)
전체 annotated(961 활동클립 또는 1,443) 캡션으로 스케일 → 질의 ~200+, B4−B2 재추정 + 결합도×retriever-강도 2D 표. 커맨드는 `--n-clips 0`(전체 추출, ~245GB transfer/~1.5h). 색인구조 벤치(Flat/IVF/HNSW/PQ)는 MEVA 임베딩으로 선택 실행 가능하나 MEVA의 주역할은 검색 tri-source 외적타당성(색인-스케일은 522 sinnaedoro 132K가 담당).

---

# ⭐⭐ 확정 결과 — 961 활동클립 스케일업 (985 corpus, 193 질의, 2026-07-13)

파일럿을 전체 활동클립으로 확장(8-shard 추출 985프레임 73분 + Qwen2.5-VL 2-GPU 캡션 985개 36분, `--with-activity-only`). **전체 A6 재검증 PASS(7/7): corpus 985, 질의 193(low 191/contrast 2), strict 4,405 / semantic 17,205 qrels, document_token_leak=0.** 무인 드라이버 `scale_driver.log`, `results/meva_bgem3_b0_b5/`.

## B0–B5 (985 clips, 193 q)
| strategy | strict nDCG@10 | semantic nDCG@10 |
|---|---:|---:|
| B0 metadata-only | **0.144** | 0.138 |
| B1 BM25 | 0.047 | 0.173 |
| **B2 vector(dense)** | **0.027** | 0.103 |
| B3 vector+postfilter | 0.117 | 0.112 |
| B4 prefilter+vector | 0.120 | 0.114 |
| B5 hybrid | 0.125 | 0.118 |

**B4−B2 (semantic nDCG@10, paired bootstrap 5000):** all n=193 **Δ=+0.0115 CI[−0.010,+0.033] — 0 포함(비유의)**, sign 54/62/77; low-coupling n=191 +0.0114 CI[−0.010,+0.032] (0 포함). **strict B4−B2 ≈ +0.093**(B4 0.120 vs B2 0.027).

## 확정 해석 (파일럿 자기교정 — 정본)
- **파일럿 semantic B4−B2 "+0.039 (CI 0 배제)"는 소표본(n=73) 아티팩트 → 스케일에서 +0.011·CI 0 포함으로 소멸.** 522가 original-32(−0.075)→기계적 확장(n.s.)에서 겪은 자기교정과 **동일 메타패턴**(작은 표본의 명목 유의가 스케일에서 사라짐).
- **강건하게 국제 재현된 것 (= MEVA 외적타당성 기여):**
  1. **strict(hard 제약) prefilter 이득**: B4 0.120 ≫ B2 0.027 (Δ≈+0.093) — 522 "hard constraint에서 유의 이득" 재현.
  2. **metadata ≫ 약한 dense (strict)**: B0 0.144 ≫ B2 0.027 — 522 "strict B0>B2" 재현.
  3. **VLM 캡션 문서 맹점**: B2 dense가 미세 DIVA 활동을 거의 못 잡음(strict 0.027) — 522 "주차 미서술 맹점"과 동형(미세 활동).
  4. **soft-intent·독립predicate에서 prefilter는 robust 효과 없음(≈0)** — 522 refined 결론(저결합 soft 효과는 쌍-클러스터 부트스트랩에서 0 포함=탐색적)과 **일치**. MEVA(국제·타도메인·타주석)가 522의 정직한 refined 결론을 독립 재현.
- **정정(철회)**: 파일럿의 "retriever-강도 2번째 축이 prefilter 부호를 +로 만든다" 해석은 효과가 스케일에서 null이 되어 **철회**. 남는 강건 축 = (i) 제약 성격 hard/soft, (ii) 문서채널이 relevance를 담는 정도(캡션 맹점).

## 종합 판정
MEVA는 522 헤드라인의 **강건한 부분을 국제적으로 재현**(strict prefilter 이득 / metadata≫weak-dense / 캡션 맹점)하고 **취약한 부분(soft-intent 저결합 효과)이 null임을 독립 확인**해 522의 refined 결론을 지지. 비순환 tri-source 프로토콜이 해외·타도메인·타주석에서 **기계감사 A6 PASS로 이식 가능**함을 입증 → **fit-2 외적타당성 arm으로 논문 반영 가능**. (추가 선택지: 색인구조 벤치를 MEVA 임베딩으로 실행 / 전체 1,443으로 빈-클립 hard-negative 추가 / 사람검증은 불요.)
