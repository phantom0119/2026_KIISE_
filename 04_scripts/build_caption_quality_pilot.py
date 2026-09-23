#!/usr/bin/env python3
"""Caption-quality human-validation pilot (522 VLM captions).

Selects a stratified sample of (frame, caption) pairs — deliberately over-sampling
the known blind spot (parked/stopped) — and emits a SELF-CONTAINED local HTML
review sheet: each card shows the frame (embedded thumbnail) + the caption + a
"what to check" hint + 3 rating dropdowns, and a button that exports the ratings
to CSV. No external upload (surveillance frames stay local).

Rating rubric (per item):
  Q1 충실도(faithfulness): 정확 / 부분(일부 누락) / 틀림·환각
  Q2 핵심요소 포착: 이 프레임의 핵심 장면요소를 캡션이 언급하나?  예 / 아니오 / 해당없음
  Q3 환각(hallucination): 프레임에 없는 것을 캡션이 말하나?  아니오 / 예

Run: Datasets/envs/kiise-vlmdb/bin/python 2026_KIISE/04_scripts/build_caption_quality_pilot.py
Out: processed/aihub_522_intersection/20260710/caption_quality_pilot/{review.html, rating_template.csv, manifest.json}
Then: 사람이 review.html 을 브라우저로 열어 평점 → "채점표 CSV 내보내기" → aggregate_caption_quality.py
"""
from __future__ import annotations
import base64, io, json
from pathlib import Path
import numpy as np, pandas as pd, cv2

PROJECT_ROOT = Path(__file__).resolve().parents[2]
VER = PROJECT_ROOT / "Datasets" / "processed" / "aihub_522_intersection" / "20260710"
OUT = VER / "caption_quality_pilot"
SEED = 20260715

# 층화 정의: (라벨, 마스크식, 목표수, 확인 힌트)
STRATA = [
    ("parked",  lambda d: d.any_parked == True,                 15, "도로변에 주차/정차한 차량이 있는지 (알려진 맹점)"),
    ("bus",     lambda d: d.max_bus >= 2,                        10, "버스가 2대 이상 보이는지"),
    ("bike",    lambda d: d.max_bike >= 2,                       10, "자전거/이륜차가 보이는지"),
    ("dense",   lambda d: d.max_objects >= 20,                   10, "차량이 매우 많은 혼잡 장면인지"),
    ("stopped", lambda d: (d.any_stopped == True) & (d.any_parked == False), 8, "정차한 차량이 있는지"),
    ("plain",   lambda d: (d.max_objects < 8) & (d.any_parked == False),      7, "한산한 장면인지 (특이 요소 유무)"),
]


