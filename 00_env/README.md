# [00] 가상 환경 구축 가이드 (`00_env/`)

본 디렉터리는 2026 KIISE 연구 논문의 실험 재현 및 코드 실행을 위한 Python 가상 환경 구축 명세를 관리합니다. **실험 재현 시 가장 먼저 확인하고 구축해야 하는 00순위 단계**입니다.

---

## 📁 구성 파일 안내

| 파일명 | 형식 | 설명 및 용도 |
|---|---|---|
| [`experiment_environment.yml`](experiment_environment.yml) | Conda 환경 정의 | Conda 기반의 격리된 가상 환경(`kiise-vlmdb`, Python 3.10)을 생성하고 패키지를 일괄 설치합니다. |
| [`experiment_requirements.txt`](experiment_requirements.txt) | Pip 의존성 목록 | 데이터 처리, 검색 모델, 임베딩 런타임, 벡터 DB 클라이언트 등 핵심 라이브러리 목록입니다. |

---

## 📦 주요 패키지 구성

1. **데이터 처리 및 유틸리티**: `pandas` (>=2.2), `pyarrow` (>=16.0), `numpy` (>=1.26), `scikit-learn` (>=1.4), `tqdm`, `PyYAML`
2. **검색 베이스라인**: `rank-bm25` (BM25 텍스트 검색), `faiss-cpu` (Faiss 벡터 인덱스/ANN)
3. **임베딩 및 딥러닝 런타임**: `torch`, `torchvision`, `torchaudio`, `transformers` (>=4.51), `sentence-transformers` (>=3.0), `FlagEmbedding` (>=1.2.11 - BGE-M3 등), `accelerate`, `huggingface-hub`
4. **벡터 데이터베이스 클라이언트**: `psycopg[binary]` & `pgvector` (PostgreSQL pgvector), `pymilvus` (Milvus), `qdrant-client` (Qdrant)
5. **영상 및 시각화**: `opencv-python-headless` (영상 키프레임/비디오 처리), `matplotlib`, `seaborn`

---

## 🚀 환경 구축 방법

저장소 최상위 루트(`2026_KIISE/`)에서 아래 명령어를 실행하십시오.

### 방법 1. Conda 가상환경 생성 (권장)
```bash
# 가상 환경 생성 (kiise-vlmdb)
conda env create -f 00_env/experiment_environment.yml

# 가상 환경 활성화
conda activate kiise-vlmdb
```

### 방법 2. 기존 Python/가상환경에 Pip 설치
기존에 활성화된 Python 3.10 이상의 환경이 있는 경우:
```bash
# 기본 의존성 설치
pip install -r 00_env/experiment_requirements.txt

# (선택) CUDA 12.1 가속 PyTorch 설치 시
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### 방법 3. 원클릭 셋업 스크립트 실행
모델 캐시 경로 설정 및 리소스 초기화까지 포함된 셸 스크립트를 사용할 수도 있습니다:
```bash
bash 04_scripts/setup_experiment_resources.sh
```
