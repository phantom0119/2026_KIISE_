#!/usr/bin/env python3
"""Generate the disk-audited dataset lineage figures used by the paper.

The figures deliberately separate external files, research transformations,
stored artifacts, and the experiment that consumes each artifact.  The DOT
sources are generated next to this script and rendered to SVG and high-DPI PNG.
"""

from __future__ import annotations

import argparse
import html
import subprocess
from pathlib import Path


HERE = Path(__file__).resolve().parent
FONT = "NanumBarunGothic"
COLORS = {
    "raw": "#E8F3FA",
    "transform": "#EAF6EC",
    "ai": "#FFF1C7",
    "synthetic": "#FFE5D6",
    "stored": "#F5F7FA",
    "use": "#FFF3D6",
    "answer": "#F9E8F2",
    "warning": "#FFF1F0",
    "line": "#526476",
    "muted": "#66788A",
}


def br(lines: list[str]) -> str:
    return '<BR ALIGN="LEFT"/>'.join(html.escape(line) for line in lines)


def card(
    node_id: str,
    title: str,
    stage: str,
    sections: list[tuple[str, list[str]]],
    *,
    width: int = 330,
    border: str | None = None,
) -> str:
    fill = COLORS[stage]
    border = border or COLORS["line"]
    rows = [
        f'<TR><TD WIDTH="{width}" BGCOLOR="{fill}" ALIGN="LEFT" '
        f'CELLPADDING="9"><FONT POINT-SIZE="16"><B>{html.escape(title)}</B></FONT></TD></TR>'
    ]
    for heading, lines in sections:
        rows.append(
            '<TR><TD ALIGN="LEFT" BGCOLOR="#FFFFFF" CELLPADDING="8">'
            f'<FONT POINT-SIZE="11"><B>{html.escape(heading)}</B><BR ALIGN="LEFT"/>'
            f'{br(lines)}</FONT></TD></TR>'
        )
    return (
        f'{node_id} [shape=plain, margin=0, label=<<TABLE BORDER="1" COLOR="{border}" '
        'CELLBORDER="0" CELLSPACING="0" CELLPADDING="0">'
        + ''.join(rows)
        + '</TABLE>>];'
    )


def graph_header(
    title: str,
    subtitle: str,
    *,
    rankdir: str = "LR",
    splines: str = "ortho",
) -> str:
    label = html.escape(title) + "\n" + html.escape(subtitle)
    return f'''digraph G {{
  graph [rankdir={rankdir}, bgcolor="white", pad="0.28", nodesep="0.32",
         ranksep="0.68", splines={splines}, outputorder=edgesfirst,
         fontname="{FONT}", fontsize=20, label="{label}",
         labelloc=t, labeljust=l];
  node [fontname="{FONT}", color="{COLORS['line']}"];
  edge [fontname="{FONT}", fontsize=9, color="{COLORS['line']}",
        penwidth=1.15, arrowsize=0.72];
'''


def legend_node() -> str:
    return f'''legend [shape=plain, label=<<TABLE BORDER="0" CELLBORDER="1" COLOR="#A7B3C0" CELLSPACING="0" CELLPADDING="6">
      <TR>
        <TD BGCOLOR="{COLORS['raw']}">외부 원본/원 배포</TD>
        <TD BGCOLOR="{COLORS['transform']}">① 추출·파싱·임베딩</TD>
        <TD BGCOLOR="{COLORS['ai']}">② 본 연구 AI 생성</TD>
        <TD BGCOLOR="{COLORS['synthetic']}">③ 합성·proxy</TD>
        <TD BGCOLOR="{COLORS['stored']}">현재 저장 파일/DB</TD>
        <TD BGCOLOR="{COLORS['use']}">논문 실험 입력</TD>
      </TR>
    </TABLE>>];'''


def warning_node(text_lines: list[str]) -> str:
    return card(
        "warning",
        "해석 시 주의",
        "warning",
        [("논문 표기 원칙", text_lines)],
        width=520,
        border="#C63C36",
    )


