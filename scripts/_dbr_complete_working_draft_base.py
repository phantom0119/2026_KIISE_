#!/usr/bin/env python3
"""Build the complete DBR review draft as a two-column Word document.

The validated v3 manuscript remains the numerical source of truth. This
builder adds the canonical motivation/RQ ordering, the completed caption-model
ablation, an experiment-inclusion audit, and a two-column review layout.

DBR review contract checked 2026-07-16:
* A4, at most 20 pages, HWP or Word, and no acknowledgements.
* Page 1 contains author/contact data; the next page is anonymous.
* Korean abstract 300--500 characters, English abstract 100--200 words,
  and 3--6 keywords in each language.
* Korean title 18 pt, English title/headings 12 pt, authors 8 pt, body 9 pt.

The official review rules do not mandate columns. The two-column body is the
requested editorial layout; title/abstract and full-width tables/figures use
single-column sections.
"""

from __future__ import annotations

import copy
import json
import re
import subprocess
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt
from docx.text.paragraph import Paragraph

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _dbr_docx_primitives as base


ROOT = Path(__file__).resolve().parents[2]
KIISE = ROOT / "2026_KIISE"
M = KIISE / "manuscript"

SRC = Path(__file__).resolve().parent / "dbr_manuscript_build_source.md"
OUT_MD = M / "_internal_dbr_base.md"
OUT_DOCX = M / "_internal_dbr_base.docx"
OUT_PDF = M / "_internal_dbr_base.pdf"
REF_DOCX = M / "_internal_dbr_reference.docx"
AUTHOR_JSON = M / "dbr_author_info.json"
DOC_FONT_KR = "Batang"
DOC_FONT_LATIN = "Times New Roman"

KOR_TITLE = (
    "도시 감시 멀티모달 데이터베이스의 증거 표현과 색인 그리고 검색 구조와 "
    "시각 언어 모델(VLM) 질의응답과 비순환 워크로드 기반 평가"
)
ENG_TITLE = (
    "Evidence Representation, Indexing, and Retrieval Structures for "
    "Multimodal Urban-Surveillance VLM Question Answering: "
    "A Non-Circular Workload Study"
)

KOR_ABSTRACT = (
    "대규모 도시 감시 아카이브에서 질의마다 전체 영상을 시각 언어 모델(VLM)에 입력할 수 없으므로 데이터베이스가 먼저 "
    "작은 증거 집합을 검색해야 한다. 본 연구는 필터 조건(predicate)과 검색 문서 그리고 관련성(relevance)이 같은 주석 계보를 "
    "공유할 때의 순환성을 진단하고, 동일한 데이터와 질의 그리고 정답과 임베딩에 필터 또는 문서 순환만 주입하여 측정치의 "
    "인위적 상승을 확인한다. 센서 기록과 사람 주석 그리고 픽셀만 본 시각 언어 모델(VLM) 캡션을 분리한 세 원천 소스(tri-source) 워크로드에 "
    "엄격하거나 의미론적인 이중 정답과 기계 감사를 적용한다. 동일한 큐웬(Qwen) 임베딩 공간에서 증거 저장과 검색 계획과 "
    "벡터 색인의 호환 가능한 백열두 가지 구성을 공동 비교하고, 외부 미바(MEVA) 데이터셋과 십사만 삼천팔백삼십 개의 벡터와 다섯 개의 무작위 초깃값 색인 실험으로 "
    "경계를 점검한다. 결과는 단일 전역 최적보다 엄격하거나 의미론적인 목적과 지연 시간과 공간 제약에 따른 파레토(Pareto) 선택을 "
    "지지한다. 마지막으로 검색 개선이 고정 시각 언어 모델(VLM) 답변으로 전파되는 규모와 지각 능력 그리고 과제 경계를 규명한다."
)
ENG_ABSTRACT = (
    "A large urban-surveillance archive cannot be passed to a vision-language model for every query; a database must "
    "first retrieve a compact evidence set. We diagnose circular evaluation lineages and intervene on them by injecting "
    "only an oracle filter or label-restating documents while holding the data, queries, judgments, and embedding space "
    "fixed. We then apply dual strict/semantic ground truth and machine audits to a tri-source workload that separates "
    "sensor records, human judgments, and pixel-only captions. In one Qwen embedding space, we jointly evaluate 91 "
    "compatible evidence-representation, search-plan, and vector-index configurations, with a same-encoder MEVA control "
    "and a five-seed 143,830-vector index study. The results support objective- and SLA-specific Pareto selection rather "
    "than a universal optimum. Finally, controlled answer experiments identify the scale, perception, task-design, and "
    "answer-bias boundaries that determine whether retrieval improvements propagate to VLM-QA."
)
KOR_KEYWORDS = "멀티모달 데이터베이스, 도시 감시, 필터드 벡터 검색, 벡터 색인, 비순환 워크로드, 시각 언어 모델(VLM) 질의응답"
ENG_KEYWORDS = "multimodal database, urban surveillance, filtered vector search, vector index, non-circular workload, VLM question answering"

BODY_MARKER = "[DBR_BODY_TWO_COLUMNS]"
WIDE_START = "[DBR_FULL_WIDTH_START]"
WIDE_END = "[DBR_FULL_WIDTH_END]"
FINAL_WIDE_START = "[DBR_FINAL_FULL_WIDTH_START]"
PAGE_BREAK = "[DBR_PAGE_BREAK]"
COLUMN_BREAK = "[DBR_COLUMN_BREAK]"
ONE_COLUMN_TABLE_NUMBERS = {3, 4, 9, 10}

AUTHOR_INFO = {
    "kor_author_names": "박천복, Eduardo Linares, 김승현, 서영균†",
    "eng_author_names": "Cheonbok Park, Eduardo Linares, Seunghyun Kim, Young-Kyoon Suh†",
    "kor_affiliation_position": (
        "경북대학교 컴퓨터학부 "
        "(박천복·Eduardo Linares·김승현: 석사과정, 서영균: 교수)"
    ),
    "eng_affiliation_position": (
        "School of Computer Science and Engineering, Kyungpook National University, Republic of Korea"
    ),
    "detailed_field": "데이터베이스, 정보검색, 멀티모달 데이터 관리",
    "corresponding_author_name": "서영균 (교수, † 교신저자)",
    "corresponding_author_address": "대구광역시 북구 대학로 80 IT-5호관 520호",
    "postal_code": "41566",
    "phone": "053-950-6372",
    "fax": "해당 없음",
    "email": (
        "박천복 cheonbok55@knu.ac.kr; Eduardo Linares edulinaro@knu.ac.kr; "
        "김승현 seunghyeonkim010312@knu.ac.kr; 서영균 yksuh@knu.ac.kr"
    ),
}


