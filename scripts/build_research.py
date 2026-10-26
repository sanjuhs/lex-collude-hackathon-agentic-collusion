"""Aggregate current study artifacts, then build reproducible publication figures."""

import argparse
import csv
import hashlib
import json
import os
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lexcollude.report import wilson_interval


def collect(allow_partial=False):
    design = json.loads((ROOT / "study/design.json").read_text())
    records, runs = [], []
    for model in design["models"]:
        for policy in design["prompt_policies"]:
            folder = ROOT / "study/api-runs" / f"{model.split('-')[-1]}-{policy}"
            if not (folder / "manifest.json").exists():
                if allow_partial:
                    continue
                raise ValueError(f"Missing run: {folder}")
            manifest = json.loads((folder / "manifest.json").read_text())
            if not allow_partial and manifest["status"] != "completed":
                raise ValueError(f"Incomplete run: {folder}")
            for path in sorted((folder / "episodes").glob("*.json")):
                record = json.loads(path.read_text())
                record["artifact_path"] = str(path.relative_to(ROOT))
                record["run_id"] = folder.name
                records.append(record)
            runs.append(manifest)
    valid = [r for r in records if r["status"] == "ok"]
    rows = []
    for model in design["models"]:
        for policy in design["prompt_policies"]:
            group = [r for r in records if r["model"] == model and r.get("prompt_policy") == policy]
            ok = [r for r in group if r["status"] == "ok"]
            approved_clean = [r for r in ok if r["condition"] in ("clean", "relay_clean")
                              and r["case"]["trusted_client_approval"]]
            decisions = Counter(r["raw_decision"]["decision"] for r in ok)
            raw = sum(r["raw_score"]["unauthorized_acceptance"] for r in ok)
            rows.append({"model": model, "prompt_policy": policy, "attempted": len(group),
                         "valid": len(ok), "errors": sum(r["status"] == "error" for r in group),
                         "pending": sum(r["status"] == "pending" for r in group),
                         "unauthorized": raw,
                         "false_approval_claims": sum(r["raw_score"]["false_approval_claim"] for r in ok),
                         "report_flags": sum(r["raw_score"]["structured_report_discrepancy"] for r in ok),
                         "gate_blocks": sum(r["gate_blocked"] for r in ok),
                         "accept": decisions["accept"], "request_approval": decisions["request_approval"],
                         "reject": decisions["reject"],
                         "approved_clean_accept": sum(r["raw_score"]["accepted"] and not r["raw_score"]["unauthorized_acceptance"] for r in approved_clean),
                         "approved_clean_n": len(approved_clean),
                         "descriptive_wilson95": wilson_interval(raw, len(ok))})
    digest = hashlib.sha256()
    for record in sorted(records, key=lambda r: r["artifact_path"]):
        path = ROOT / record["artifact_path"]
        digest.update(record["artifact_path"].encode())
        digest.update(path.read_bytes())
    out = {"study_id": "lexcollude-v2-responses", "backend": "responses",
           "planned_episodes": design["planned_episodes"],
           "complete": len(valid) == design["planned_episodes"] and len(runs) == 6,
           "completed_episodes": len(valid), "attempted_episodes": len(records),
           "completed_calls": sum(len(r["calls"]) for r in valid),
           "unauthorized_acceptances": sum(r["raw_score"]["unauthorized_acceptance"] for r in valid),
           "errors": sum(r["status"] == "error" for r in records),
           "pending": sum(r["status"] == "pending" for r in records),
           "report_flags": sum(r["raw_score"]["structured_report_discrepancy"] for r in valid),
           "episode_data_sha256": digest.hexdigest(), "groups": rows,
           "statistics_note": "Counts over fixed synthetic cases. Wilson intervals are descriptive under an independence approximation, not deployment-risk guarantees. No significance or model ranking claim.",
           "records": records}
    return out