def generic_flow(
    title: str,
    subtitle: str,
    raw: list[tuple[str, list[str]]],
    transform: list[tuple[str, list[str]]],
    stored: list[tuple[str, list[str]]],
    use: list[tuple[str, list[str]]],
    warning: list[str],
    *,
    transform_stage: str = "transform",
    use_stage: str = "use",
) -> str:
    parts = [graph_header(title, subtitle, rankdir="TB", splines="polyline")]
    parts.extend(
        [
            card("raw", "1. 외부 원본 파일", "raw", raw),
            card("transform", "2. 연구 처리", transform_stage, transform),
            card("stored", "3. 현재 디스크/DB 산출물", "stored", stored, width=360),
            card("use", "4. 논문에서 실제 사용", use_stage, use),
            "raw -> transform [xlabel=\"입력\"];",
            "transform -> stored [xlabel=\"materialize\"];",
            "stored -> use [xlabel=\"평가 입력\"];",
            "{ rank=same; raw; transform; }",
            "{ rank=same; stored; use; }",
            "raw -> stored [style=invis, weight=40];",
            "transform -> use [style=invis, weight=40];",
            warning_node(warning),
            "stored -> warning [style=dashed, arrowhead=none, color=\"#C63C36\", constraint=false];",
            legend_node(),
            "use -> warning [style=invis, weight=30];",
            "warning -> legend [style=invis, weight=30];",
            "}",
        ]
    )
    return "\n  ".join(parts)