INTRO_REPLACEMENT = """대규모 도시 교통 감시 환경은 폐쇄회로 텔레비전(CCTV) 영상과 함께 신호 상태와 시간, 위치, 그리고 교통량 데이터를 함께 생산한다. 그리고 데이터 사용자는 특정 시간대에 오토바이가 두 대 이상 보이는 교차로 장면을 찾는 것처럼 자연어에 구조적 조건을 포함하여 시각 언어 모델(VLM)[43]에 질문한다. 그러나 장기간 축적한 전체 영상이 포함된 물리적 저장소에서 사용자 질의에 맞는 데이터를 찾는 과정은 모델의 문맥 길이 제한과 그래픽 처리 장치(GPU) 비용, 그리고 검색 과정에서의 응답 지연 측면에서 비현실적이다. 따라서 대규모 저장소에서는 데이터베이스가 먼저 소수의 관련 증거를 찾아야 한다[10,13,17,32].

대량의 멀티모달 데이터로부터 사용자 질의에 맞는 VLM의 답변 생성에 필요한 소수의 시각적 및 언어적 단서를 선별하여 관리하는 데이터베이스 물리 설계 계층을 본 연구에서는 ‘증거 계층’이라고 정의한다. 질의와 관련된 영상을 검색하고 정보량이 높은 프레임을 선별하여 시각 정보와 언어 정보를 생성 단계에 함께 제공하는 기존 연구는 이러한 계층의 필요성을 뒷받침한다[3,6]. 그러나 증거 계층에서 보편적으로 적용할 수 있는 최고 효율의 구조적 설계를 결정하는 것은 어렵다.
벡터 유사도 검색과 메타데이터 필터를 어떤 순서와 방식으로 결합할지를 결정하는 ‘질의 실행 방식’의 성능은 필터 선택도와 데이터 규모 및 데이터 상관관계에 따라 달라진다[7,8]. 또한 저장 단위와 벡터 색인 구조, 그리고 데이터 분할과 색인 배치 방식의 선택은 검색 재현율과 응답 지연, 그리고 저장 공간과 구축 비용 사이에 서로 다른 상충 관계를 형성한다[9,10,11,12]. 이러한 선택으로 달라진 검색 결과가 후속 답변의 근거로 사용되므로 증거의 누락과 순위 변화는 답변 품질에도 영향을 줄 수 있다[3,6].
동일한 영상이라도 클립 단위의 설명 문장인 캡션(clip-caption)이나 개별 프레임 단위의 벡터(frame-vector), 그리고 단일 이미지와 캡션을 결합한 표현이나 다중 벡터(multi-vector) 또는 이중 색인(dual-index) 구성 중에서 무엇을 실체화하여 저장할지에 따라 검색 품질과 저장 및 연산 비용이 달라질 수 있다[3,6,10,11]. 아울러 플랫 색인(flat index)이나 계층형 탐색 가능 소세계(HNSW)[12] 또는 역색인 파일(IVF)[13] 계열과 같이 어떤 종류의 색인을 선택하고 전역 색인이나 부분 색인 또는 지역 색인 구조를 어떻게 배치하는지에 따라 검색 재현율과 지연 시간 그리고 저장 공간과 구축 비용 사이의 상충 관계가 달라진다[9,14]. 본 연구의 구체적인 연구 문제는 다음과 같다. **전체 원본 데이터를 매번 시각 언어 모델에 입력하는 대신에 필요한 증거를 더 낮은 검색 비용과 지연 시간으로 선별하면서 검색 정확도와 답변 지원 가능성을 보존하려면 어떤 데이터베이스 저장과 검색 그리고 색인 구조를 선택해야 하며 그 비교 분석 과정이 특정 구조에 유리하게 편향되어 설계되지 않았음을 어떻게 입증하고 보장할 것인가?**

연구 절차상 평가 타당성을 첫 질문으로 둔다. 순환성을 수리하지 않은 상태에서는 이후 구조 비교의 우열이 데이터 계보에 의해 미리 결정될 수 있기 때문이다.

**연구 질문 일 — 비순환 평가의 타당성.** [필터 조건](predicate)과 질의 템플릿 그리고 검색 문서와 [관련성 표식](relevance label)이 동일한 주석 계보에서 파생되는 순환성은 검색 구조의 상대 성능을 어떻게 왜곡하며, [세 원천 소스 분리](tri-source separation)와 이중 정답 그리고 기계 감사는 그 구조적 우위 보장을 제거할 수 있는가?

**연구 질문 이 — 증거 표현.** [클립 캡션](clip caption)이나 [프레임 벡터](frame vector) 그리고 [단일 이미지와 캡션 결합 표현](image caption joint representation)이나 [다중 벡터](multi vector) 혹은 [이중 색인](dual index) 구성[42]은 검색 품질과 질의 지연 시간 그리고 저장 공간 사이에 어떤 절충을 형성하며, 캡션과 질의의 정합도는 최적 표현을 어떻게 바꾸는가?

**연구 질문 삼 — 메타데이터와 벡터 결합 계획.** 필터 조건이 [강한 제약](hard constraint)인지 혹은 [약한 의도](soft intent)인지에 따라, 그리고 필터 조건과 관련성의 결합도가 어느 정도인지에 따라 [벡터 단독](vector-only) 방식이나 [사전 필터](prefilter) 혹은 [사후 필터](postfilter) 그리고 [단일 단계](single-stage) 계획의 상대 효과는 어떻게 달라지는가?

**연구 질문 사 — 검색 신호와 순위 융합.** 메타데이터나 [어휘 검색](BM25) 그리고 [밀집 텍스트](dense text)나 [시각 검색](visual retrieval) 또는 [희소 밀집](sparse dense) 및 [텍스트 시각](text visual) 융합 중 어떤 신호가 데이터 표현과 질의 유형에 적합하며, 라벨 재진술을 제거한 뒤에도 독립적인 이득을 제공하는가?

**연구 질문 오 — 물리적 색인과 배포.** 실측 필터 조건의 선택도와 군집성 그리고 질의 빈도 아래에서 [플랫](Flat) 구조나 [계층형 탐색 가능 소세계](Hierarchical Navigable Small World)[40] 혹은 [역색인 파일 플랫](Inverted File Flat)[4] 그리고 [역색인 파일 곱양자화](Inverted File Product Quantization)[4] 구조와, 관계형[5] 혹은 전용 엔진[8,41] 그리고 [전역](global)이나 [부분](partial) 혹은 [지역](local) 그리고 [자주 쓰이는 영역과 그렇지 않은 영역](hot and cold) 배포는 재현율과 지연 시간 그리고 크기와 구축 비용을 어떻게 균형화하는가?

**연구 질문 육 — 최종 시각 언어 모델 질의응답으로의 전파.** 검색 품질과 색인 재현율의 차이는 최종 [시각 언어 모델 질의응답](VLM-QA) 정확도로 어느 정도 전파되며, 코퍼스 규모와 [시각 언어 모델](VLM)의 지각 능력 그리고 질문 설계와 답변 편향은 이 전파를 어떻게 제한하는가? 정확도와 지연 시간 그리고 비용은 별도의 승자 지표가 아니라 두 번째 연구 질문부터 다섯 번째 연구 질문에 공통으로 적용되는 평가 축이며, 지연 시간과 비용에 대한 주장은 생성 추론을 제외한 검색과 색인 계층으로 한정한다."""


