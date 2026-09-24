# RDBMS 연계 GraphRAG와 생성 모델 환각 연구 동향 정밀 조사 (2024–2026.7)

## TL;DR
- **RDBMS 위에서 그래프·벡터·SQL을 통합해 환각을 "시스템적으로" 억제·감사하는 방향은 아직 상위 학회에 거의 비어 있는 최적의 진입 지점이다.** DB 학회(SIGMOD/VLDB/CIDR)는 2024→2026 사이 "정확성 보증(accuracy guarantee)"·시맨틱 연산자·벡터-그래프 통합 저장엔진으로 빠르게 이동했고(LOTUS, TigerVector, LEGO-GraphRAG, Palimpzest), NLP/ML 학회(ACL/EMNLP/NeurIPS/Nature)는 환각 탐지(semantic entropy)·abstention·faithfulness로 이동했으나, 두 흐름이 만나는 "DB 제약·프로버넌스 기반 환각 보증"은 미개척이다.
- **GraphRAG가 vanilla RAG 대비 환각을 줄인다는 주장은 조건부로만 참이다.** 복합·다중홉·시간적·추론집약 질의에서는 유의미하게 개선되지만(예: FinanceBench에서 환각 6% 감소·토큰 80% 절감), 단순 단일홉 사실 검색에서는 오히려 vanilla RAG가 우위이며, KG 커버리지가 낮으면 성능이 하락한다(Han et al.의 실측: HotpotQA 65.8%·NQ 65.5%의 정답 엔티티만 구축 KG에 존재).
- **연구실 자산(pgvector/TimescaleDB/DuckDB 테스트베드, 비순환 Tri-Source 평가, false-abstention 경험, 필터드 벡터 검색·VLM-QA 증거 계층)은 세 축의 교차점에 정확히 들어맞는다.** 특히 "관계형 제약·계보를 증거로 삼아 검증가능한 GraphRAG + 근거 기반 선택적 거부(evidence-grounded abstention)"가 DB 학회 주도권을 가질 수 있는 방향이다.

## Key Findings

### 총평: 세 축의 2024→2026 흐름
**축 1(RDBMS 연계 GraphRAG)**은 2024년 개념 정립기(TAG, HybridRAG, Microsoft GraphRAG)를 지나 2025년 DB 학회의 "시스템화" 국면으로 진입했다. 핵심은 (a) 시맨틱 연산자에 통계적 정확성 보증을 붙이는 흐름(LOTUS, PVLDB 2025), (b) 벡터 검색을 그래프 DB/관계형 엔진에 네이티브 통합(TigerVector, SIGMOD 2025; DuckPGQ의 SQL/PGQ), (c) GraphRAG 파이프라인을 모듈화해 설계공간을 탐색(LEGO-GraphRAG, PVLDB 2025)이다. 즉 "새 RAG 알고리즘"보다 "질의 최적화·저장·보증"이라는 DB 고유 무기로 재편되고 있다.

**축 2(환각)**은 2024년 정의·서베이·탐지의 폭발기(semantic entropy가 Nature 게재, RAGTruth·HaluEval·FActScore 확립)를 지나 2025~2026년에는 (a) 탐지의 저비용화(semantic entropy probes, 내부상태 프로브), (b) RAG 특화 환각(context-parametric 지식 충돌, faithfulness vs factuality 구분), (c) abstention/selective answering의 정식 벤치마크화(AbstentionBench, Know Your Limits 서베이)로 세분화됐다. "환각은 완전 제거 불가"라는 인식이 자리잡으며 탐지·거부·근거화로 무게중심이 이동했다.

**축 3(교차점)**은 아직 얇다. DB 학회에서 KG 정확도 추정(Marchesin & Silvello), 시맨틱 무결성 제약(Semantic Integrity Constraints), 데이터 기반 주장 검증(CEDAR) 등 "신뢰성"을 다루는 개별 논문이 등장했으나, 이들을 GraphRAG·환각과 하나의 파이프라인으로 엮은 연구는 거의 없다.

