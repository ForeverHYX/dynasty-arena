#!/usr/bin/env python3
"""合并 canonical 正典 + geometry 几何 + 状态文件 → sim/web/sim-data.json（网页数据源）。
每次天道裁定后运行；终局后再运行一次加入 epilogue。"""
import json, glob, os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
SIM = os.path.join(ROOT, "sim")
WEB = os.path.join(ROOT, "sim", "web")
os.makedirs(WEB, exist_ok=True)

def load(p):
    with open(p, encoding="utf-8") as f: return json.load(f)

COLORS = {"qin":"#8f9bb0","han":"#c94b3c","donghan":"#6da85e","sui":"#a06cc9",
          "tang":"#e0ad3c","song":"#4fa387","yuan":"#4f83d9","ming":"#d4628f"}
CRESTS = {"qin":"秦","han":"汉","donghan":"汉","sui":"隋","tang":"唐",
          "song":"宋","yuan":"元","ming":"明"}
LEADERS = {"qin":"嬴政","han":"刘邦","donghan":"刘秀","sui":"杨坚",
           "tang":"李渊","song":"赵匡胤","yuan":"忽必烈","ming":"朱元璋"}
START = {"qin":"longxi","han":"bashu","donghan":"hebei","sui":"guanzhong",
         "tang":"hedong","song":"zhongyuan","yuan":"mobei","ming":"jiangnan"}

MN = ["正月","二月","三月","四月","五月","六月","七月","八月","九月","十月","十一月","十二月"]

# ---- 收集正典 ----
canon_files = sorted(glob.glob(os.path.join(SIM, "canonical", "phase*.json")),
                     key=lambda p: int(re.search(r"phase(\d+)", p).group(1)))
all_events = []
for cf in canon_files:
    all_events += load(cf)["events"]
N = max(e["month"] for e in all_events)

# ---- 逐月归属 ----
base = load(os.path.join(SIM, "state-phase0.json"))
ownership = {}
cur = {rid: r["owner"] for rid, r in base["regions"].items()}
for m in range(1, N + 1):
    for e in sorted([x for x in all_events if x["month"] == m], key=lambda x: all_events.index(x)):
        for rid, o in (e.get("delta", {}).get("regions") or {}).items():
            cur[rid] = o
    ownership[str(m)] = dict(cur)

# ---- 逐月势力数值（事件 delta 累积 + 阶段末与 state 文件对齐）----
states = {"0": base}
for sp in sorted(glob.glob(os.path.join(SIM, "state-phase*.json")),
                 key=lambda p: int(re.search(r"phase(\d+)", p).group(1))):
    states[re.search(r"phase(\d+)", sp).group(1)] = load(sp)

fids = list(base["factions"].keys())
power = {f: {"regions": [], "troops": [], "food": [], "morale": [], "stability": []} for f in fids}
curv = {f: {k: base["factions"][f][tk] for k, tk in
            [("troops","troops"),("food","food"),("morale","morale"),("stability","stability")]} for f in fids}
for m in range(1, N + 1):
    evs = [e for e in all_events if e["month"] == m]
    for e in evs:
        d = e.get("delta", {})
        for key in ("troops","food","morale","stability"):
            for f, v in (d.get(key) or {}).items():
                if f in curv:
                    curv[f][key] = round(curv[f][key] + v, 1)
    # 阶段末对齐
    ph = m // 12
    if m % 12 == 0 and str(ph) in states:
        st = states[str(ph)]["factions"]
        for f in fids:
            if f in st:
                for key in ("troops","food","morale","stability"):
                    if st[f].get(key) is not None:
                        curv[f][key] = st[f][key]
    for f in fids:
        power[f]["regions"].append(sum(1 for r in ownership[str(m)].values() if r == f))
        for key in ("troops","food","morale","stability"):
            power[f][key].append(curv[f][key])

# ---- regions 合并（真实省界几何）----
geo = load(os.path.join(SIM, "geometry2.json"))
regions = {}
for rid, r in base["regions"].items():
    g = geo["regions"][rid]
    regions[rid] = {
        "name": r["name"], "terrain": g.get("terrain",""), "pop": r["pop"], "grain": r["grain"],
        "capital": g["cities"][0]["n"], "cities": g["cities"],
        "label": g["label"],
    }
TERRAIN = {"longxi":"高原险塞·产马","guanzhong":"四塞之国·沃野","hedong":"表里山河·盐铁",
           "hebei":"平原·豪族","zhongyuan":"四战之地·漕运","shandong":"丘陵·渔盐",
           "bashu":"天府·蜀道天险","jingchu":"江汉·水乡","jianghuai":"淮上·鱼米",
           "jiangnan":"财赋·水网","lingnan":"岭海·港市","mobei":"草原·贫瘠"}
for rid in regions: regions[rid]["terrain"] = TERRAIN.get(rid, "")

