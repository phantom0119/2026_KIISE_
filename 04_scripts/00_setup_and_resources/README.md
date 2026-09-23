# [00] 환경 및 리소스 초기화 스크립트 (`00_setup_and_resources/`)

본 디렉터리는 KIISE-DBR 2026 논문 실험을 재현하기 위해 필요한 **Conda 가상환경 구축, 사전 학습된 언어/임베딩 모델 가중치 로컬 캐싱, 그리고 하드웨어(GPU) 및 의존 라이브러리/데이터셋 무결성 진단**을 수행하는 초기화 스크립트를 관리합니다.

---

## 📂 스크립트 목록 및 상세 명세

| 파일명 | 실행 권한 | 주요 입력 / 캐시 경로 | 주요 출력 아티팩트 | 구현 목적 및 핵심 역할 |
|---|:---:|---|---|---|
| [`setup_experiment_resources.sh`](setup_experiment_resources.sh) | `chmod +x` | `00_env/experiment_requirements.txt` | `Datasets/envs/kiise-vlmdb/`<br>`Datasets/logs/setup/` | 독립 Conda 가상환경(`python=3.10`, CUDA 12.1 PyTorch)을 자동 생성하고 필수 패키지 설치 및 캐시 경로를 바인딩합니다. |
| [`download_model_assets.py`](download_model_assets.py) | `chmod +x` | HuggingFace Hub | `Datasets/models/huggingface/BAAI--bge-m3/`<br>`Datasets/models/huggingface/intfloat--e5-large-v2/` | 외부 네트워크가 차단된 환경에서도 오프라인 임베딩 생성이 가능하도록 BGE-M3, E5-large-v2 및 Reranker 가중치를 사전 다운로드합니다. |
| [`check_research_resources.py`](check_research_resources.py) | `chmod +x` | `nvidia-smi`, Python 환경, `Datasets/processed/` | 콘솔 리포트 및 무결성 진단 JSON | GPU 가용 상태, CUDA 지원 여부, 핵심 패키지 버전(PyTorch, pgvector, faiss 등) 및 정본 Parquet/JSONL 파일의 행 수를 전수 검사합니다. |

---

## 🚀 표준 실행 순서

실험을 처음 시작하거나 새로운 머신에서 재현할 때 다음 순서대로 실행합니다.

```bash
# 1. Conda 가상환경 생성 및 의존성 설치
bash 04_scripts/00_setup_and_resources/setup_experiment_resources.sh

# 2. 가상환경 활성화 및 필수 환경변수 적용
conda activate /home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/envs/kiise-vlmdb
export PYTHONPATH="/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/03_src:${PYTHONPATH:-}"

# 3. 오프라인 모델 가중치 사전 캐싱 (BGE-M3 등)
python 04_scripts/00_setup_and_resources/download_model_assets.py --include-optional

# 4. 하드웨어 및 데이터셋 준비 상태 최종 진단
python 04_scripts/00_setup_and_resources/check_research_resources.py
```

---

## 🔗 선후행 의존 관계

- **선행 조건**: PostgreSQL pgvector 컨테이너가 실행 중이어야 함 (`01_infra/README.md` 참조)
- **후행 단계**: 환경과 모델 준비 완료 후 `01_dataset_canonicalization/`으로 이동하여 정본 데이터셋 및 임베딩을 빌드합니다.