**DB vs NLP 학회의 관심사 대비:** DB 학회는 "정확성 보증·비용·질의 최적화·저장 엔진·감사가능성"을 언어로 삼고(선언적 연산자, 통계적 보장, 프로브 없는 시스템 보증), NLP/ML 학회는 "모델 내부 신호·불확실성·학습/디코딩 개입·벤치마크"를 언어로 삼는다. 환각이라는 동일 문제를 DB는 "데이터·질의의 성질"로, NLP는 "모델의 성질"로 접근한다. 이 간극이 곧 공백이자 기회다.

### 축 1 대표 논문 표 (RDBMS 연계 GraphRAG / 구조화 데이터 RAG)

| 제목 | 제1저자 | 학회/출처 | 연도 | 핵심 기여 | 상태 |
|---|---|---|---|---|---|
| Text2SQL is Not Enough: Unifying AI and Databases with TAG | Asim Biswal & Liana Patel | CIDR | 2025 | NL 질의를 DB 위 LM+질의 통합 패러다임(TAG)으로 일반화; 표준기법 정답률 20% 미만 실증 | 게재확정 |
| Semantic Operators ... Accuracy Guarantees in LOTUS | Liana Patel | PVLDB 18(11):4171–4184 | 2025 | LLM 기반 semantic filter/join/group-by/top-k에 통계적 정확도 보증 부여, 최대 1,000× 최적화(품질은 최신 LLM 파이프라인 대비 최대 170% 초과) | 게재확정 |
| TigerVector: Vector Search in Graph Databases for Advanced RAGs | Shige Liu | SIGMOD 2025, pp.553–565 | 2025 | 그래프 DB(TigerGraph)에 벡터 검색 네이티브 통합, GSQL 확장 hybrid VectorGraphRAG; Neo4j·Neptune·Milvus 대비 우위 | 게재확정 |
| LEGO-GraphRAG: Modularizing Graph-based RAG | Yukun Cao | PVLDB 18(10):3269–3283 | 2025 | GraphRAG 파이프라인을 subgraph추출·path필터·path정제로 모듈화, 설계공간 탐색 | 게재확정 |
| Palimpzest: Optimizing AI-Powered Analytics with Declarative Query Processing | Chunwei Liu | CIDR | 2025 | 비정형 데이터 대상 선언적 AI 분석 질의 + 비용 최적화(Convert/Filter 연산자) | 게재확정 |
| ELEET: Efficient Learned Query Execution over Text and Tables | Matthias Urban | PVLDB 17(13):4867–4880 | 2024 | 텍스트+테이블 학습형 다중모달 연산자, SLM 기반 최대 575× 가속 | 게재확정 |
| DocETL: Agentic Query Rewriting for Complex Document Processing | Shreya Shankar | PVLDB | 2025 | LLM 문서처리 파이프라인의 rewrite directive + 에이전트 평가, 정확도 21–80%↑ | 게재확정 |
| DuckPGQ: Bringing SQL/PGQ to DuckDB | Daniël ten Wolde | PVLDB(demo)/CIDR 2023 | 2023–24 | 분석형 RDBMS(DuckDB)에 SQL:2023 SQL/PGQ 그래프 질의 통합 | 게재확정(기초문헌) |
| HybridRAG: Integrating KGs and Vector RAG | Bhaskarjit Sarmah (BlackRock)·B.Hall/R.Rao/S.Patel(NVIDIA) | ACM ICAIF | 2024 | VectorRAG+GraphRAG 결합, 금융 earnings-call QA에서 개별 대비 검색·생성 모두 우수 | 게재확정 |
| KAG: Boosting LLMs in Professional Domains | Lei Liang (Ant Group) | WWW 2025 (Companion) | 2025 | 스키마 제약 KG + 논리형 유도 하이브리드 추론, 다중홉 F1 19.6–33.5%↑ | 게재확정 |
| From Local to Global: A Graph RAG Approach (Microsoft GraphRAG) | Darren Edge | arXiv 2404.16130 | 2024 | 커뮤니티 요약 기반 글로벌 질의응답 GraphRAG 원형 | 프리프린트 |
| UQE: A Query Engine for Unstructured Databases | Hanjun Dai (Google) | NeurIPS | 2024 | NL 조건 포함 SQL 방언 + 통계적 샘플링 실행 엔진 | 게재확정 |
| RASL: Retrieval Augmented Schema Linking for Massive DB Text-to-SQL | Jeffrey Eben | arXiv 2507.23104 | 2025 | 스키마/메타데이터를 의미단위로 분해·색인해 대규모 DB 스키마 링킹 | 프리프린트 |
| CRUSH4SQL: Collective Retrieval Using Schema Hallucination | Mayank Kothyari | EMNLP | 2023 | 스키마 환각을 브리징 기제로 역이용해 스키마 서브셋 검색 | 게재확정(기초문헌) |
| STaRK: Benchmarking LLM Retrieval on Textual and Relational KBs | Shirley Wu | NeurIPS D&B | 2024 | 텍스트+관계형 결합 KB 상 반정형 검색 벤치마크(3개 도메인) | 게재확정 |
| A Survey of LLM × DATA | Xuanhe Zhou | arXiv 2505.18458 | 2025 | DATA4LLM/LLM4DATA 양방향 관계 종합 서베이 | 프리프린트 |