# ---- factions（人设信息）----
factions = {}
for f in fids:
    factions[f] = {"name": base["factions"][f]["name"], "leader": LEADERS[f], "color": COLORS[f],
                   "crest": CRESTS[f], "start_region": START[f],
                   "doctrine": "", "bio": "", "ministers": [], "leader_fate": "", "minister_fates": []}
    pm = os.path.join(SIM, "personas", f + ".md")
    if os.path.exists(pm):
        txt = open(pm, encoding="utf-8").read()
        m = re.search(r"## 战略思想\n(.+?)(?=\n##|\Z)", txt, re.S)
        if m: factions[f]["doctrine"] = " ".join(m.group(1).split())[:90]
        m = re.search(r"## 背景\n(.+?)(?=\n##|\Z)", txt, re.S)
        if m: factions[f]["bio"] = " ".join(m.group(1).split())[:90]
        ms = re.findall(r"^- ([^（（]+?)[（(]([^）)]+)[）)](.*)$", txt, re.M)
        seen = set()
        for name, role, note in ms:
            name = name.strip()
            if name in seen or len(factions[f]["ministers"]) >= 6: continue
            seen.add(name)
            factions[f]["ministers"].append({"name": name, "role": role.strip()[:6],
                                             "note": " ".join(note.split())[:40]})

# ---- epilogue（若已有）----
epilogue = {"world_verdict":"推演仍在进行……","end_reason_cn":"未定",
            "fates":{f:{"leader":"","ministers":[]} for f in fids},
            "turning_points":[], "ranking":[]}
ep_path = os.path.join(SIM, "epilogue.json")
if os.path.exists(ep_path):
    ep = load(ep_path)
    epilogue.update(ep)
    for f, fe in (ep.get("fates") or {}).items():
        if f in factions:
            factions[f]["leader_fate"] = fe.get("leader","")
            factions[f]["minister_fates"] = fe.get("ministers",[])

months_label = []
for m in range(1, N + 1):
    months_label.append(f"天命{(m-1)//12+1}年{MN[(m-1)%12]}")

timeline = {}
for m in range(1, N + 1):
    evs = [e for e in all_events if e["month"] == m]
    timeline[str(m)] = sorted(evs, key=lambda e: 0 if e["type"]=="war" else 1)

# ---- 人物→势力字典（人名角标）----
EXTRA = {
    "扶苏":"qin","胡亥":"qin","赵高":"qin","李信":"qin","蒙毅":"qin","尉缭":"qin",
    "吕后":"han","刘盈":"han","灌婴":"han","刘交":"han","陆贾":"han","郦食其":"han",
    "卢生":"qin","徐巿":"qin",
    "阴丽华":"donghan","郭圣通":"donghan","刘庄":"donghan","贾复":"donghan","马成":"donghan","耿纯":"donghan","吴汉":"donghan",
    "独孤伽罗":"sui","独孤后":"sui","韩擒虎":"sui","贺若弼":"sui","杨勇":"sui","杨广":"sui","长孙晟":"sui",
    "李元吉":"tang","魏征":"tang","薛万彻":"tang","房玄龄":"tang","杜如晦":"tang","尉迟恭":"tang","秦琼":"tang","平阳公主":"tang",
    "慕容延钊":"song","石守信":"song","高怀德":"song","王审琦":"song","曹翰":"song","李处耘":"song","赵德昭":"song","赵匡义":"song",
    "姚枢":"yuan","张弘范":"yuan","王著":"yuan","刘秉忠":"yuan","史天泽":"yuan","阿合马":"yuan","阿里不哥":"yuan","真金":"yuan",
    "沐英":"ming","胡惟庸":"ming","朱标":"ming","李文忠":"ming","蓝玉":"ming","马皇后":"ming",
}
CHARACTERS = {}
for f in fids:
    for m in factions[f]["ministers"]:
        CHARACTERS[m["name"]] = f
    CHARACTERS[LEADERS[f]] = f
# 拆分顿号并列的人名（曹参、灌婴、樊哙、周勃），并过滤非人名脏键
import re as _re
def _name_ok(s):
    return 2 <= len(s) <= 4 and not _re.search(r"[\s0-9a-zA-Z。；：，、「」『』（）【】*·～—-]", s)
_split = {}
_clean = {}
for name, f in CHARACTERS.items():
    if "、" in name or "，" in name or "," in name:
        for part in name.replace("，", "、").replace(",", "、").split("、"):
            part = part.strip().rstrip("等").rstrip("等）")
            if _name_ok(part): _split[part] = f
    else:
        if _name_ok(name): _clean[name] = f
CHARACTERS = {**_clean, **_split, **EXTRA}
CHARACTERS.update(EXTRA)

data = {
    "meta": {"title": "天命争鼎 · 八帝同世", "subtitle": "中国八大开国皇帝同世争锋的多智能体沙盘推演",
             "months_total": N, "months_label": months_label,
             "end_reason": epilogue.get("end_reason","ongoing"),
             "end_reason_cn": epilogue.get("end_reason_cn","未定"),
             "agents_note": "本沙盘由多智能体系统推演：8个势力代理分别扮演八朝开国君臣逐12月提交方略，天道裁定代理对撞战争/外交/天灾/生死并书写正典，史官代理撰写终局评赞。全架空推演，非真实历史。底图为中国真实省界（DataV GeoAtlas），州域由省份归组而成。"},
    "factions": factions, "regions": regions, "timeline": timeline,
    "ownership": ownership, "power": power, "epilogue": epilogue,
    "rivers": geo["rivers"], "provinces": geo["provinces"],
    "characters": CHARACTERS,
}
out = os.path.join(WEB, "sim-data.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False)
print(f"sim-data.json written: months={N} events={len(all_events)} size={os.path.getsize(out)//1024}KB")