def overview_dot() -> str:
    datasets = [
        (
            "d522", "AI Hub 522 교차로", "헤드라인: 검색 + 색인 + 답변",
            ["198G archive", "JPG 프레임 + 센서 CSV + CVAT XML"],
            ["processed 142G", "AI 캡션 3,000 + BGE 1,024d", "전체 프레임 143,830 + CLIP 512d"],
            ["tri-source 검색 85질의", "filtered-ANN/저장, 지각 한계 파일럿"],
        ),
        (
            "dsin", "AI Hub 시내도로", "실 프레임 색인 + 합성 규모 확장",
            ["320G JPG ZIP", "위치·카메라·파일시각 포함 CCTV 프레임"],
            ["real 132,521 x 512 CLIP", "frame_index.parquet", "synthetic 1,000,000 x 512"],
            ["실 predicate filtered-ANN", "FAISS/pgvector 규모·부분색인"],
        ),
        (
            "dmeva", "MEVA", "검색 외적 타당성 + 저장 단위",
            ["로컬 KPF/DIVA JSON 7.6G", "S3 AVI는 일시 다운로드 후 삭제"],
            ["중간프레임 JPG 985", "AI 캡션 985 + BGE/CLIP", "canonical 193질의"],
            ["활동 검색 외적 타당성", "프레임/벡터 저장 단위 비교"],
        ),
        (
            "dmiris", "MIRIS", "부분색인·hot/cold 외적 타당성",
            ["14G MP4 + YOLOv3 JSON", "Warsaw/Shibuya 12개 고정 카메라"],
            ["hold-out NPY 1,000 x 512", "PostgreSQL 59,019행", "scene/video/nobj/tseg"],
            ["공간·내용 predicate filtered-ANN", "부분색인 및 hot/cold 정책"],
        ),
        (
            "dvru", "VRU-Accident", "순환성 수리 대조 + 답변 앵커",
            ["MP4 1,000 (3.0G)", "외부 HF dense caption/VQA 5.8G"],
            ["수리판 6.1M", "외부 dense caption 1,000문서", "canonical 85질의 + BGE"],
            ["수리 전후 순환 붕괴", "고정 LLM 증거 사다리"],
        ),
        (
            "dint", "AI Hub 지능형 관제", "국내 소형 수리 대조",
            ["staging MP4 269 + JSON 269", "13G, media-label 누락 0"],
            ["외부 event_caption 269문서", "수리판 1.5M", "canonical 18질의 + BGE"],
            ["단일 JSON 생산자 한계", "수리 후 국내 CCTV 이식성"],
        ),
        (
            "duca", "UCA/UCF-Crime", "2.5채널 검색 외적 타당성",
            ["raw MP4 1,950 / UCA 주석 대상 1,854", "문장/구간 23,542, 로컬 194G, 총 110.7시간"],
            ["중간프레임 JPG + AI 캡션 6,432", "processed 176M", "canonical 135질의 + BGE"],
            ["사건 구간 기반 검색", "센서 없는 2.5채널 대조"],
        ),
        (
            "dmulti", "AI Hub 다각도 CCTV", "다중 시점 증거 선택·답변",
            ["483G ZIP", "사건 4,500 + MP4 9,000(c1/c2) + JSON"],
            ["canonical 426M", "bbox 비대칭 400사건", "evidence JPG 2,400 + VLM 답변"],
            ["worse/better/both 짝지은 답변", "검색 문서가 아닌 평가 결과"],
        ),
    ]

    def dataset_card(item: tuple) -> str:
        node_id, title, role, raw, stored, use = item
        rows = [
            f'<TR><TD COLSPAN="2" WIDTH="355" BGCOLOR="#243B53" ALIGN="LEFT" CELLPADDING="9">'
            f'<FONT COLOR="white" POINT-SIZE="15"><B>{html.escape(title)}</B></FONT><BR ALIGN="LEFT"/>'
            f'<FONT COLOR="#D9E2EC" POINT-SIZE="10">{html.escape(role)}</FONT></TD></TR>',
            f'<TR><TD WIDTH="76" BGCOLOR="{COLORS["raw"]}"><B>원본</B></TD>'
            f'<TD ALIGN="LEFT" CELLPADDING="7">{br(raw)}</TD></TR>',
            f'<TR><TD BGCOLOR="{COLORS["stored"]}"><B>저장</B></TD>'
            f'<TD ALIGN="LEFT" CELLPADDING="7">{br(stored)}</TD></TR>',
            f'<TR><TD BGCOLOR="{COLORS["use"]}"><B>사용</B></TD>'
            f'<TD ALIGN="LEFT" CELLPADDING="7">{br(use)}</TD></TR>',
        ]
        return (
            f'{node_id} [shape=plain, label=<<TABLE BORDER="1" COLOR="{COLORS["line"]}" '
            'CELLBORDER="1" CELLSPACING="0" CELLPADDING="3">'
            + ''.join(rows)
            + '</TABLE>>];'
        )

    parts = [
        graph_header(
            "본 연구 데이터셋 전체 계보: 파일 형식·저장 산출물·실험 역할",
            "2026-07-15 디스크 실측 | Datasets -> /hdd2/KIISE_datasociety/Datasets | 상세도 8장 별도 제공",
            rankdir="TB",
        )
    ]
    parts.extend(dataset_card(item) for item in datasets)
    parts.extend(
        [
            "{ rank=same; d522; dsin; dmeva; dmiris; }",
            "{ rank=same; dvru; dint; duca; dmulti; }",
            "d522 -> dsin -> dmeva -> dmiris [style=invis, weight=100];",
            "dvru -> dint -> duca -> dmulti [style=invis, weight=100];",
            "d522 -> dvru [style=invis, weight=100];",
            "legend [shape=plain, label=<<TABLE BORDER=\"0\" CELLBORDER=\"1\" COLOR=\"#A7B3C0\" CELLSPACING=\"0\" CELLPADDING=\"7\"><TR><TD BGCOLOR=\"#E8F3FA\">원본: 외부 배포 파일</TD><TD BGCOLOR=\"#F5F7FA\">저장: 현재 materialized 파일/DB</TD><TD BGCOLOR=\"#FFF3D6\">사용: 논문 평가 입력</TD><TD>크기는 du -sh, 행·shape는 parquet/NPY/DB 실측</TD></TR></TABLE>>];",
            "dmulti -> legend [style=invis, weight=50];",
            "}",
        ]
    )
    return "\n  ".join(parts)