### 축 2 대표 논문 표 (생성 모델 환각)

| 제목 | 제1저자 | 학회/출처 | 연도 | 핵심 기여 | 상태 |
|---|---|---|---|---|---|
| Detecting hallucinations using semantic entropy | Sebastian Farquhar | Nature 630:625–630 | 2024 | 의미 단위 엔트로피로 confabulation 무감독 탐지 | 게재확정 |
| Semantic Entropy Probes | Jannik Kossen | arXiv 2406.15927 | 2024 | 은닉상태에서 단일 패스로 semantic entropy 근사, 5–10× 비용 절감 | 프리프린트 |
| RAGTruth: A Hallucination Corpus for Trustworthy RAG | Cheng Niu | ACL | 2024 | RAG 응답 단어수준 환각 약 18k 주석 코퍼스, 4유형 분류 | 게재확정 |
| Long-form factuality (SAFE/LongFact) | Jerry Wei | arXiv 2403.18802 | 2024 | 장문 사실성 프롬프트셋(LongFact)+에이전트 검증(SAFE) | 프리프린트 |
| WildHallucinations | (Zhao et al.) | arXiv 2407.17468 | 2024 | 실사용 엔티티 기반 장문 사실성, 엔티티 52%는 Wikipedia無 | 프리프린트 |
| FactBench: Dynamic In-the-Wild Factuality | Farima Fatahi Bayat | arXiv 2410.22257 | 2024 | 실대화 유래 동적 사실성 벤치마크 | 프리프린트 |
| Know Your Limits: A Survey of Abstention in LLMs | Bingbing Wen | TACL | 2025 | query/model/human-value 3관점 abstention 프레임워크 서베이 | 게재확정 |
| AbstentionBench: Reasoning LLMs Fail on Unanswerable Questions | Polina Kirichenko (Meta) | arXiv 2506.09038 | 2025 | 20개 데이터셋·35k+ unanswerable 질문·20개 frontier LLM 평가; abstention은 미해결이며 추론 파인튜닝이 abstention 평균 24%↓ | 프리프린트 |
| Do LLMs Know When to NOT Answer? (Abstain-QA) | Nishanth Madhusudhan | COLING | 2025 | abstention 능력 정량화 벤치마크(AUCM) | 게재확정 |
| Lookback Lens: Contextual hallucination via attention maps | Yung-Sung Chuang | EMNLP | 2024 | 어텐션맵만으로 맥락 환각 탐지·완화 | 게재확정 |
| INSIDE: LLMs' internal states retain power of hallucination detection | Chao Chen | arXiv 2402.03744 | 2024 | 내부상태 공분산 고유값으로 환각 탐지 | 프리프린트 |
| GraphEval: KG-Based Hallucination Evaluation | Hannah Sansford | KiL@KDD | 2024 | LLM 출력을 KG triple로 분해해 NLI로 환각 탐지·교정(GraphCorrect) | 게재확정(워크숍) |
| FaithEval | Chaowei Xiao 그룹(Ming et al.) | ICLR | 2025 | 반사실/불가답/불일치 맥락 하 faithfulness 평가 | 게재확정(초록 기준) |
| Self-RAG | Akari Asai | ICLR | 2024 | reflection token으로 검색·자기비판 통합 | 게재확정 |
| CRAG: Corrective RAG | Shi-Qi Yan | arXiv 2401.15884 | 2024 | 검색 품질 평가 후 교정 검색 | 프리프린트 |
| FaithfulRAG | Qinggang Zhang | ACL | 2025 | 사실수준 충돌 모델링+self-thinking으로 맥락 충실성 개선 | 게재확정 |
| Can Knowledge Graphs Reduce Hallucinations? A Survey | Garima Agrawal | NAACL | 2024 | KG의 환각 완화 기여를 유형화한 서베이 | 게재확정 |
| Hallucination Detection on a Budget (Bayesian SE) | Kamil Ciosek 외 | arXiv 2504.03579 | 2025 | 베이지안 semantic entropy로 53% 샘플로 동일 AUROC | 프리프린트 |
| A Survey on Hallucination in LLMs | Lei Huang | ACM TOIS | 2025 | 환각 정의·원인·탐지·완화 종합 서베이 | 게재확정 |
| RAG vs. GraphRAG: A Systematic Evaluation | Haoyu Han (Michigan State Univ., 12인) | arXiv 2502.11371 | 2025 | GraphRAG는 다중홉·시간적·추론집약 질의서 최대 20+점 우위, 단순 단일홉(NQ)선 vanilla RAG 우위; KG 커버리지 한계 실증 | 프리프린트 |
| SafeRAG: security benchmark for RAG | Xun Liang 외 | arXiv | 2025 | RAG 4대 공격(노이즈·충돌·소프트광고·DoS) 벤치마크 | 프리프린트 |