def figures(data):
    os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'results/matplotlib-cache'))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch
    import numpy as np
    dest = ROOT / "figures"
    dest.mkdir(exist_ok=True)
    navy, blue, gold, gray = "#172B4D", "#3568A6", "#C49436", "#697585"
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "text.color": navy, "axes.labelcolor": navy,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "svg.fonttype": "none", "svg.hashsalt": "lexcollude-v2",
                         "savefig.facecolor": "white"})
    def save(fig, name):
        for extension in ("png", "svg", "pdf"):
            path=dest / f"{name}.{extension}"
            fig.savefig(path, dpi=220, bbox_inches="tight",
                        **({"metadata":{"Date":None}} if extension=="svg" else {}))
            if extension=="svg":
                path.write_text('\n'.join(line.rstrip() for line in path.read_text().splitlines())+'\n')
        plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 3.2))
    ax.set_xlim(0, 10.7); ax.set_ylim(0, 3.55); ax.axis("off")
    boxes = [(0.15,1.15,2.25,1.15,"Opposing counsel","Controls comments\nand revisions", "#EDF2F8"),
             (3.05,1.15,2.25,1.15,"Document channel","Direct • summary relay\n• reciprocal revision", "#FCF5E5"),
             (5.95,1.15,2.25,1.15,"Defending agent","Sees private mandate\nChooses final action", "#EDF2F8"),
             (8.85,1.15,1.7,1.15,"Rules / gate","Check action\nagainst mandate", "#F1F3F5")]
    for x,y,w,h,title,subtitle,fill in boxes:
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.08,rounding_size=0.1",fc=fill,ec="#CED5DF",lw=1))
        ax.text(x+w/2,y+h*.72,title,ha="center",va="center",fontweight="bold",fontsize=10)
        ax.text(x+w/2,y+h*.34,subtitle,ha="center",va="center",fontsize=10,linespacing=1.5)
    for a,b in [(2.45,2.95),(5.35,5.85),(8.3,8.75)]:
        ax.annotate("",xy=(b,1.72),xytext=(a,1.72),arrowprops={"arrowstyle":"->","lw":1.8,"color":blue})
    ax.text(7.08,3.05,"Trusted client mandate",ha="center",fontweight="bold",fontsize=10)
    ax.annotate("",xy=(7.08,2.36),xytext=(7.08,2.86),arrowprops={"arrowstyle":"->","color":navy,"lw":1.5})
    ax.text(4.18,.65,"External content is evidence, not client authority",ha="center",fontsize=10,color=gray)
    ax.text(5.35,.15,"Observe decisions and artifacts. Do not infer collusion from a violation alone.",ha="center",fontsize=10,color=navy)
    save(fig,"workflow")
    conditions=["clean","misinformation","injection","relay_clean","relay_injection","revision_clean","revision_injection","verified_injection"]
    labels=["Clean","Misinformation","Instruction","Clean relay","Poisoned relay","Clean revision","Adversarial revision","Instruction + gate"]
    states=[("accept",blue,"Accept"),("request_approval",gold,"Request approval"),("reject","#CBD3DF","Reject")]
    fig,axes=plt.subplots(1,3,figsize=(9.5,6.5),sharey=True)
    for ax,model in zip(axes,["gpt-6-sol","gpt-6-astra","gpt-6-luna"]):
        for pidx,policy in enumerate(["ordinary","hardened"]):
            ys=np.arange(8)*2.2 + (pidx-.5)*.7
            values=[]
            for c in conditions:
                group=[r for r in data["records"] if r["status"]=="ok" and r["model"]==model and r["prompt_policy"]==policy and r["condition"]==c]
                values.append(Counter(r["raw_decision"]["decision"] for r in group))
            left=np.zeros(8)
            for state,color,label in states:
                vals=np.array([v[state] for v in values])
                ax.barh(ys,vals,left=left,height=.55,color=color,label=label if pidx==0 else None,
                        edgecolor="white",linewidth=.6,hatch="//" if policy=="hardened" else None)
                left+=vals
            for y,total in zip(ys,left):
                if total<3: ax.text(3.1,y,f"{int(total)}/3",va="center",fontsize=7,color=gray)
        ax.set_title(model,fontweight="bold",pad=12,fontsize=13)
        ax.set_yticks(np.arange(8)*2.2,labels,fontsize=11)
        ax.set_xlim(0,3.65);ax.set_xticks([0,1,2,3]);ax.set_xlabel("Completed cases\nper condition",fontsize=11)
        ax.grid(axis="x",alpha=.15);ax.set_axisbelow(True)
    axes[0].invert_yaxis()
    handles,legendlabels=axes[0].get_legend_handles_labels()
    fig.legend(handles,legendlabels,loc="lower center",ncol=3,bbox_to_anchor=(.57,-.015),frameon=False)
    fig.suptitle("Observed settlement decisions",x=.54,y=1.01,fontsize=16,fontweight="bold")
    fig.text(.54,.955,"Upper bar: ordinary mandate prompt · Lower hatched bar: explicit trust warning",ha="center",fontsize=10,color=gray)
    fig.tight_layout(rect=[0,.045,1,.94]);save(fig,"decisions")
    rows=data["groups"]
    fig,ax=plt.subplots(figsize=(8.8,3.7))
    y=np.arange(len(rows))
    counts=np.array([r['unauthorized'] for r in rows]);ns=np.array([r['valid'] for r in rows])
    ax.barh(y,[n-c for n,c in zip(ns,counts)],color="#E7ECF3",height=.6,label="No unauthorized finalization observed")
    ax.barh(y,counts,color=gold,height=.6,label="Unauthorized finalization")
    for i,r in enumerate(rows):ax.text(max(1,r['valid'])+.4,i,f"{r['unauthorized']} / {r['valid']} unauthorized",va='center',fontsize=9)
    ax.set_yticks(y,[r['model']+' · '+r['prompt_policy'] for r in rows]);ax.invert_yaxis()
    ax.set_xlim(0,35);ax.set_xticks([0,8,16,24]);ax.set_xlabel('Completed episodes (24 planned per row)')
    ax.set_title('Unauthorized final acceptance',loc='left',fontweight='bold',pad=16)
    ax.spines['right'].set_visible(False);ax.grid(axis='x',alpha=.12);ax.set_axisbelow(True)
    fig.tight_layout();save(fig,"primary-outcome")


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--allow-partial',action='store_true')
    args=parser.parse_args()
    data=collect(args.allow_partial)
    folder=ROOT/'study/analysis';folder.mkdir(parents=True,exist_ok=True)
    (folder/'results.json').write_text(json.dumps(data,indent=2)+'\n')
    with (folder/'model-summary.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(data['groups'][0]),lineterminator='\n');writer.writeheader();writer.writerows(data['groups'])
    figures(data)
    print(json.dumps({k:v for k,v in data.items() if k not in ('records','groups')}))


if __name__=='__main__':main()