CONTRIBUTIONS = """본 연구의 기여는 다음과 같다.

1. [필터 조건](predicate)에 해당하는 센서 기록과 [관련성 표식](relevance)에 해당하는 사람 주석 그리고 [문서](document)에 해당하는 픽셀만 본 [시각 언어 모델](VLM) 캡션의 생성 계보를 분리한 **비순환 세 원천 소스 프로토콜**과 엄격하거나 의미론적인 이중 정답 그리고 기계 감사를 제시한다.
2. 두 초기 자체 워크로드의 코드 수준 순환 경로와 수리 전후 성능 붕괴를 재현하고, 522 데이터셋의 데이터와 질의 그리고 정답과 임베딩을 고정한 채 필터 또는 문서 순환만 주입하여 측정치가 인위적으로 상승하는 직접 개입 증거를 제시한다.
3. 실제 센서와 시공간 필터 조건 그리고 동일 선택도 [무작위 마스크](random mask)를 짝지어 공유 [사전 필터 근사 최근접 이웃](filtered-ANN)의 편향을 측정하고, [피지벡터](pgvector)[5]와 [밀버스](Milvus)[8] 그리고 [위비에이트](Weaviate)[41]에서 작동 원리와 완화 경계를 교차 확인한다.
4. 동일한 Qwen 임베딩 공간에서 호환 가능한 증거 표현과 검색 계획 그리고 [근사 최근접 이웃](ANN) 색인의 백열두 가지 구성을 정확도와 백분위수 지연 시간 그리고 크기와 구축 비용 위에서 공동 비교하고, 목적과 [서비스 수준 계약](Service Level Agreement)별 파레토 선택과 온콜드 손익분기 규칙을 도출한다.
5. 고정 생성기에서 증거 사다리, 다중 시점 선택과 색인에서 답변으로 이어지는 게이트를 수행하여 데이터베이스 개선이 답변으로 전파되는 조건과 실패 경계를 분리한다.
6. 동일 프레임과 프롬프트 그리고 [비지이 엠스리](BGE-M3) 검색기를 고정한 캡션 생성기 [소거 실험](ablation)으로 문서 표현의 모델 의존성과 도메인 의존성을 검증한다.
7. 표준 워크로드와 필터 조건 등록표 그리고 사전등록과 수정 로그 및 지표와 실험 처치 그리고 통계 검산과 두 독립 에이전트의 읽기 전용 비판 감사를 포함하는 공개 가능한 재현 체계를 구성한다.

위 기여를 보고할 때 본 논문은 주장마다 증거 지위를 구분해 명시한다. 즉, 사전등록 검정 가족에서 유의한 결과는 **확증**, 조작 실패처럼 직접 실측으로 성립한 결과는 **확립 관찰**, 신뢰구간이 0을 포함하거나 외적 이식인 결과는 **탐색적**, 파일럿 근거의 병목 후보는 **가설적**으로 표기한다."""


RELATED_GAP = """### 2.5 비디오 DB와 통합 설계공간의 공백

NoScope와 BlazeIt은 고정 카메라 영상에서 객체 존재·집계·limit 질의를 가속하고[32,33], EQUI-VOCAL은 scene graph 기반 복합 사건 질의를 합성하며[34], Spatialyze는 지리·시공간 메타데이터를 비디오 분석 DSL과 결합한다[35]. 이 연구들은 객체·트랙·시공간 질의처리를 크게 발전시켰지만, 자유형 자연어 의미와 외생 센서 predicate를 함께 사용해 VLM용 evidence packet을 구성할 때의 저장 입도·ANN/RDB 물리 설계·답변 전파가 주 평가 대상은 아니다. 반대로 HAWK 같은 감시 VLM 연구는 모델의 이상행동 이해와 QA를 평가한다[36]. ForeSea처럼 검색과 VideoLLM을 연결한 예외도 있으므로 “감시 VLM에는 검색이 없다”고 주장하지 않는다. 본 연구의 공백은 이 축들의 개별 부재가 아니라, 실제 도시 센서 predicate와 비순환 정답 아래에서 증거 표현·필터 계획·색인·백엔드·비용·답변 전파를 하나의 통제된 설계공간으로 연결한 평가가 드물다는 데 있다. 또한 Filtered-DiskANN과 ACORN은 실제 라벨과 predicate clustering을 이미 다루므로[6,9], 본 연구의 차이는 상관성의 최초 발견이 아니라 실측 도시 predicate와 동일 선택도 random mask의 짝 비교, DB 배포 및 VLM evidence 계층까지의 연결이다. UNIFY도 범위 필터 통합 색인을 제안하므로[37], 본 연구는 새 ANN 알고리즘보다 regime별 구조 선택과 평가 타당성에 초점을 둔다.
"""


CAPTION_ABLATION = """### 7.6 검색 문서 생성 모델 ablation

clip-caption의 성능이 특정 캡셔너에 고정된 결론인지 확인하기 위해 Qwen2.5-VL-7B 기준선[25]을 Qwen3-VL-8B[38]와 Qwen3.5-9B[39]로 교체했다. 522 3,000장·MEVA 985장·UCA 6,432장의 동일 프레임, 동일 프롬프트, 최대 200,704 pixels, 110-token 상한, greedy decoding을 고정하고, 문서만 다시 생성했다. 질의·qrels·metadata·BGE-M3 query embedding·B0 랭킹의 해시 동일성을 검사하고, 9/9 캡션 무결성 및 9/9 A6 감사, 36/36 주 paired 비교의 전체 질의 포함을 확인했다. 주 추정량은 동일 질의의 B2 semantic nDCG@10 차이이며 10,000회 paired bootstrap 95% CI를 사용했다.

**표 11. 캡션 생성 모델별 B2 semantic nDCG@10과 Qwen2.5-VL 대비 변화**

| 데이터셋 | Qwen2.5-VL | Qwen3-VL | 변화 [95% CI] | Qwen3.5 | 변화 [95% CI] |
|---|---:|---:|---:|---:|---:|
| 522 | 0.1700 | 0.2419 | +0.0719 [0.0288, 0.1164] | **0.2722** | **+0.1022 [0.0348, 0.1706]** |
| MEVA | 0.1029 | **0.4541** | **+0.3513 [0.3024, 0.4003]** | 0.2710 | +0.1681 [0.1441, 0.1932] |
| UCA | 0.2504 | 0.2190 | −0.0314 [−0.0587, −0.0037] | **0.3044** | **+0.0540 [0.0151, 0.0920]** |

Qwen3.5-9B는 고정 프롬프트·생성 예산으로 평가한 세 데이터셋 모두에서 기준선을 유의하게 개선해 사전 고정된 **본 실험 범위의 일관 개선** 조건을 충족했다. 이는 다른 데이터·프롬프트·예산에 대한 보편 우위를 뜻하지 않는다. Qwen3-VL은 522와 MEVA에서 개선했지만 UCA에서 유의하게 하락했으므로 도메인·전략 의존 결과다. 후속 두 모델은 UCA에서 110-token 상한 도달률이 높았다(Qwen3-VL 85.52%, Qwen3.5 54.04%; 기준선 0%). 따라서 최신 VLM 교체는 검색 문서 품질을 높일 수 있지만 장문·절단을 자동으로 해결하지 않으며, 모델별 상한을 사후 변경해서는 공정 비교가 깨진다. 생성 latency는 GPU 열 상태·병렬 실행의 영향을 받아 우위 근거로 사용하지 않는다. 이 실험은 RQ2의 clip-caption 표현이 캡셔너 선택을 포함하는 DB 물질화 결정임을 보여주며, 7.5절의 저장 단위 결론을 “Qwen2.5에만 성립”하는 결과로 제한하지 않되 보편적 단일 캡셔너를 선언하지 않게 한다.
"""