def intersection_522_dot() -> str:
    parts = [
        graph_header(
            "AI Hub 522 교차로: 실제 파일에서 두 실험 트랙까지",
            "외부 archive 198G -> processed 142G | 주 시각은 MP4가 아니라 미리 추출된 JPG | 현재 검색 정본: canonical_trisource_expanded/",
            rankdir="TB",
            splines="polyline",
        ),
        card(
            "visual_raw", "시각 채널 (x11/x22)", "raw",
            [
                ("원본 파일", ["TS_3 / VS_3 solid archive", "내부: 교차로 CCTV JPG 프레임", "주 트랙 143,830장 / video 그룹 52,462"]),
                ("프레임 의미", ["같은 video_id의 짧은 교차로 프레임 묶음", "예: ..._105.jpg (중간 프레임)"]),
            ], width=310,
        ),
        card(
            "sensor_raw", "센서 채널 (x10)", "raw",
            [
                ("원본 파일", ["TL_1/2, VL_1/2 ZIP 내부 CSV 65,782개", "차량·보행자 계수와 신호 상태"]),
                ("카메라 관계", ["시각 x11/x22와 다른 센서 카메라", "동일 교차로·근접 시각으로만 결합"]),
            ], width=310,
        ),
        card(
            "ann_raw", "사람 주석 채널 (x11/x22)", "raw",
            [
                ("원본 파일", ["TL_3/4, VL_3/4 ZIP 내부 CVAT XML 7,787개", "프레임별 객체 bbox·상태·환경 주석"]),
                ("relevance 근거", ["stopped/parked, bus/truck/car/bike", "max_objects, env_category 등"]),
            ], width=310,
        ),
        card(
            "visual_build", "① JPG 해제·표집 + ② 캡션", "ai",
            [
                ("검색 문서용 표집", ["조인 성공 + TL_3 보유 video", "intersection_id x time_of_day 층화", "seed 20260710, 중간 JPG 3,000장"]),
                ("AI 생성 문서", ["Qwen2.5-VL-7B-Instruct (2026-07-15 정본)", "입력: 중간 JPG 픽셀만, greedy, max 110 tokens", "출력: 영어 2-4문장 장면 설명 3,000개"]),
                ("실제 문장 내용", ["교통량, 차종, 정지/주차, 보행자·자전거", "날씨·도로 상태를 자연어로 기술"]),
            ], width=360,
        ),
        card(
            "sensor_build", "① 센서 CSV 파싱·시간 조인", "transform",
            [
                ("sensor_facets.parquet", ["32,880 clips / 63 intersections", "date, hour, time_of_day, signal phase", "n_vehicles, n_pedestrians, density bins"]),
                ("visual_sensor_join.parquet", ["같은 교차로 최근접 시각 ±120초", "주 시각 video 조인율 90.18%", "시간 차 중앙값 0초"]),
            ], width=360,
        ),
        card(
            "ann_build", "① CVAT XML 파싱", "transform",
            [
                ("annotation_frame_facets.parquet", ["234,317 rows", "한 행 = 한 주석 프레임의 집계 facet"]),
                ("annotation_video_facets.parquet", ["52,210 videos", "한 행 = video 전체의 사람 주석 집계"]),
            ], width=360,
        ),
        card(
            "canonical", "검색 트랙 저장 파일", "stored",
            [
                ("captions/", ["captions_shard*.jsonl + documents.parquet", "doc_id, clip_id, text, lang, source_frame"]),
                ("canonical_trisource_expanded/", ["clips.parquet 3,000 / documents.parquet 3,000", "metadata.parquet 27,000 rows", "queries.jsonl 85", "qrels.tsv 6,809 + qrels_semantic.tsv 24,872"]),
                ("embeddings_trisource_expanded/bge-m3/", ["document_embeddings.npy 3,000 x 1,024 float32", "query_embeddings.npy 85 x 1,024 float32"]),
            ], width=390,
        ),
        card(
            "frame_index", "전체 프레임 색인 트랙 저장", "stored",
            [
                ("frames_src/train + val", ["JPG 143,830장", "bbox 확장 트랙 105,784장은 별도 폴더"]),
                ("visual_embeddings_clip/", ["frame_embeddings.npy 143,830 x 512 float32", "frame_index.parquet", "CLIP ViT-B/32, L2 정규화"]),
            ], width=390,
        ),
        card(
            "search_use", "검색 실험", "use",
            [
                ("채널 역할", ["document = 픽셀-only AI 캡션", "predicate = 센서 CSV facet", "relevance = 사람 CVAT 주석"]),
                ("평가", ["B0-B5 검색 전략", "strict + semantic 이중 qrels", "A6 계보·누출 감사 6/6 PASS"]),
            ], width=320,
        ),
        card(
            "index_use", "색인·저장·답변 실험", "answer",
            [
                ("프레임 단위 사용", ["코퍼스 B filtered-ANN", "저장 단위·색인 구조 비교", "522 지각 한계 파일럿"]),
                ("혼용 금지", ["검색 문서 단위 = 3,000 clips", "색인 단위 = 143,830 frames"]),
            ], width=320,
        ),
        "{ rank=same; visual_raw; sensor_raw; ann_raw; }",
        "{ rank=same; visual_build; sensor_build; ann_build; }",
        "{ rank=same; canonical; frame_index; }",
        "{ rank=same; search_use; index_use; }",
        "visual_raw -> visual_build;",
        "sensor_raw -> sensor_build;",
        "ann_raw -> ann_build;",
        "sensor_build -> visual_build [xlabel=\"조인·표집 조건\", constraint=false];",
        "ann_build -> visual_build [xlabel=\"주석 보유 조건\", constraint=false];",
        "visual_build -> canonical [xlabel=\"document\"];",
        "sensor_build -> canonical [xlabel=\"predicate\"];",
        "ann_build -> canonical [xlabel=\"relevance\"];",
        "canonical -> search_use;",
        "visual_raw -> frame_index [xlabel=\"전체 JPG는 별도 CLIP\", style=dashed, constraint=false];",
        "sensor_build -> frame_index [xlabel=\"filter facet\", style=dashed, constraint=false];",
        "frame_index -> index_use;",
        card(
            "excluded", "헤드라인에서 분리", "warning",
            [
                ("TS_4 / VS_4", ["악천후·시간대 bbox JPG 105,784장", "센서 조인 0%: 검색 canonical 제외"]),
                ("frames_src 전체", ["주 트랙 143,830 + bbox 105,784 = JPG 249,614장", "143,830은 train/val 주 트랙만의 수"]),
                ("TL_5 / VL_5", ["큐보이드 staging 존재", "최종 relevance/canonical 미사용"]),
                ("정확한 비순환성 주장", ["파일·카메라·생산 경로가 분리됨", "같은 교통 현상의 통계적 독립을 뜻하지 않음"]),
            ], width=600, border="#C63C36",
        ),
        "canonical -> excluded [style=dashed, arrowhead=none, color=\"#C63C36\", constraint=false];",
        legend_node(),
        "search_use -> excluded [style=invis, weight=30];",
        "excluded -> legend [style=invis, weight=30];",
        "}",
    ]
    return "\n  ".join(parts)