def thumb_b64(path: Path, width=460, q=62) -> str | None:
    im = cv2.imread(str(path))
    if im is None:
        return None
    h, w = im.shape[:2]
    im = cv2.resize(im, (width, int(h * width / w)))
    ok, buf = cv2.imencode(".jpg", im, [cv2.IMWRITE_JPEG_QUALITY, q])
    if not ok:
        return None
    return "data:image/jpeg;base64," + base64.b64encode(buf).decode()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    docs = pd.read_parquet(VER / "captions" / "documents.parquet")   # clip_id/visual_video_id/split/text/source_frame
    ann = pd.read_parquet(VER / "annotation_video_facets.parquet")
    base = docs.merge(ann, on=["visual_video_id", "split"], how="inner")
    rng = np.random.default_rng(SEED)

    rows, used = [], set()
    for label, mask, n, hint in STRATA:
        pool = base[mask(base) & ~base.clip_id.isin(used)]
        take = pool.sample(min(n, len(pool)), random_state=SEED)
        for r in take.itertuples(index=False):
            used.add(r.clip_id)
            rows.append({"stratum": label, "hint": hint, "clip_id": r.clip_id,
                         "caption": r.text, "frame": str(VER / r.source_frame)})
    rng.shuffle(rows)  # 무작위 순서(층화 편향 방지)
    items = []
    for i, r in enumerate(rows, 1):
        b = thumb_b64(Path(r["frame"]))
        if b is None:
            continue
        items.append({"id": i, **r, "thumb": b})
    print(f"[select] {len(items)} 항목 (층화: {pd.Series([x['stratum'] for x in items]).value_counts().to_dict()})")

    # rating template CSV (fallback for manual filling)
    pd.DataFrame([{"item_id": it["id"], "stratum": it["stratum"], "clip_id": it["clip_id"],
                   "caption": it["caption"], "hint": it["hint"],
                   "Q1_faithful(정확/부분/틀림)": "", "Q2_captures(예/아니오/해당없음)": "",
                   "Q3_hallucination(아니오/예)": "", "note": ""} for it in items]
                 ).to_csv(OUT / "rating_template.csv", index=False)

    # self-contained interactive HTML
    cards = []
    for it in items:
        cards.append(f"""
<div class="card" data-id="{it['id']}">
  <div class="hd">#{it['id']} <span class="st">[{it['stratum']}]</span></div>
  <img src="{it['thumb']}"/>
  <div class="cap"><b>캡션:</b> {it['caption'].replace('<','&lt;')}</div>
  <div class="hint">✔ 확인: {it['hint']}</div>
  <div class="q">
    <label>Q1 충실도
      <select class="q1"><option value="">-</option><option>정확</option><option>부분</option><option>틀림</option></select></label>
    <label>Q2 핵심요소 언급
      <select class="q2"><option value="">-</option><option>예</option><option>아니오</option><option>해당없음</option></select></label>
    <label>Q3 환각
      <select class="q3"><option value="">-</option><option>아니오</option><option>예</option></select></label>
    <input class="note" placeholder="메모(선택)"/>
  </div>
</div>""")
    html = """<!doctype html><html lang="ko"><head><meta charset="utf-8">
<title>캡션 품질 사람검증</title><style>
body{font-family:'Malgun Gothic',sans-serif;margin:0;background:#f4f6f9;color:#222}
header{position:sticky;top:0;background:#1B2A4A;color:#fff;padding:14px 20px;display:flex;justify-content:space-between;align-items:center;z-index:10}
header h1{font-size:17px;margin:0}
#exp{background:#2E74B5;color:#fff;border:0;padding:10px 16px;border-radius:6px;font-size:14px;cursor:pointer}
#prog{font-size:13px;color:#bcd}
.wrap{max-width:760px;margin:16px auto;padding:0 12px}
.card{background:#fff;border:1px solid #e2e8f0;border-radius:10px;margin:14px 0;padding:14px;box-shadow:0 1px 3px rgba(0,0,0,.05)}
.hd{font-weight:700;color:#1B2A4A;margin-bottom:8px}.st{color:#2E74B5;font-size:13px}
.card img{width:100%;border-radius:6px;border:1px solid #ddd}
.cap{margin:10px 0;font-size:15px;line-height:1.5}.hint{color:#b45309;font-size:14px;margin-bottom:10px}
.q{display:flex;flex-wrap:wrap;gap:10px;align-items:center}
.q label{font-size:13px;display:flex;flex-direction:column;gap:3px}
.q select,.q input{padding:6px;border:1px solid #cbd5e1;border-radius:5px;font-size:14px}
.note{flex:1;min-width:160px}
.intro{background:#EAF2FB;border:1px solid #cfe0f5;border-radius:8px;padding:14px;font-size:14px;line-height:1.6}
</style></head><body>
<header><h1>522 캡션 품질 사람검증 (프레임 vs AI 캡션)</h1>
<div><span id="prog">0 / TOTAL</span> &nbsp; <button id="exp">채점표 CSV 내보내기</button></div></header>
<div class="wrap">
<div class="intro"><b>방법</b>: 각 카드의 <b>프레임(사진)</b>을 보고 그 아래 <b>AI 캡션</b>이 맞는지 3가지를 골라주세요.<br>
· <b>Q1 충실도</b>: 캡션이 사진을 정확히 서술=정확 / 일부 누락=부분 / 틀리거나 없는 걸 말함=틀림<br>
· <b>Q2 핵심요소 언급</b>: '확인' 힌트의 요소를 캡션이 언급하나 (예/아니오/해당없음)<br>
· <b>Q3 환각</b>: 사진에 <b>없는</b> 것을 캡션이 말하나 (아니오/예)<br>
끝나면 우상단 <b>CSV 내보내기</b> → 그 파일을 aggregate 스크립트에 넣으면 신뢰도 수치가 나옵니다.</div>
CARDS
</div><script>
const T=document.querySelectorAll('.card').length;document.getElementById('prog').textContent='0 / '+T;
function done(){let c=0;document.querySelectorAll('.card').forEach(k=>{if(k.querySelector('.q1').value&&k.querySelector('.q2').value&&k.querySelector('.q3').value)c++});document.getElementById('prog').textContent=c+' / '+T;}
document.addEventListener('change',done);
document.getElementById('exp').onclick=function(){
 let out=[['item_id','Q1_faithful','Q2_captures','Q3_hallucination','note']];
 document.querySelectorAll('.card').forEach(k=>{out.push([k.dataset.id,k.querySelector('.q1').value,k.querySelector('.q2').value,k.querySelector('.q3').value,'\"'+(k.querySelector('.note').value||'').replace(/\"/g,'')+'\"'])});
 let csv=out.map(r=>r.join(',')).join('\\n');
 let a=document.createElement('a');a.href=URL.createObjectURL(new Blob(['\\ufeff'+csv],{type:'text/csv'}));a.download='caption_ratings_filled.csv';a.click();
};
</script></body></html>""".replace("TOTAL", str(len(items))).replace("CARDS", "\n".join(cards))
    (OUT / "review.html").write_text(html, encoding="utf-8")

    (OUT / "manifest.json").write_text(json.dumps({
        "n_items": len(items), "seed": SEED,
        "strata": {s[0]: s[2] for s in STRATA},
        "source": "captions/documents.parquet (Qwen2.5-VL, greedy) x annotation_video_facets",
        "note": "review.html 을 브라우저로 열어 평점 후 CSV 내보내기 → aggregate_caption_quality.py",
    }, ensure_ascii=False, indent=2))
    print(f"[saved] {OUT}/review.html  (브라우저로 열어 평점)")
    print(f"[saved] {OUT}/rating_template.csv (수기 대안)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