APPENDIX_C = """## 부록 C. 전체 실험 포함·제외 판정

**표 15. 저장소에 존재하는 실험 트랙의 원고 반영 판정**

| 트랙 | 데이터·비교 | 원고 판정 | 근거 절 |
|---|---|---|---|
| 순환성 붕괴 | VRU·지능형 CCTV v1→수리판 | 포함: 진단·붕괴 증거 | 4절 |
| 비순환 검색 | 522 B0–B5, strict/semantic, 결합도 | 포함: 헤드라인 | 5–6절 |
| 외부 검색 | UCA 2.5-channel, MEVA | 포함: 탐색/교차검증 | 6, 7.5절 |
| 실측 filtered-ANN | Sinnaedoro·522 visual, real vs random | 포함: 헤드라인 | 7.1절 |
| DB 엔진 | pgvector·Milvus·Weaviate | 포함 | 7.2절 |
| 색인 3축 | Flat·IVF-Flat·HNSW·IVF-PQ | 포함 | 7.3절 |
| graph 계열 | A6-KG·entity-KG 경계 | 포함: 음성/경계 결과 | 7.4절 |
| 저장 단위 | 522·MEVA caption/frame/multi/dual | 포함 | 7.5절 |
| 부분 색인·배포 | Sinnaedoro·MIRIS global/partial, N* | 포함 | 7.5절 |
| 캡셔너 강건성 | Qwen2.5-VL·Qwen3-VL·Qwen3.5 | 포함 | 7.6절 |
| 답변 계층 | VRU 증거 사다리·다각도·1K/143K 게이트 | 포함 | 8절 |
| v1 시각·융합·reranker·한국어 인코더 | 순환 qrels 상속 | 성능 주장 제외, 진단 이력만 보존 | 4절, 부록 B |
| AI Hub 이상행동·CityFlow-NL | 고아 결과 또는 staging-only | 결과 주장 제외 | 10절 |

“모든 실험 포함”은 저장소의 모든 숫자를 긍정 결과로 옮긴다는 뜻이 아니다. 수리 전 qrels를 상속한 M-계열 시각 검색, weighted fusion, cross-encoder reranker와 한국어 인코더 결과는 구현 기능을 보여도 구조 성능 근거로는 무효이므로 제외 사유를 공개한다. AI Hub 이상행동 CCTV 결과는 v3의 역할이 UCA로 재배정되어 고아 산출물이며, CityFlow-NL은 annotation staging만 존재하고 프레임·semantic qrels·다운스트림 소비자가 없어 실험 완료로 간주하지 않는다. 반면 부정적 결과(KG 환원, 색인→답변 전파 실패, 캡션 절단)는 성공 결과와 동일하게 본문에 남긴다.
"""


EXTRA_REFERENCES = """[32] D. Kang, J. Emmons, F. Abuzaid, P. Bailis, and M. Zaharia, “NoScope: Optimizing Neural Network Queries over Video at Scale,” *Proc. VLDB Endowment*, vol. 10, no. 11, 2017.
[33] D. Kang, P. Bailis, and M. Zaharia, “BlazeIt: Optimizing Declarative Aggregation and Limit Queries for Neural Network-Based Video Analytics,” *Proc. VLDB Endowment*, vol. 13, no. 4, 2019.
[34] E. Zhang et al., “EQUI-VOCAL: Synthesizing Queries for Compositional Video Events from Limited User Interactions,” *Proc. VLDB Endowment*, vol. 16, no. 11, 2023.
[35] C. Kittivorawong, Y. Ge, Y. Helal, and A. Cheung, “Spatialyze: A Geospatial Video Analytics System with Spatial-Aware Optimizations,” *Proc. VLDB Endowment*, vol. 17, no. 9, 2024.
[36] J. Tang et al., “HAWK: Learning to Understand Open-World Video Anomalies,” in *Proc. NeurIPS*, 2024.
[37] A. Liang et al., “UNIFY: Unified Index for Range Filtered Approximate Neighbors Search,” *Proc. VLDB Endowment*, vol. 18, no. 4, 2025.
[38] S. Bai et al., “Qwen3-VL Technical Report,” arXiv:2511.21631, 2025.
[39] Qwen Team, “Qwen3.5-9B Model Card,” Hugging Face, 2026. [Online]. Available: https://huggingface.co/Qwen/Qwen3.5-9B. Accessed: Jul. 16, 2026.
[40] Yu. A. Malkov and D. A. Yashunin, “Efficient and Robust Approximate Nearest Neighbor Search Using Hierarchical Navigable Small World Graphs,” *IEEE Trans. Pattern Anal. Mach. Intell.*, vol. 42, no. 4, pp. 824–836, 2018. [Online]. Available: https://github.com/nmslib/hnswlib.
[41] Weaviate, “Open-Source Vector Database for AI-driven Applications,” 2026. [Online]. Available: https://github.com/weaviate/weaviate. Accessed: Jul. 16, 2026.
[42] KIISE Datasociety Team, “Implementation and Workload Configuration for Multimodal Urban-Surveillance Vector Database and VLM-QA Evidence Layer,” GitHub Repository, 2026. [Online]. Available: https://github.com/explorer/vectorDB/experiments/db/KIISE_datasociety. Accessed: Jul. 18, 2026.
"""


def configure_section(section) -> None:
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    # The DBR review rule fixes A4, page count, and font sizes but does not
    # prescribe review margins. 1.5 cm preserves 9-pt body and readable 8-pt
    # table text while the two-column layout stays within 20 pages.
    section.top_margin = Cm(1.5)
    section.bottom_margin = Cm(1.5)
    section.left_margin = Cm(1.5)
    section.right_margin = Cm(1.5)
    section.header_distance = Cm(0.8)
    section.footer_distance = Cm(0.8)


def replace_once(text: str, pattern: str, replacement: str, flags=0) -> str:
    out, n = re.subn(pattern, replacement, text, count=1, flags=flags)
    if n != 1:
        raise RuntimeError(f"expected one replacement, got {n}: {pattern[:90]}")
    return out


