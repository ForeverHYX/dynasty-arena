#!/usr/bin/env python3
"""扫描 sim/ 目录，生成 progress.json 供实时进度页展示。每次阶段裁定后运行。"""
import json, glob, os, re, time

ROOT = os.path.dirname(os.path.abspath(__file__))
SIM = os.path.join(ROOT, "sim")

def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)

# 已完成的天道阶段
canon = sorted(glob.glob(os.path.join(SIM, "canonical", "phase*.json")),
               key=lambda p: int(re.search(r"phase(\d+)", p).group(1)))
phase = len(canon)
events_total = 0
recent = []
months_done = 0
if canon:
    last = load(canon[-1])
    evs = last["events"]
    events_total = sum(len(load(c)["events"]) for c in canon)
    months_done = max(e["month"] for e in evs)
    for e in sorted(evs, key=lambda x: x["month"])[-14:]:
        recent.append({k: e.get(k) for k in ("month", "type", "faction", "region", "title", "desc", "inter")})

# 最新天下状态
states = sorted(glob.glob(os.path.join(SIM, "state-phase*.json")),
                key=lambda p: int(re.search(r"phase(\d+)", p).group(1)))
state = load(states[-1]) if states else None
factions = []
if state:
    for fid, f in state["factions"].items():
        factions.append({
            "id": fid, "name": f["name"], "leader": f["leader"],
            "troops": f["troops"], "food": f["food"], "morale": f["morale"],
            "stability": f["stability"], "regions": f["regions"],
            "n_regions": len(f["regions"]), "alive": f.get("alive", True),
            "notes": f.get("notes", ""),
        })

# 方略收集进度（当前阶段各势力是否已交卷）
cur = phase + 1
submitted = sorted(os.path.basename(p).split("-")[1].replace(".json", "")
                   for p in glob.glob(os.path.join(SIM, "arcs", f"phase{cur}-*.json")))

final_ready = os.path.exists(os.path.join(ROOT, "index.html"))

YR = (months_done - 1) // 12 + 1 if months_done else 0
MN = ["正", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一", "十二"][(months_done - 1) % 12] if months_done else ""

out = {
    "phase": phase,            # 已裁定完成的阶段数
    "current_phase": cur,      # 正在推演的阶段
    "months_done": months_done,
    "now_label": f"天命{YR}年{MN}月" if months_done else "开局前夜",
    "events_total": events_total,
    "factions": factions,
    "recent_events": recent,
    "submitted_arcs": submitted,
    "final_ready": final_ready,
    "generated_at": time.strftime("%H:%M:%S"),
}
sd = os.path.join(ROOT, "sim", "web", "sim-data.json")
if os.path.exists(sd):
    try:
        out["characters"] = load(sd).get("characters", {})
    except Exception:
        pass
with open(os.path.join(ROOT, "progress.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False)
print("progress.json updated:", out["now_label"], f"phase={phase}", f"events={events_total}")
