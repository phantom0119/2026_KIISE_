#!/usr/bin/env python3
"""P3-E: Qwen2.5-7B constrained A/B/U evidence-choice evaluation."""

from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


MODEL=Path("/hdd2/huggingface_cache/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28")
SEED=20260807
ARMS=("current_only","missing","mixed_old_last","mixed_new_last")


def prompt(row,arm,rng):
    if rng.random()<.5:a,b,current=row["old_answer"],row["new_answer"],"B"
    else:a,b,current=row["new_answer"],row["old_answer"],"A"
    if arm=="current_only":e=f"[source_epoch=2] {row['new_evidence']}"
    elif arm=="missing":e="(no retrieved evidence)"
    elif arm=="mixed_old_last":e=f"[source_epoch=2] {row['new_evidence']}\n[source_epoch=1] {row['old_evidence']}"
    else:e=f"[source_epoch=1] {row['old_evidence']}\n[source_epoch=2] {row['new_evidence']}"
    text=("Use only retrieved evidence. Select evidence with the largest source_epoch. If evidence is absent, select U.\n"
          f"Question: {row['question']}\nEvidence:\n{e}\nA: {a}\nB: {b}\nU: insufficient evidence\nAnswer with A, B, or U only.")
    return text,("U" if arm=="missing" else current),current,a,b


def main():
    p=argparse.ArgumentParser();p.add_argument("--qa",required=True,type=Path);p.add_argument("--output-dir",required=True,type=Path);p.add_argument("--batch-size",type=int,default=12);args=p.parse_args()
    out=args.output_dir.resolve();out.mkdir(parents=True,exist_ok=True)
    if not torch.cuda.is_available() or torch.cuda.mem_get_info()[0] < 18*1024**3:
        result={"T5":"MODEL_RESOURCE_PENDING","cuda_available":torch.cuda.is_available(),"free_memory_bytes":torch.cuda.mem_get_info()[0] if torch.cuda.is_available() else 0}
        (out/"aggregate.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n");print(json.dumps(result));return
    qa=list(csv.DictReader(args.qa.open(encoding="utf-8")));human=sum(str(r["human_reviewed"]).lower()=="true" for r in qa)
    tok=AutoTokenizer.from_pretrained(MODEL,local_files_only=True);tok.padding_side="left";tok.pad_token=tok.pad_token or tok.eos_token
    model=AutoModelForCausalLM.from_pretrained(MODEL,local_files_only=True,torch_dtype=torch.bfloat16,device_map={"":"cuda:0"},attn_implementation="sdpa");model.eval()
    choice_ids={letter:tok.encode(letter,add_special_tokens=False) for letter in "ABU"}
    if any(len(v)!=1 for v in choice_ids.values()):raise RuntimeError(choice_ids)
    requests=[]
    for row in qa:
        for arm in ARMS:
            rng=random.Random(SEED+int(row["fact_id"])*97+sum(map(ord,row["domain"]+arm)))
            text,expected,current,a,b=prompt(row,arm,rng)
            chat=tok.apply_chat_template([{"role":"user","content":text}],tokenize=False,add_generation_prompt=True)
            requests.append((row,arm,chat,expected,current,a,b))
    outputs=[]
    for start in range(0,len(requests),args.batch_size):
        batch=requests[start:start+args.batch_size];enc=tok([x[2] for x in batch],return_tensors="pt",padding=True,truncation=True,max_length=2048).to("cuda:0")
        with torch.inference_mode():logits=model(**enc).logits[:,-1,:]
        ids=torch.tensor([choice_ids[x][0] for x in "ABU"],device=logits.device);scores=logits.index_select(1,ids);pred=scores.argmax(1).cpu().tolist()
        for item,index,score in zip(batch,pred,scores.float().cpu().tolist()):
            row,arm,_,expected,current,a,b=item;letter="ABU"[index]
            outputs.append({"qa_id":row["qa_id"],"domain":row["domain"],"fact_id":row["fact_id"],"arm":arm,"expected_letter":expected,"current_letter":current,"predicted_letter":letter,"task_correct":int(letter==expected),"latest_answer_correct":int(letter==current),"score_A":score[0],"score_B":score[1],"score_U":score[2],"option_a":a,"option_b":b})
        print(json.dumps({"completed":min(start+len(batch),len(requests)),"total":len(requests)}),flush=True)
    arms={}
    for arm in ARMS:
        s=[r for r in outputs if r["arm"]==arm];arms[arm]={"n":len(s),"task_accuracy":sum(r["task_correct"] for r in s)/len(s),"latest_answer_accuracy":sum(r["latest_answer_correct"] for r in s)/len(s)}
    gap=arms["current_only"]["latest_answer_accuracy"]-arms["missing"]["latest_answer_accuracy"];pos=abs(arms["mixed_old_last"]["latest_answer_accuracy"]-arms["mixed_new_last"]["latest_answer_accuracy"])
    model_pass=arms["current_only"]["latest_answer_accuracy"]>=.8 and arms["missing"]["task_accuracy"]>=.7 and gap>=.3 and pos<=.1
    if not model_pass:t5="MODEL_QA_FAIL"
    elif human<30:t5="MODEL_PASS_HUMAN_REVIEW_PENDING"
    else:t5="MODEL_HUMAN_QA_PASS"
    result={"model":str(MODEL),"qa_count":len(qa),"human_reviewed":human,"arms":arms,"current_missing_gap":gap,"mixed_position_gap":pos,"T5":t5}
    with (out/"model_outputs.csv").open("w",newline="",encoding="utf-8") as f:w=csv.DictWriter(f,fieldnames=list(outputs[0]));w.writeheader();w.writerows(outputs)
    (out/"aggregate.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    lines=["# P3-E Qwen2.5-7B 자동 보고","",f"- T5: **{t5}**",f"- human reviewed: {human}/{len(qa)}","","| arm | task accuracy | latest accuracy |","|---|---:|---:|"]
    for arm in ARMS:lines.append(f"| {arm} | {arms[arm]['task_accuracy']:.3f} | {arms[arm]['latest_answer_accuracy']:.3f} |")
    (out/"AUTO_REPORT.md").write_text("\n".join(lines)+"\n",encoding="utf-8");print(json.dumps({"T5":t5,"gap":gap,"position_gap":pos}))


if __name__=="__main__":main()