def wrap_wide_blocks(text: str) -> str:
    table_pat = re.compile(
        r"(?m)(^\*\*표\s+\d+[^\n]*\*\*\n\n(?:^\|.*\n)+)"
    )
    # Frequent continuous column switches can leave large balanced-column
    # holes. Keep only genuinely wide tables across both columns; compact
    # 2--4 column result tables remain inside a normal text column.
    wide_tables = {1, 3, 4, 6, 9, 10, 11, 14, 15}

    def table_repl(match: re.Match[str]) -> str:
        block = match.group(1)
        number_match = re.search(r"\*\*표\s+(\d+)", block)
        number = int(number_match.group(1)) if number_match else -1
        if number not in wide_tables:
            return block
        if number == 15:
            return f"{FINAL_WIDE_START}\n\n{block}\n"
        return f"{WIDE_START}\n\n{block}\n{WIDE_END}\n"

    text = table_pat.sub(table_repl, text)
    fig_pat = re.compile(
        r"(?m)(^!\[그림\s+\d+[^\n]*\]\([^\n]+\)(?:\{[^\n]+\})?\n)"
    )
    wide_figures = {1, 5, 6}

    def figure_repl(match: re.Match[str]) -> str:
        block = match.group(1)
        number_match = re.search(r"그림\s+(\d+)", block)
        number = int(number_match.group(1)) if number_match else -1
        if number in wide_figures:
            return f"{WIDE_START}\n\n{block}\n{WIDE_END}\n"
        block = re.sub(r"\{width=[^}]+\}", "{width=3.0in}", block)
        return block

    text = fig_pat.sub(figure_repl, text)
    return text


def build_body() -> str:
    text = base.strip_draft_header(SRC.read_text(encoding="utf-8"))

    text = replace_once(
        text,
        r"## 초록\n\n.*?\n\n주요어: .*?\n\n## Abstract",
        f"## 초록\n\n{KOR_ABSTRACT}\n\n주요어: {KOR_KEYWORDS}\n\n## Abstract",
        re.DOTALL,
    )
    text = replace_once(
        text,
        r"## Abstract\n\n.*?\n\nKeywords: .*?\n\n## 1\. 서론",
        f"## Abstract\n\n{ENG_ABSTRACT}\n\nKeywords: {ENG_KEYWORDS}\n\n{BODY_MARKER}\n\n## 1. 서론",
        re.DOTALL,
    )

    text = replace_once(
        text,
        r"도시 교통·감시 환경은.*?이것이 본 연구가 프로토콜을 첫 기여로 두는 이유다\.",
        INTRO_REPLACEMENT,
        re.DOTALL,
    )
    text = replace_once(
        text,
        r"본 연구의 기여는 다음과 같다\..*?위 기여를 보고할 때.*?\(부록 A\)\.",
        CONTRIBUTIONS,
        re.DOTALL,
    )
    text = text.replace(
        "## 3. 비순환 워크로드 프로토콜",
        RELATED_GAP + "\n## 3. 비순환 워크로드 프로토콜",
        1,
    )
    # v3 had tables 11--12 in the answer section. The newly completed caption
    # ablation precedes it, so shift those two numbers before inserting table 11.
    text = text.replace("표 12", "__DBR_TABLE_12__")
    text = text.replace("표 11", "표 12")
    text = text.replace("__DBR_TABLE_12__", "표 13")
    text = text.replace(
        "## 8. 실험 3 — 답변 계층",
        CAPTION_ABLATION + "\n## 8. 실험 3 — 답변 계층",
        1,
    )
    # Correct a legacy Markdown row that accidentally swallowed the following
    # multi-view paragraph into the last evidence-ladder cell.
    text = text.replace(
        "| oracle (정답 클립 캡션) | 0.7467 | 0.6900 | (ii) 다각도",
        "| oracle (정답 클립 캡션) | 0.7467 | 0.6900 |\n\n(ii) 다각도",
        1,
    )
    text = text.replace("표 13 구조 선택", "표 14 구조 선택")
    text = text.replace("표 13의 상황별 권고", "표 14의 상황별 권고")
    text = text.replace("표 13(9절)", "표 14(9절)")
    text = text.replace("종합하면 표 13과 같다", "종합하면 표 14와 같다")

    # The validated v3 intentionally records extensive review history. Retain
    # every experiment and decision, but collapse repeated procedural prose so
    # the review manuscript stays within the official 20-page limit.
    text = replace_once(
        text,
        r"구축을 요약한다:.*?네 대조의 내용·522 기준·UCA 결과·판정을 표 6에 정리한다\.",
        (
            "UCA는 사람 문장주석 1,854비디오·23,542문장과 UCF-Crime 영상에서 이벤트 구간을 표집해 "
            "6,432 세그먼트로 정규화했다. 522와 같은 픽셀-only 캡션 파이프라인을 사용했고 프레임 드롭, "
            "라벨 키·렉시콘 8-gram 누출은 0건이었다. 기계 교차곱으로 135질의를 만들고, 착수 전에 네 대조 "
            "중 3건 이상 방향이 일치하면 이식 성공으로 판정하도록 고정했다. 결과는 3/4 일치였다: strict "
            "Δ(B4−B2)=+0.150, semantic duration_bin은 −0.049, semantic 음수 부호는 68/129로 재현됐다. "
            "강결합 class 계층 우위는 −0.056으로 재현되지 않았으며, 이 실패는 결합도 효과를 도메인 보편 "
            "법칙이 아닌 탐색적 결과로 제한한다. 네 대조의 내용·522 기준·UCA 결과·판정을 표 6에 정리한다."
        ),
        re.DOTALL,
    )
    text = replace_once(
        text,
        r"게이트·중단의 판정 세부는 다음과 같다.*?약 36,000 생성 호출에 해당한다\.",
        (
            "게이트 1은 exact와 26개 열화 구성의 전체 27행을 보고했으며 상대 evidence-recall@3가 "
            "0.9742–1.0526에 갇혀 조작 실패로 판정됐다. 게이트 2는 사전 고정 창에 따라 mid=HNSW(M8, "
            "ef1, 상대 0.807), strong=IVF-PQ(m32, nprobe8, 상대 0.451)을 잠갔지만, 360호출 파일럿의 "
            "적중–비적중 답변 차이가 −0.020(약 ±0.13)으로 지렛대를 보이지 않았다. Amendment 2–4의 "
            "중단 규칙에 따라 약 36,000 생성 호출의 본실험을 시작하지 않았다."
        ),
        re.DOTALL,
    )
    text = replace_once(
        text,
        r"심사자 재현 절차는 세 단계다\..*?환경·스크립트 체인의 기계 세부는 부록 A와 상호 참조한다\.",
        (
            "재현 스위트는 데이터 무결성, A6/A9, predicate 전건 짝, 85질의 기계 재도출, 원고 수치와 "
            "환경 manifest를 한 번에 검사한다. 최근 실행은 직접 40체크 40/40, 원고 수치 검증기 "
            "164/164를 통과했다. 사전등록 Amendment 1–6a와 수정 로그는 구간화 버그 정정과 전용 엔진 "
            "재라벨을 포함해 결과 이후 변경 이력을 남긴다. 이 체계는 규칙 선언 이후의 체리피킹을 차단하지만 "
            "설계 시점 자유도까지 보증하지는 않는다."
        ),
        re.DOTALL,
    )
    text = replace_once(
        text,
        r"이상의 한계를 타당성 위협의 네 범주로 정리하면 다음과 같다.*?\n\n\*\*데이터·코드 공개\.\*\*",
        (
            "타당성 위협은 네 범주다. 구성 타당성에는 과제 관련 캡션 프롬프트, 동일 순간 교차 카메라 조인의 "
            "잔여 상관과 UCA의 2.5채널성이 있다. 내적 타당성에는 설계 시점 자유도와 다각도 Qwen manifest의 "
            "사후 재구성이 남는다. 외적 타당성은 CLIP ViT-B/32, 주간 평일·448px·단일 호스트, 완전 "
            "tri-source 522 한 종과 색인→답변 VLM 1종에 제한된다. 통계적 결론 타당성에서는 결합도 쌍 "
            "군집 CI, 자연결합 2쌍과 게이트 2의 넓은 파일럿 CI를 과해석하지 않는다.\n\n"
            "**데이터·코드 공개.**"
        ),
        re.DOTALL,
    )

    # Older build sources ended at reference 31.  Current sources already
    # contain 32--42, so append the compatibility block only when it is absent.
    if not re.search(r"(?m)^\[32\]\s", text):
        text = text.replace(
            "\n## 부록 A. 재현성",
            "\n" + EXTRA_REFERENCES + "\n## 부록 A. 재현성",
            1,
        )
    text = text.rstrip() + "\n\n" + APPENDIX_C.strip() + "\n"

    # Update the main conclusion to the explicit ordered RQs.
    text = text.replace(
        "요컨대 RQ-S는 6–7절이, RQ-ALC는 7.3절과 8.2절이, RQ-M은 5·6·8절이 답한다.",
        "요컨대 첫 번째 연구 질문은 3절과 4절 그리고 6절이, 두 번째 연구 질문은 7.5절과 7.6절이, 세 번째 연구 질문과 네 번째 연구 질문은 6절이, 다섯 번째 연구 질문은 7.1절부터 7.5절까지가, 여섯 번째 연구 질문은 8절이 답한다.",
    )
    text = text.replace(
        "[17] \"ForeSea: AI Forensic Search with Multi-modal Queries for Video Surveillance,\" arXiv:2603.22872, 2026. [저자 명단 카메라레디 확정]",
        "[17] H. Park et al., \"ForeSea: AI Forensic Search with Multi-modal Queries for Video Surveillance,\" arXiv:2603.22872, 2026.",
        1,
    )
    text = text.replace(
        "본 결과는 CLIP ViT-B/32 임베딩(색인·검색 실험)·주간 평일 기록·448px 프레임 조건에 한정되며,",
        "본 결과는 [대조 언어 이미지 사전 학습 모델](CLIP) 임베딩의 색인과 검색 실험 그리고 주간 평일 기록과 사백사십팔 픽셀의 프레임 조건에 한정된다. 캡션 생성기 소거 실험은 세 모델과 공통 백열 개의 토큰 상한을 둔 단일 프롬프트 비교이며, 장문 절단의 원인을 격리하지 않는다. 또한",
        1,
    )
    return wrap_wide_blocks(text)