### 축 3 대표 논문 표 (DB 시스템 관점의 환각 억제/신뢰 GraphRAG)

| 제목 | 제1저자 | 학회/출처 | 연도 | 핵심 기여 | 상태 |
|---|---|---|---|---|---|
| Efficient and Reliable Estimation of Knowledge Graph Accuracy | Stefano Marchesin | PVLDB 17(9):2392–2404 | 2024 | 표본 기반 KG 정확도 추정을 신뢰성 있는 추정량으로 개선(Wald 대체) | 게재확정 |
| Credible Intervals for KG Accuracy Estimation | Stefano Marchesin | PACMMOD 3(3), SIGMOD | 2025 | 베이지안 credible interval(aHPD)로 최소폭·보증된 KG 정확도 감사 | 게재확정 |
| Semantic Integrity Constraints: Declarative Guardrails for AI-Augmented Data | Alexander W. Lee | PVLDB 18(11):4073–4080 | 2025 | LLM 데이터 파이프라인용 선언적 정확성 가드레일 | 게재확정 |
| CEDAR: Cost-Efficient Data-Driven Claim Verification | Tharushi Jayasekara | PVLDB 18(11):4492–4504 | 2025 | 데이터 기반 주장 검증 시스템 | 게재확정 |
| Fact Verification in Knowledge Graphs Using LLMs (FactCheck) | Stefano Marchesin 외 | SIGIR | 2025 | LLM으로 KG 내 사실 검증하는 웹 플랫폼 | 게재확정 |
| D-Bot: Database Diagnosis System using LLMs | Xuanhe Zhou | PVLDB 17(10):2514–2527 | 2024 | 검증가능 참조 포함 DB 진단 리포트 자동 생성(SIGMOD'25 데모로 확장) | 게재확정 |
| Trustworthy and Efficient LLMs Meet Databases | Kyoungmin Kim (EPFL) | arXiv 2412.18022 (튜토리얼) | 2024 | DB 기법으로 환각 저감·효율화하는 LLM↔DB 통합 비전/튜토리얼 | 프리프린트/튜토리얼 |
| Database Perspective on LLM Inference Systems | James Pan | PVLDB 18(12):5504–5507 | 2025 | LLM 추론 시스템을 DB 관점에서 정리(튜토리얼) | 게재확정 |
| LLM for Data Management | Guoliang Li | PVLDB 17(12):4213–4216 | 2024 | LLM의 환각·비용·저정확도 문제를 데이터관리 관점서 조망(비전) | 게재확정 |
| TruthfulRAG: Resolving Factual-level Conflicts with KGs | (Zhang et al.) | arXiv 2511.10375 | 2025 | 검색 내용서 triple 추출·엔트로피 필터로 지식충돌 해소 | 프리프린트 |
| KGR: Mitigating Hallucinations via KG-based Retrofitting | Xinyan Guan | AAAI | 2024 | 추론 중 KG로 초안을 자동 검증·교정 | 게재확정 |

### 공백(Gap) 분석 — 세 축의 교차 영역
1. **관계형 제약·계보 기반 환각 감사(database-grounded auditability)의 부재.** DB에는 프로버넌스/lineage(SmokedDuck·DuckDB), 무결성 제약이 있으나, 이를 GraphRAG 증거 패킷의 출처 추적·검증에 결합한 상위 학회 논문이 없다. Semantic Integrity Constraints·CEDAR가 "가드레일/주장검증"을 열었지만 GraphRAG·다중홉 근거와는 미연결.
2. **pgvector/PostgreSQL·Apache AGE 기반 GraphRAG 저장·서빙 계층의 학술 부재.** 서브에이전트 확인 결과, 상위 DB 학회에 pgvector/AGE 기반 GraphRAG 저장엔진 논문이 없다(산업 블로그만 존재). TigerVector는 그래프 DB, DuckPGQ는 분석 RDBMS로, "관계형 OLTP+pgvector+그래프 확장"의 통합 서빙은 비어 있음.
3. **비순환(non-circular) 평가로 "GraphRAG가 환각을 줄이는가"를 엄밀 측정한 연구 부족.** 현재 근거는 산업 벤치마크(FinanceBench 6% 감소) 또는 프리프린트에 산재하며, 평가 오염(LLM 심판이 생성·평가 동시)이 통제되지 않음. 연구실의 Tri-Source 방법론이 정확히 이 공백을 겨냥.
4. **근거 기반 선택적 거부(evidence-grounded abstention)와 GraphRAG의 결합 부재.** abstention 연구(AbstentionBench)와 GraphRAG 연구가 분리돼 있음. "그래프 경로/관계형 제약으로 근거가 불충분하면 거부"하는 false-abstention 통제형 시스템은 미개척.
5. **NL2SQL·테이블QA의 실행 기반 검증(execution-grounded verification)과 스키마 환각의 통합 처리 부재.** 스키마 환각(CRUSH4SQL)·스키마 링킹 연구는 많으나, SQL 실행 결과·제약 위반을 환각 신호로 삼아 응답을 검증·거부하는 폐루프는 얇다.
6. **필터드 벡터 검색의 정확도-환각 인과 정량화 부재.** 메타데이터 필터가 검색 품질과 환각률에 미치는 인과를 DB 질의 최적화 관점에서 측정한 연구가 없음.

### 차기 연구 방향 후보

**후보 1 — "Provenance-Grounded GraphRAG: 관계형 계보를 증거로 삼는 검증가능 RAG"**
- *정의:* RDBMS 외래키 그래프+pgvector 위에서 GraphRAG를 서빙하되, 모든 응답 문장을 SQL 프로버넌스(lineage)와 무결성 제약으로 역추적·검증하는 증거 계층을 표준화한다.
- *왜 지금:* Semantic Integrity Constraints(PVLDB 2025)·CEDAR·KG 정확도 추정(Marchesin & Silvello)이 등장했고, TigerVector·LEGO-GraphRAG로 벡터-그래프 통합이 성숙. 프로버넌스는 DB 고유 무기.
- *가장 가까운 선행과 차별점:* HybridRAG/KAG는 근거 추적을 명시적 제약·계보로 보증하지 않음; 본 방향은 "출처 추적가능성"을 시스템 계약으로 삼음.
- *연구실 접합점:* pgvector 테스트베드 + VLM-QA 증거 계층 + 필터드 벡터 검색.
- *타깃 학회:* SIGMOD/PVLDB(스케일드 데이터·시스템 트랙), CIDR(비전).
- *리스크:* 프로버넌스 오버헤드, 자연어→triple 매핑의 정확도 병목.

**후보 2 — "비순환 Tri-Source 평가로 GraphRAG의 환각 억제 효과를 인과적으로 규명"**
- *정의:* 파라메트릭 지식·벡터 검색·그래프 경로를 분리한 비순환 워크로드로, GraphRAG가 vanilla RAG 대비 환각을 언제·왜 줄이는지(또는 늘리는지)를 KG 커버리지·질의 유형별로 정량화.
- *왜 지금:* Han et al.의 "RAG vs GraphRAG"(arXiv 2502.11371)가 다중홉선 GraphRAG 우위·단일홉선 vanilla 우위 및 KG 커버리지 한계(HotpotQA 65.8%·NQ 65.5%)를 지적했으나 평가 오염 통제가 없음. 표준 벤치마크 부재.
- *가장 가까운 선행과 차별점:* WildGraphBench/GraphRAG-Bench는 성능 위주; 본 방향은 "환각 인과"와 "평가 비순환성"이 핵심.
- *연구실 접합점:* 비순환 Tri-Source 방법론 + false-abstention 경험.
- *타깃 학회:* VLDB(실험·분석 트랙), EMNLP/NAACL(리소스·평가).
- *리스크:* KG 구축 품질이 교란변수, 데이터셋 라이선스.

**후보 3 — "Evidence-Grounded Abstention over Structured Data: 근거 부족 시 거부하는 GraphRAG"**
- *정의:* 그래프 경로·관계형 제약으로 근거 충분성을 정량화해, 불충분하면 거부하되 false-abstention(과잉 거부)을 통제하는 선택적 응답 계층.
- *왜 지금:* AbstentionBench(Kirichenko et al., Meta)가 abstention을 "미해결"로 규정하고 추론 파인튜닝이 abstention을 평균 24% 떨어뜨림을 보고; 근거 기반 거부는 RAG의 자연스러운 확장이나 구조화 데이터엔 미적용.
- *가장 가까운 선행과 차별점:* 기존 abstention은 모델 불확실성 기반; 본 방향은 "DB 증거 충분성" 기반 거부로 프레임 전환.
- *연구실 접합점:* false-abstention 연구 + 필터드 벡터 검색 + 증거 계층.
- *타깃 학회:* ACL/EMNLP(주 트랙) 또는 SIGMOD(시스템), SIGIR.
- *리스크:* 순수 NLP 색채가 강해질 수 있어 DB 기여 명확화 필요.

**후보 4 — "Execution-Grounded NL2SQL 검증: 실행 결과·제약 위반을 환각 신호로"**
- *정의:* NL2SQL/TableQA에서 SQL 실행 결과, 제약 위반, 스키마 링킹 신뢰도를 결합해 응답을 검증하고 환각 시 거부/재생성하는 폐루프.
- *왜 지금:* 스키마 환각(CRUSH4SQL)·스키마 링킹 연구는 성숙했으나 실행 기반 검증 폐루프는 얇음; TAG가 "Text2SQL만으론 부족"을 실증.
- *가장 가까운 선행과 차별점:* Self-RAG/CRAG는 텍스트 검색 교정; 본 방향은 "SQL 실행 시맨틱스"를 검증 신호로.
- *연구실 접합점:* DuckDB/PostgreSQL 테스트베드 + 비순환 평가.
- *타깃 학회:* SIGMOD/VLDB, ICDE.
- *리스크:* 벤치마크(BIRD/Spider) 포화, 신규성 확보 필요.

**후보 5 — "필터드 벡터 검색의 환각 인과 최적화"**
- *정의:* 메타데이터/제약 조건 필터가 검색 recall·정밀도와 환각률에 미치는 인과를 DB 질의 최적화 관점에서 모델링, 환각 최소화 실행계획을 선택.
- *왜 지금:* pgvector·필터드 ANN이 성숙했고 "The Power of Noise"(SIGIR 2024)가 검색 품질↔환각 관계를 부각. 최적화 관점은 미개척.
- *가장 가까운 선행과 차별점:* LOTUS는 정확도 보증을 연산자에 부여; 본 방향은 "필터드 벡터 검색→환각"의 인과에 특화.
- *연구실 접합점:* 필터드 벡터 검색·TimescaleDB(시계열 필터)·비순환 평가.
- *타깃 학회:* VLDB/SIGMOD, SIGIR.
- *리스크:* 인과 식별의 통계적 엄밀성 확보 난이도.

## Details

**축 1 심화.** TAG(Biswal & Patel, CIDR 2025)는 Text2SQL(관계대수로 표현 가능한 질의)과 RAG(소수 레코드 점검색)를 모두 특수사례로 포섭하는 일반 패러다임을 제시하고, 표준기법이 20% 미만만 정답을 낸다는 점을 실증해 연구 여지를 열었다. LOTUS(Patel, PVLDB 18(11):4171–4184)는 semantic filter/join/group-by/top-k에 통계적 정확도 보증(목표 정확도 γ, 허용오차 확률)을 부여하는 최초의 형식론으로, 최적화로 이들 연산을 최대 1,000× 가속하면서 최신 LLM 분석 파이프라인 품질을 최대 170% 초과했다 — "정확성 보증"이라는 DB식 언어를 환각 문제에 도입한 사실상의 앵커다. TigerVector(Shige Liu, SIGMOD 2025, pp.553–565)는 그래프 DB에 벡터 검색을 네이티브 통합해 Neo4j·Neptune·Milvus 대비 우위를 보고했다. LEGO-GraphRAG(Yukun Cao, PVLDB 18(10):3269–3283)는 GraphRAG를 subgraph추출·path필터·path정제 3모듈로 분해해 추론품질·런타임·토큰비용의 트레이드오프를 실증했다. DuckPGQ(ten Wolde, CIDR 2023 → PVLDB demo)는 SQL:2023의 SQL/PGQ를 DuckDB에 구현해 관계형 엔진 위 그래프 질의를 표준화했다 — 연구실 DuckDB 자산과 직접 접합.

**축 2 심화.** Farquhar et al.(Nature 630:625–630, 2024)의 semantic entropy는 토큰이 아닌 의미 단위 클러스터의 엔트로피로 confabulation을 무감독 탐지해 환각 탐지의 방법론적 표준이 됐고, 후속으로 Semantic Entropy Probes(Kossen, 2024)가 은닉상태 단일패스로 5–10× 비용을 절감했다. RAGTruth(Niu, ACL 2024)는 약 18,000개 RAG 응답에 단어수준 환각을 주석해 "evident/subtle × conflict/baseless" 4유형 분류를 확립했다. Abstention은 Know Your Limits 서베이(Wen, TACL 2025)가 query/model/human-value 3관점으로 정리했고, AbstentionBench(Kirichenko et al., Meta, arXiv 2506.09038)는 20개 데이터셋·35k+ unanswerable 질문에서 20개 frontier LLM을 평가해 abstention이 "미해결 문제이며 모델 스케일링이 거의 도움이 되지 않는다"고 결론지었으며, 추론 파인튜닝이 오히려 abstention을 평균 24% 떨어뜨린다고 보고했다 — 연구실의 false-abstention 경험과 직접 연결.

**축 3 심화 및 GraphRAG의 환각 억제 실증.** Barry et al.(GenAIK@COLING 2025, pp.54–65)는 FactRAG/HybridRAG로 FinanceBench에서 환각 6% 감소·토큰 사용 80% 절감을 보고했다. 반면 Han et al.의 "RAG vs. GraphRAG"(arXiv 2502.11371)는 KG 기반 GraphRAG가 HotpotQA에서 정답 엔티티의 65.8%, NQ에서 65.5%만 구축 KG에 포함돼 성능이 하락할 수 있음을 지적하고, GraphRAG는 다중홉·시간적·추론집약 질의에서 최대 20점 이상 우위지만 단순 단일홉 사실 질의(NQ)에서는 vanilla RAG가 우위임을 실증했다. 즉 GraphRAG의 환각 억제는 질의 유형·KG 커버리지에 강하게 의존한다. DB 쪽에서는 Marchesin & Silvello가 KG 정확도 추정을 PVLDB 2024(신뢰성 있는 추정량)·PACMMOD 2025(베이지안 credible interval)로 정식화했고, Semantic Integrity Constraints(PVLDB 2025)·CEDAR(PVLDB 2025)가 LLM 데이터 파이프라인의 검증·가드레일을 열었다.

## Recommendations

**1단계(0–3개월) — 후보 2 + 후보 1의 측정 인프라 선점.** 연구실의 비순환 Tri-Source 방법론으로 "GraphRAG의 환각 억제 인과"를 pgvector/DuckDB 테스트베드에서 측정하는 평가 프레임을 먼저 확립하라. 이는 리스크가 낮고(데이터·시스템 자산 재활용), VLDB 실험 트랙/EMNLP 리소스로 빠르게 산출 가능하며, 이후 후보 1(프로버넌스 GraphRAG)의 기반이 된다. *진행 기준:* KG 커버리지·질의유형별 환각률 곡선을 재현 가능하게 확보하면 후보 1으로 확장.

**2단계(3–9개월) — 후보 1(Provenance-Grounded GraphRAG)에 집중.** DB 학회 주도권이 가장 확실한 방향. Semantic Integrity Constraints·CEDAR를 선행으로 인용하되, "GraphRAG 증거 패킷의 계보 추적+제약 검증"을 시스템 계약으로 제시. *진행 기준:* 프로버넌스 오버헤드가 질의 지연의 일정 배수 이내로 유지되고, 근거 추적으로 환각률이 통계적으로 유의하게 감소하면 SIGMOD/PVLDB 제출.

**3단계(병행) — 후보 3(Evidence-Grounded Abstention)으로 교차 성과.** false-abstention 경험을 살려 "근거 충분성 기반 거부"를 후보 1/2 위에 얹어라. 단, DB 기여(증거 충분성의 질의 최적화적 정의)를 명확히 해 순수 NLP로 흐르지 않도록 하라. *임계값:* false-abstention이 통제된 상태에서 환각률-거부율 파레토가 기존 abstention 기법을 지배하면 ACL/EMNLP 제출.

**보류 권고:** 후보 4·5는 벤치마크 포화(BIRD/Spider)와 인과 식별 난이도 때문에 후속으로 미루되, 후보 1/2의 부산물로 자연히 확보되면 spin-off하라.

## Caveats
- **프리프린트 다수:** Microsoft GraphRAG(2404.16130), CRAG, AbstentionBench, RAG-vs-GraphRAG(2502.11371, Han et al./Michigan State), TruthfulRAG, A Survey of LLM×DATA 등은 arXiv 프리프린트로, 심사 상태가 미확정이다. 표에 상태를 명시했다.
- **게재처 미확정:** "Trustworthy and Efficient LLMs Meet Databases"(2412.18022, Kim & Ailamaki)는 튜토리얼 성격으로 정확한 학회 슬롯 미확인. AnDB는 SIGMOD 2025 데모로 추정되나 공식 데모 목록서 미확인. FaithEval의 ICLR 2025 게재 및 일부 서베이 게재처는 초록·인용 기준.
- **산업 수치 주의:** "환각 62% 감소" 등 일부 수치는 산업 블로그·비피어리뷰 출처로, 재현 조건이 불명확하다. FinanceBench 6% 감소·토큰 80% 절감은 GenAIK 워크숍(피어리뷰, Barry et al.) 출처로 상대적으로 신뢰.
- **저자 표기 불완전:** 일부 표의 제1저자는 초록/인용에서 확인한 것으로, TAG(Biswal·Patel 공동 제1)·LEGO-GraphRAG(Cao·Gao 공동 제1)처럼 공동 제1저자가 있을 수 있다. 괄호 표기(예: Zhao et al.)는 제1저자 확정이 미완인 항목이다.
- **pgvector GraphRAG 저장엔진 공백:** 서브에이전트가 상위 DB 학회서 확인 실패했으나, 부재의 증명은 아니며 워크숍·최신 프리프린트에 존재할 가능성은 배제 못한다.
- **검색 예산 제약:** 웹 검색 예산 소진으로 SQL:2023 property graph 최신 사례, ALCE/citation-attribution 벤치마크, Apache AGE 기반 사례의 직접 확인은 미완이며 후속 확인이 필요하다.