def diagrams() -> dict[str, str]:
    return {
        "dataset_lineage_overview": overview_dot(),
        "dataset_lineage_522_trisource": intersection_522_dot(),
        "dataset_lineage_sinnaedoro": generic_flow(
            "AI Hub 시내도로 CCTV: 실제 프레임 벡터와 합성 1M의 분리",
            "외부 320G -> processed 2.5G | 검색 문서/캡션이 없는 색인 전용 코퍼스",
            [
                ("배포 형식", ["Training/Validation JPG ZIP", "고정형 도로 CCTV 프레임 (MP4 아님)"]),
                ("프레임 식별 정보", ["location / camera / date / time", "예: 범박터널-범박1교방향, BC1000501, 20201004"]),
            ],
            [
                ("① 실제 데이터 변환", ["원천 JPG ZIP 131개를 풀지 않고 직접 읽기", "위치·카메라·시간에 걸쳐 분산 표집", "CLIP ViT-B/32 -> 512차원, L2 정규화", "표집 JPG 자체는 별도 파일로 저장하지 않음"]),
                ("③ 합성 규모 확장", ["real vector 재표본 + jitter로 기록", "1,000,000개 CLIP-space vector 생성"]),
            ],
            [
                ("corpus_real/", ["frame_embeddings.npy: 132,521 x 512 float32 (~259MiB)", "frame_index.parquet: 132,521 rows", "facets: location 39 / camera 16,107 / date 51", "queries.npy: hold-out 1,000 x 512"]),
                ("corpus_aug_1m.npy", ["1,000,000 x 512 float32", "2,048,000,128 bytes (약 1.91GiB)", "실제 JPG 100만 장이 아니라 합성 벡터"]),
            ],
            [
                ("real 132,521", ["실제 시공간 predicate filtered-ANN", "FAISS 색인 Pareto", "PostgreSQL b3_frames 부분색인"]),
                ("synthetic 1M", ["메모리·지연시간 규모 확장만 측정", "실제 CCTV 분포/라벨 성능 주장에 사용하지 않음"]),
            ],
            ["real과 synthetic 결과를 표·파일명에서 분리한다.", "1M 생성 seed/jitter/source map manifest가 없어 원점 재현 계보는 현재 불완전하다."],
        ),
        "dataset_lineage_meva": generic_flow(
            "MEVA: 원격 AVI·사람 활동 주석·픽셀-only 캡션의 구축 계보",
            "로컬 원본 7.6G(주석 중심) -> processed 638M | 최종 materialized 985 clips",
            [
                ("로컬 외부 파일", ["KPF/DIVA *.activities.yml / *.geom.yml / *.types.yml", "contrib *.activities.json / *.file-index.json", "capture metadata와 사람 활동 주석"]),
                ("원격 영상", ["공개 S3 drops-123-r13의 약 5분 AVI", "필요할 때만 다운로드: 현재 로컬 AVI 0개"]),
            ],
            [
                ("① 프레임·facet", ["AVI 중간 프레임 1장 -> JPG", "추출 직후 임시 AVI 삭제", "location/hour/time_of_day predicate", "activity presence relevance"]),
                ("② AI 문서", ["Qwen2.5-VL-7B-Instruct (2026-07-15 정본)", "입력: 중간 JPG 픽셀만", "출력: 영어 장면 캡션 985개"]),
            ],
            [
                ("frames/ + captions/", ["frames/*.jpg: 985", "captions_shard*.jsonl", "documents.parquet: doc_id/clip_id/text/source_frame"]),
                ("canonical_trisource/", ["clips/documents 985", "metadata.parquet 3,940 rows", "queries.jsonl 193", "strict qrels 4,405 / semantic 17,205"]),
                ("embeddings/", ["BGE-M3 document 985 x 1,024", "CLIP frame 985 x 512 (NPY + index parquet)"]),
            ],
            [
                ("검색", ["활동 검색의 외적 타당성", "A6 계보 감사 PASS"]),
                ("저장", ["영상/프레임/벡터 저장 단위 비교", "최종 985만 정본; 276 clip 파일럿은 폐기"]),
            ],
            ["7.6G는 전체 영상 크기가 아니라 로컬 주석 repository 크기다.", "재구축에는 S3 접근이 필요하며 522와 같은 독립 센서 tri-source는 아니다."],
        ),
        "dataset_lineage_miris": generic_flow(
            "MIRIS: 교통 영상·YOLOv3 JSON에서 PostgreSQL 부분색인까지",
            "외부 14G -> query 파일 4.0M + PostgreSQL 서비스 상태 | Warsaw/Shibuya 12개 고정 카메라",
            [
                ("미디어", ["warsaw/*.mp4 + shibuya/*.mp4", "12개 고정 카메라 영상", "beach/uav 트랙은 현재 실험에서 제외"]),
                ("메타/검출", ["*-detections.json / *-baseline.json", "YOLOv3 검출·track 결과", "전 프레임 사람 GT가 아님"]),
            ],
            [
                ("① 프레임 임베딩", ["6-frame stride, video당 최대 5,200", "총 60,019 frames", "CLIP ViT-B/32 -> 512차원"]),
                ("①/③ predicate", ["scene=Warsaw/Shibuya", "video=카메라-세션 파일명", "nobj=YOLOv3 검출 객체수", "tseg=video 상대 위치를 0..23으로 양자화"]),
            ],
            [
                ("파일", ["miris_queries2.npy: 1,000 x 512 float32", "hold-out query vector만 portable 파일로 보존"]),
                ("PostgreSQL + pgvector", ["miris_frames2: 59,019 rows (~162.1MiB)", "vector(512), scene, video, nobj, tseg", "volume: Datasets/services/postgres_pgvector"]),
                ("보존 상태", ["추출 JPG는 저장하지 않음", "구형 miris_frames도 59,019 rows", "구형 hour 열은 실제 시계 시간이 아니므로 해석 금지"]),
            ],
            [
                ("filtered-ANN", ["scene/video/nobj 조건 검색", "1,000 hold-out query의 exact GT 비교"]),
                ("DB 설계", ["부분색인·hot/cold 정책 외적 타당성", "캡션/semantic qrels 검색에는 사용하지 않음"]),
            ],
            ["nobj는 검출기 출력 수이며 사람 정답 객체수가 아니다.", "벡터 본체의 portable dump/parquet가 없어 장기 보존이 DB volume에 의존한다."],
        ),
        "dataset_lineage_vru": generic_flow(
            "VRU-Accident: 외부 영상·dense caption에서 비순환 수리판까지",
            "영상 3.0G + 외부 HF 표 5.8G -> 현재 수리판 6.1M | 1,000 clips",
            [
                ("영상", ["raw/VRU-Accident/VRU_videos/**/*.mp4", "CAP_DATA, DADA_2000, DoTA, MANUAL_DATA", "총 1,000 accident clips"]),
                ("외부 문서/라벨", ["HF *.parquet", "dense caption 1,000 + VQA 6,000", "본 연구 Qwen 생성물이 아님"]),
            ],
            [
                ("v1 순환판", ["dense caption + VQA 답변 template", "documents 7,000 / queries 244", "filter·qrels·문서가 VQA 계보 공유"]),
                ("① 20260710_noncircular 수리", ["VQA-derived 문서 제거", "document=외부 dense caption", "relevance=accident_type", "filter=weather_light/road_type/location"]),
            ],
            [
                ("canonical/", ["clips.parquet 1,000 / documents.parquet 1,000", "metadata.parquet 6,000 rows", "queries.jsonl 85", "qrels.tsv 3,744 / semantic 9,703"]),
                ("문서 행의 값", ["text=날씨·도로·주행·사고를 설명하는 영어 문장", "source=외부 caption parquet 파일명"]),
                ("embeddings/bge-m3/", ["document 1,000 x 1,024", "query 85 x 1,024 (NPY + index parquet)"]),
            ],
            [
                ("검색 대조", ["순환 워크로드 붕괴와 수리 전후 비교", "A9 감사·채널 결합도 보고"]),
                ("답변", ["고정 LLM 증거 사다리의 앵커 데이터"]),
            ],
            ["수리판도 문서·filter·relevance가 같은 외부 VQA 생산자 계보에 속한다.", "따라서 522의 생산자 수준 tri-source와 동등하다고 주장하지 않는다."],
        ),
        "dataset_lineage_intelligent_cctv": generic_flow(
            "AI Hub 지능형 관제 CCTV: MP4/JSON staging에서 수리판 검색까지",
            "선별 staging 13G -> 현재 수리판 1.5M | media-label pair 누락 0",
            [
                ("외부 -> staging", ["외부 원천 ZIP 31 + 라벨 ZIP 31", "선별 videos/{train,val}/event/*.mp4: 269", "labels/{train,val}/event/*.json: 269", "clip_pairs.csv로 1:1 pair 고정"]),
                ("JSON 내용", ["event_caption, event_class", "night, place_type 등 사건·환경 label", "event_caption은 외부 제공 문서"]),
            ],
            [
                ("v1 순환판", ["event_caption + event class template", "documents 807 / queries 133", "라벨 어휘의 직접 재진술 포함"]),
                ("① 20260710_noncircular 수리", ["template 문서 제거", "document=외부 event_caption", "relevance=event_class", "filter=night/place_type"]),
            ],
            [
                ("canonical/", ["clips/documents.parquet 269", "queries.jsonl 18", "qrels.tsv 584 / semantic 827"]),
                ("실제 문서 예", ["'가방을 가진 3명과 ... 모텔 앞 도로변에서 ...'", "lang=ko, source=원 JSON 경로"]),
                ("embeddings/bge-m3/", ["document 269 x 1,024", "query 18 x 1,024 (NPY + index parquet)"]),
            ],
            [
                ("검색 대조", ["순환 붕괴와 수리 효과", "국내 고정형 CCTV 소형 이식성 대조"]),
                ("범위", ["헤드라인 tri-source가 아닌 보조 control"]),
            ],
            ["event_caption은 본 연구가 VLM으로 생성한 캡션이 아니다.", "모든 채널이 같은 외부 JSON 생산자에 의존하므로 생산자 독립성은 없다."],
        ),
        "dataset_lineage_uca": generic_flow(
            "UCA/UCF-Crime: 사건 구간 MP4에서 6,432개 AI 검색 문서까지",
            "외부 194G | UCF-Crime 1,854 videos + UCA 문장/구간 23,542 (110.7시간)",
            [
                ("영상", ["UCF_Crimes/**/*.mp4: raw 1,950개", "UCA 주석과 연결되는 감시 영상 1,854개"]),
                ("사람 문장 주석", ["사건 설명 text + start/end seconds", "총 23,542 sentences / 110.7시간", "relevance lexicon의 원천"]),
            ],
            [
                ("① 구간 materialize", ["video당 최대 4 event spans 등간 표집", "각 구간 midpoint -> JPG", "중복 (video, midpoint) 58건 병합", "최종 6,432 segments, frame drop 0"]),
                ("② AI 문서", ["Qwen2.5-VL-7B-Instruct (2026-07-15 정본)", "입력: midpoint JPG 픽셀만", "정답 lexicon을 prompt에 넣지 않음", "영어 장면 캡션 6,432개"]),
            ],
            [
                ("frames/ + captions/", ["frames/*.jpg 6,432", "captions_shard*.jsonl", "documents.parquet: doc_id/video_id/split/caption"]),
                ("canonical/", ["clips/documents 6,432", "metadata.parquet 19,296 rows", "queries.jsonl 135", "strict qrels 7,709 / semantic 41,435"]),
                ("embeddings/bge-m3/", ["document 6,432 x 1,024", "query 135 x 1,024 float32 NPY"]),
            ],
            [
                ("검색 외적 타당성", ["사건 구간 기반 B0-B5 검색", "A6 계보 감사 + strict/semantic qrels"]),
                ("채널 수준", ["document=VLM, relevance=사람 문장", "predicate=video class/duration/일부 timing"]),
            ],
            ["독립 센서가 없고 코퍼스 포함 자체가 annotation span에 의존한다.", "따라서 물리 3채널이 아니라 '2.5채널' 외적 타당성으로만 해석한다."],
        ),
        "dataset_lineage_multiangle": generic_flow(
            "AI Hub 다각도 CCTV: c1/c2 영상에서 시점별 증거·VLM 답변까지",
            "외부 483G ZIP -> processed 426M | 답변 실험의 검색 문서와 생성 답변을 구분",
            [
                ("외부 archive", ["원천+라벨 ZIP 44개 / 총 483G", "4,500 events", "event당 c1/c2 MP4 = 총 9,000 views"]),
                ("라벨 JSON", ["JSON 4,500", "bbox, event class, question/answer, frame/object ID", "두 view의 완전 동기 프레임은 보장되지 않음"]),
            ],
            [
                ("① canonical 파싱", ["clips 4,500 / views 9,000", "evidence frame rows 27,000", "외부 JSON + template 문서 36,000", "metadata rows 63,000 / queries 4,572"]),
                ("① bbox 비대칭 표집", ["bbox 면적 기준 better/worse가 다른 400 events", "view당 최대 3 frames -> JPG 2,400", "추출 오류 0"]),
                ("② 답변 생성", ["Qwen2.5-VL, Qwen2-VL, InternVL3, Idefics2", "closed/worse/better/both 조건별 답변"]),
            ],
            [
                ("canonical/", ["clips/views/evidence_frames/documents/metadata.parquet", "queries.jsonl + qrels.tsv", "documents 36,000은 외부 JSON 기반 검색용 staging"]),
                ("keyframes/stratum_bbox_asymmetry_400/", ["frames/*.jpg 2,400", "frames.parquet + frame_manifest.json", "frame_extract_errors.csv = 0 errors"]),
                ("results/multiview_answer_vlm_*_400/", ["모델별 vlm_answers.parquet 1,600 rows", "run_manifest.json + eval/*.csv/json", "AI 답변은 데이터셋 문서가 아니라 실험 결과"]),
            ],
            [
                ("시점 선택", ["worse / better / both evidence의 짝지은 비교", "bbox 가시성과 답변 정확도 관계"]),
                ("모델 비교", ["4개 VLM의 동일 400-event 답변 평가", "tri-source 검색 헤드라인에는 사용하지 않음"]),
            ],
            ["better/worse는 bbox 면적 proxy이며 의미적 정보량의 완전한 정답이 아니다.", "두 view를 동일 시각의 완전 동기 pair로 기술하지 않는다."],
            use_stage="answer",
        ),
    }


def render(dot_path: Path, *, dpi: int) -> None:
    subprocess.run(["dot", "-Tsvg", str(dot_path), "-o", str(dot_path.with_suffix(".svg"))], check=True)
    subprocess.run(
        ["dot", f"-Gdpi={dpi}", "-Tpng", str(dot_path), "-o", str(dot_path.with_suffix(".png"))],
        check=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dpi", type=int, default=300)
    parser.add_argument("--no-render", action="store_true")
    args = parser.parse_args()

    for stem, dot in diagrams().items():
        dot_path = HERE / f"{stem}.dot"
        dot_path.write_text(dot + "\n", encoding="utf-8")
        if not args.no_render:
            render(dot_path, dpi=args.dpi)
        print(dot_path.name)


if __name__ == "__main__":
    main()