def build_markdown() -> None:
    AUTHOR_JSON.write_text(json.dumps(AUTHOR_INFO, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    body = base.normalize_dbr_captions(build_body())
    # Some v3 captions intentionally omitted the period after the number.
    body = re.sub(r"\*\*표\s+(\d+)\s+", r"**\\<표 \1\\> ", body)
    front = f"""# {KOR_TITLE}

{ENG_TITLE}

{AUTHOR_INFO['kor_author_names']}

{AUTHOR_INFO['eng_author_names']}

| 항목 | 내용 |
|---|---|
| 소속기관 및 직위 | {AUTHOR_INFO['kor_affiliation_position']} |
| Affiliation and Position | {AUTHOR_INFO['eng_affiliation_position']} |
| 논문의 세부분야 | {AUTHOR_INFO['detailed_field']} |
| 교신저자 성명 | {AUTHOR_INFO['corresponding_author_name']} |
| 교신저자 주소 | {AUTHOR_INFO['corresponding_author_address']} |
| 우편번호 | {AUTHOR_INFO['postal_code']} |
| 전화번호 | {AUTHOR_INFO['phone']} |
| FAX 번호 | {AUTHOR_INFO['fax']} |
| E-mail | {AUTHOR_INFO['email']} |

{PAGE_BREAK}

# {KOR_TITLE}

{ENG_TITLE}

"""
    OUT_MD.write_text(front + body, encoding="utf-8")


def create_reference_docx() -> None:
    old_ref = base.REF_DOCX
    old_font_kr, old_font_latin = base.FONT_KR, base.FONT_LATIN
    try:
        base.REF_DOCX = REF_DOCX
        base.FONT_KR = DOC_FONT_KR
        base.FONT_LATIN = DOC_FONT_LATIN
        base.create_reference_docx()
        doc = Document(REF_DOCX)
        for section in doc.sections:
            configure_section(section)
        doc.save(REF_DOCX)
    finally:
        base.REF_DOCX = old_ref
        base.FONT_KR, base.FONT_LATIN = old_font_kr, old_font_latin


def build_initial_docx() -> None:
    cmd = [
        "pandoc",
        str(OUT_MD.relative_to(ROOT)),
        "--reference-doc",
        str(REF_DOCX.relative_to(ROOT)),
        "-o",
        str(OUT_DOCX.relative_to(ROOT)),
    ]
    subprocess.run(cmd, cwd=ROOT, check=True)


def set_cols(sect_pr, count: int) -> None:
    cols = sect_pr.find(qn("w:cols"))
    if cols is None:
        cols = OxmlElement("w:cols")
        sect_pr.append(cols)
    cols.set(qn("w:num"), str(count))
    cols.set(qn("w:equalWidth"), "1")
    cols.set(qn("w:space"), "397")  # 0.7 cm


def section_break_properties(template, columns: int):
    sect_pr = copy.deepcopy(template)
    kind = sect_pr.find(qn("w:type"))
    if kind is None:
        kind = OxmlElement("w:type")
        sect_pr.insert(0, kind)
    kind.set(qn("w:val"), "continuous")
    set_cols(sect_pr, columns)
    return sect_pr


def add_page_number(section) -> None:
    para = section.footer.paragraphs[0]
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = para.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    value = OxmlElement("w:t")
    value.text = "1"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    for node in (begin, instr, separate, value, end):
        run._r.append(node)
        base.set_run_font(run, 8, False)


def constrain_table_width(
    table, target_width: int, column_weights: list[int] | None = None
) -> None:
    """Scale a result table to one column of the two-column body."""
    grid = table._tbl.find(qn("w:tblGrid"))
    if grid is None:
        return
    grid_cols = grid.findall(qn("w:gridCol"))
    current = (
        column_weights
        if column_weights is not None
        else [int(col.get(qn("w:w")) or "1") for col in grid_cols]
    )
    if len(current) != len(grid_cols):
        raise RuntimeError("one-column table width profile does not match its grid")
    total = sum(current)
    if total <= 0:
        return
    widths = [max(420, int(target_width * width / total)) for width in current]
    widths[-1] += target_width - sum(widths)

    tbl_pr = table._tbl.tblPr
    # python-docx and the native-table rebuild can each leave a preferred
    # width/layout node. LibreOffice honors the last duplicate, which makes a
    # nominal one-column table expand to the full page and clips its trailing
    # columns. Keep exactly one fixed-layout width declaration.
    for node in list(tbl_pr.findall(qn("w:tblW"))):
        tbl_pr.remove(node)
    for node in list(tbl_pr.findall(qn("w:tblLayout"))):
        tbl_pr.remove(node)
    tbl_w = OxmlElement("w:tblW")
    tbl_w.set(qn("w:type"), "dxa")
    tbl_w.set(qn("w:w"), str(target_width))
    tbl_pr.append(tbl_w)
    tbl_layout = OxmlElement("w:tblLayout")
    tbl_layout.set(qn("w:type"), "fixed")
    tbl_pr.append(tbl_layout)

    for grid_col, width in zip(grid_cols, widths):
        grid_col.set(qn("w:w"), str(width))
    for row in table.rows:
        for ci, cell in enumerate(row.cells):
            if ci >= len(widths):
                continue
            tc_pr = cell._tc.get_or_add_tcPr()
            tc_w = tc_pr.find(qn("w:tcW"))
            if tc_w is None:
                tc_w = OxmlElement("w:tcW")
                tc_pr.append(tc_w)
            tc_w.set(qn("w:type"), "dxa")
            tc_w.set(qn("w:w"), str(widths[ci]))


def polish_docx() -> None:
    old_font_kr, old_font_latin = base.FONT_KR, base.FONT_LATIN
    base.FONT_KR = DOC_FONT_KR
    base.FONT_LATIN = DOC_FONT_LATIN
    try:
        doc = Document(OUT_DOCX)
        for section in doc.sections:
            configure_section(section)
        base.enforce_paragraph_format(doc)
        base.rebuild_tables_native(doc)
        # base.enforce_paragraph_format applies the legacy 2-cm reference
        # margins, so restore this manuscript's review margins afterwards.
        for section in doc.sections:
            configure_section(section)

        # The footer relation is copied into every generated section break.
        add_page_number(doc.sections[0])
        final_sect = doc._element.body.sectPr
        has_final_wide = any(
            re.sub(r"\s+", " ", p.text).strip() == FINAL_WIDE_START
            for p in doc.paragraphs
        )
        set_cols(final_sect, 1 if has_final_wide else 2)

        marker_to_previous_columns = {
            BODY_MARKER: 1,
            WIDE_START: 2,
            WIDE_END: 1,
            FINAL_WIDE_START: 2,
        }
        for para in list(doc.paragraphs):
            txt = re.sub(r"\s+", " ", para.text).strip()
            if txt == PAGE_BREAK:
                para.clear()
                para.add_run().add_break(WD_BREAK.PAGE)
                para.paragraph_format.space_before = Pt(0)
                para.paragraph_format.space_after = Pt(0)
                para.paragraph_format.line_spacing = Pt(1)
                continue
            if txt == COLUMN_BREAK:
                para.clear()
                para.add_run().add_break(WD_BREAK.COLUMN)
                para.paragraph_format.space_before = Pt(0)
                para.paragraph_format.space_after = Pt(0)
                para.paragraph_format.line_spacing = Pt(1)
                continue
            if txt not in marker_to_previous_columns:
                continue
            columns = marker_to_previous_columns[txt]
            para.clear()
            p_pr = para._p.get_or_add_pPr()
            old = p_pr.find(qn("w:sectPr"))
            if old is not None:
                p_pr.remove(old)
            p_pr.append(section_break_properties(final_sect, columns))
            para.paragraph_format.space_before = Pt(0)
            para.paragraph_format.space_after = Pt(0)
            para.paragraph_format.line_spacing = Pt(1)

        author_lines = {AUTHOR_INFO["kor_author_names"], AUTHOR_INFO["eng_author_names"]}
        abstract_mode = False
        paragraphs = list(doc.paragraphs)
        for pi, para in enumerate(paragraphs):
            txt = re.sub(r"\s+", " ", para.text).strip()
            fmt = para.paragraph_format
            has_drawing = bool(para._p.xpath(".//w:drawing"))
            has_section_break = bool(para._p.xpath("./w:pPr/w:sectPr"))
            is_heading = bool(para.style and para.style.name.startswith("Heading"))
            num_pr = bool(para._p.xpath("./w:pPr/w:numPr"))

            # Eliminate accidental blank-line spacing introduced by Markdown.
            # Publication spacing is assigned explicitly to the surrounding
            # object, caption, heading, or body paragraph below.
            if not txt and not has_drawing:
                fmt.space_before = Pt(0)
                fmt.space_after = Pt(0)
                fmt.line_spacing = Pt(1)
                if not has_section_break:
                    for run in para.runs:
                        base.set_run_font(run, 1, False)
                continue

            fmt.space_before = Pt(0)
            fmt.space_after = Pt(2)
            # Keep the prescribed 9-pt body type while using compact journal
            # leading.  The manuscript has many full-width evidence tables and
            # figures, so 1.05 prevents avoidable spill pages without shrinking
            # the text itself.
            fmt.line_spacing = 1.05
            fmt.keep_together = False
            fmt.keep_with_next = False
            fmt.first_line_indent = Cm(0.35)

            if txt == KOR_TITLE:
                abstract_mode = False
                para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                fmt.first_line_indent = Cm(0)
                fmt.space_before = Pt(0)
                fmt.space_after = Pt(5)
                fmt.line_spacing = 1.0
                fmt.keep_together = True
                for run in para.runs:
                    base.set_run_font(run, 18, True)
            elif txt == ENG_TITLE:
                para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                fmt.first_line_indent = Cm(0)
                fmt.space_after = Pt(9)
                fmt.line_spacing = 1.0
                fmt.keep_together = True
                for run in para.runs:
                    base.set_run_font(run, 12, True)
            elif txt in author_lines:
                para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                fmt.first_line_indent = Cm(0)
                fmt.space_after = Pt(2)
                fmt.line_spacing = 1.0
                for run in para.runs:
                    base.set_run_font(run, 8, False)
            elif txt in {"초록", "Abstract"}:
                abstract_mode = True
                para.alignment = WD_ALIGN_PARAGRAPH.LEFT
                fmt.first_line_indent = Cm(0)
                fmt.space_before = Pt(8)
                fmt.space_after = Pt(3)
                fmt.line_spacing = 1.0
                fmt.keep_with_next = True
                fmt.keep_together = True
                for run in para.runs:
                    base.set_run_font(run, 12, True)
            elif is_heading:
                abstract_mode = False
                para.alignment = WD_ALIGN_PARAGRAPH.LEFT
                fmt.first_line_indent = Cm(0)
                fmt.keep_with_next = True
                fmt.keep_together = True
                level_match = re.search(r"(\d+)$", para.style.name)
                level = int(level_match.group(1)) if level_match else 2
                if level <= 2:
                    fmt.space_before = Pt(11)
                    fmt.space_after = Pt(4.5)
                    size = 12
                else:
                    fmt.space_before = Pt(7.5)
                    fmt.space_after = Pt(3)
                    size = 12
                fmt.line_spacing = 1.0
                for run in para.runs:
                    base.set_run_font(run, size, True)
            elif txt.startswith("<표 ") or txt.startswith("<그림 "):
                para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                fmt.first_line_indent = Cm(0)
                fmt.line_spacing = 1.0
                fmt.keep_together = True
                if txt.startswith("<표 "):
                    # DBR-style table title above the table.
                    fmt.space_before = Pt(8)
                    fmt.space_after = Pt(4)
                    fmt.keep_with_next = True
                else:
                    # Figure caption below the figure, with visible separation
                    # before the following body paragraph.
                    fmt.space_before = Pt(1.5)
                    fmt.space_after = Pt(7)
                for run in para.runs:
                    base.set_run_font(run, 8, True if txt.startswith("<표 ") else False)
            elif has_drawing:
                para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                fmt.first_line_indent = Cm(0)
                fmt.space_before = Pt(8)
                fmt.space_after = Pt(1.5)
                fmt.line_spacing = 1.0
                fmt.keep_with_next = True
                fmt.keep_together = True
            elif txt.startswith("[") and re.match(r"^\[\d+\]", txt):
                abstract_mode = False
                para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                fmt.first_line_indent = Cm(-0.35)
                fmt.left_indent = Cm(0.35)
                fmt.space_after = Pt(1)
                fmt.line_spacing = 1.0
                for run in para.runs:
                    base.set_run_font(run, 8, run.bold)
            else:
                para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                # Abstracts, keywords, lists, and code-like lines do not use a
                # first-line indent. Normal body prose uses 0.35 cm.
                no_indent = (
                    abstract_mode
                    or txt.startswith(("주요어:", "Keywords:", "```", "- ", "• "))
                    or num_pr
                    or bool(re.match(r"^(\(?[a-zA-Z0-9]+\)|\d+[.)])\s", txt))
                )
                if no_indent:
                    fmt.first_line_indent = Cm(0)
                if txt.startswith(("주요어:", "Keywords:")):
                    fmt.space_before = Pt(2)
                    fmt.space_after = Pt(7)
                    fmt.line_spacing = 1.0
                for run in para.runs:
                    base.set_run_font(run, 9, run.bold)

        # First table is the author-information table; result tables use a
        # compact font. Cell padding and repeated headers make the tables read
        # as publication objects rather than text pressed against grid lines.
        for ti, table in enumerate(doc.tables):
            table.autofit = False
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            if ti in ONE_COLUMN_TABLE_NUMBERS:
                # A centered one-column table is centered against the page
                # rather than the active text column by some LibreOffice
                # versions, which clips its outer cells.  Keep a small gutter
                # and anchor these compact tables to the column's left edge.
                constrain_table_width(table, 4400)
                table.alignment = WD_TABLE_ALIGNMENT.LEFT
            if table.rows:
                tr_pr = table.rows[0]._tr.get_or_add_trPr()
                if tr_pr.find(qn("w:tblHeader")) is None:
                    repeat = OxmlElement("w:tblHeader")
                    repeat.set(qn("w:val"), "true")
                    tr_pr.append(repeat)
            for ri, row in enumerate(table.rows):
                tr_pr = row._tr.get_or_add_trPr()
                if tr_pr.find(qn("w:cantSplit")) is None:
                    tr_pr.append(OxmlElement("w:cantSplit"))
                for cell in row.cells:
                    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                    margin = cell._tc.get_or_add_tcPr()
                    tc_mar = margin.find(qn("w:tcMar"))
                    if tc_mar is None:
                        tc_mar = OxmlElement("w:tcMar")
                        margin.append(tc_mar)
                    for side in ("top", "left", "bottom", "right"):
                        node = tc_mar.find(qn(f"w:{side}"))
                        if node is None:
                            node = OxmlElement(f"w:{side}")
                            tc_mar.append(node)
                        node.set(qn("w:w"), "85" if side in {"top", "bottom"} else "70")
                        node.set(qn("w:type"), "dxa")
                    for p in cell.paragraphs:
                        p.paragraph_format.space_before = Pt(0)
                        p.paragraph_format.space_after = Pt(0)
                        p.paragraph_format.line_spacing = 1.0
                        p.paragraph_format.first_line_indent = Cm(0)
                        for run in p.runs:
                            base.set_run_font(run, 8, ri == 0 or run.bold)

            # Add separation after the table even when Pandoc inserted one or
            # more empty paragraphs or a continuous section-break paragraph.
            node = table._tbl.getnext()
            while node is not None:
                if node.tag == qn("w:p"):
                    following = Paragraph(node, table._parent)
                    following_text = re.sub(r"\s+", " ", following.text).strip()
                    if following_text:
                        if (
                            not following_text.startswith("<표 ")
                            and not following_text.startswith("<그림 ")
                            and not (following.style and following.style.name.startswith("Heading"))
                        ):
                            following.paragraph_format.space_before = Pt(7)
                        break
                node = node.getnext()

        # Keep images within the full-width text area and center their anchors.
        for shape in doc.inline_shapes:
            max_width = Cm(15.8)
            if shape.width > max_width:
                ratio = max_width / shape.width
                shape.width = max_width
                shape.height = int(shape.height * ratio)
        for para in doc.paragraphs:
            if para._p.xpath(".//w:drawing"):
                para.alignment = WD_ALIGN_PARAGRAPH.CENTER

        doc.save(OUT_DOCX)
    finally:
        base.FONT_KR, base.FONT_LATIN = old_font_kr, old_font_latin


def build_pdf() -> None:
    subprocess.run(
        [
            "libreoffice",
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(M),
            str(OUT_DOCX),
        ],
        cwd=ROOT,
        check=True,
    )


def validate() -> None:
    ko_chars = len(re.sub(r"\s+", "", KOR_ABSTRACT))
    en_words = len(re.findall(r"\b[\w-]+\b", ENG_ABSTRACT))
    if not 300 <= ko_chars <= 500:
        raise RuntimeError(f"Korean abstract out of range: {ko_chars}")
    if not 100 <= en_words <= 200:
        raise RuntimeError(f"English abstract out of range: {en_words}")
    if len([x for x in KOR_KEYWORDS.split(",") if x.strip()]) not in range(3, 7):
        raise RuntimeError("Korean keyword count out of range")
    if len([x for x in ENG_KEYWORDS.split(",") if x.strip()]) not in range(3, 7):
        raise RuntimeError("English keyword count out of range")
    print(f"Korean abstract chars(no-space): {ko_chars}")
    print(f"English abstract words: {en_words}")


def main() -> None:
    validate()
    build_markdown()
    create_reference_docx()
    build_initial_docx()
    polish_docx()
    build_pdf()
    print(f"markdown: {OUT_MD}")
    print(f"docx: {OUT_DOCX}")
    print(f"pdf: {OUT_PDF}")


if __name__ == "__main__":
    raise SystemExit("internal formatter module; run make_dbr_complete_working_draft_v5.py")
