#!/usr/bin/env python3
"""从真实省界 GeoJSON 生成沙盘几何：省份归组十二州 + 真实经纬度城市 + 江河线。"""
import json, math, os

SIM = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sim")
gj = json.load(open(os.path.join(SIM, "china-geo.json"), encoding="utf-8"))

# 省份 → 区域归组（None = 化外之地）
GROUP = {
    150000:"mobei",                                  # 内蒙古
    620000:"longxi",640000:"longxi",                 # 甘肃 宁夏
    610000:"guanzhong",                              # 陕西
    140000:"hedong",                                 # 山西
    130000:"hebei",110000:"hebei",120000:"hebei",    # 河北 京津
    370000:"shandong",                               # 山东
    410000:"zhongyuan",                              # 河南
    510000:"bashu",500000:"bashu",                   # 四川 重庆
    420000:"jingchu",430000:"jingchu",               # 湖北 湖南
    340000:"jianghuai",                              # 安徽
    320000:"jiangnan",330000:"jiangnan",310000:"jiangnan",360000:"jiangnan",350000:"jiangnan",  # 江苏 浙江 上海 江西 福建
    440000:"lingnan",450000:"lingnan",460000:"lingnan",710000:"lingnan",810000:"lingnan",820000:"lingnan",  # 两广 海南 台湾 港澳
}
WILD = {650000:"西域",540000:"青藏",630000:"青藏",210000:"辽东",220000:"关外",230000:"关外"}

# 投影：等距圆柱（标准纬线 35°N），拟合到 viewBox 1000×780（留边）
VW, VH, PAD = 1000, 780, 18
LON0, LON1, LAT0, LAT1 = 73, 136, 17.5, 54.5   # 中国大陆与海南范围
KX = math.cos(math.radians(35))
span_x = (LON1-LON0)*KX; span_y = (LAT1-LAT0)
scale = min((VW-2*PAD)/span_x, (VH-2*PAD)/span_y)
def proj(lon, lat):
    x = (lon-LON0)*KX*scale + (VW - span_x*scale)/2
    y = VH - ((lat-LAT0)*scale + (VH - span_y*scale)/2)
    return [round(x,1), round(y,1)]

# Douglas-Peucker 简化
def dp(pts, tol):
    if len(pts) < 4: return pts
    def d(p, a, b):
        ax,ay,bx,by = a[0],a[1],b[0],b[1]
        dx,dy = bx-ax, by-ay
        L = math.hypot(dx,dy)
        if L == 0: return math.hypot(p[0]-ax, p[1]-ay)
        t = max(0, min(1, ((p[0]-ax)*dx+(p[1]-ay)*dy)/(L*L)))
        return math.hypot(p[0]-(ax+t*dx), p[1]-(ay+t*dy))
    stk=[(0,len(pts)-1)]; keep=[False]*len(pts); keep[0]=keep[-1]=True
    while stk:
        i,j = stk.pop()
        if j<=i+1: continue
        dmax, imax = 0, None
        for k in range(i+1,j):
            dd = d(pts[k], pts[i], pts[j])
            if dd>dmax: dmax, imax = dd, k
        if dmax>tol:
            keep[imax]=True; stk.append((i,imax)); stk.append((imax,j))
    return [p for p,k in zip(pts,keep) if k]

def polys_of(feat):
    """MultiPolygon → [[ [x,y],... ], ...]"""
    out=[]
    geom=feat["geometry"]
    mp = geom["coordinates"] if geom["type"]=="MultiPolygon" else [geom["coordinates"]]
    for poly in mp:
        ring = poly[0]  # 外环
        pts=[proj(c[0],c[1]) for c in ring]
        if any(p[1] > 785 or p[1] < -5 or p[0] < -5 or p[0] > 1005 for p in pts):
            continue  # 舍弃远离主图的岛礁（如南沙）
        pts=dp(pts,1.1)
        if len(pts)>=4: out.append(pts)
    return out

provinces=[]
for f in gj["features"]:
    ad=f["properties"]["adcode"]; name=f["properties"]["name"]
    polys=polys_of(f)
    if not polys: continue
    provinces.append({"adcode":ad,"name":name,
                      "region":GROUP.get(ad), "wild":WILD.get(ad),
                      "polys":polys})

# 城市（真实经纬度）
CITIES={
 "mobei":[("开平",115.98,42.03,25,"元上都，金莲川幕府龙兴之地"),("丰州",111.75,40.85,20,"漠南边市，青城雏形"),("临潢",118.88,42.29,20,"契丹旧壤，草原东门户")],
 "longxi":[("姑臧",102.64,37.93,45,"凉州治所，河西第一雄城"),("金城",103.83,36.06,35,"黄河渡口，陇右门户"),("狄道",103.86,35.37,30,"洮河谷地要塞"),("祁山",105.23,34.22,25,"陇右粮道咽喉")],
 "guanzhong":[("长安",108.94,34.34,150,"八水长安，天下第一都会"),("陈仓",107.14,34.37,60,"暗度陈仓的故道口"),("冯翊",110.09,34.79,50,"左辅重镇，拱卫京畿"),("上郡",109.49,36.59,40,"北地边郡，直面草原")],
 "hedong":[("晋阳",112.55,37.87,90,"表里山河的太原雄城"),("平阳",111.52,36.09,60,"汾河谷地粮仓"),("上党",113.08,36.35,55,"天下之脊"),("蒲坂",110.44,34.83,45,"蒲津渡，入关中桥头堡")],
 "hebei":[("邺城",114.62,36.34,120,"河北第一雄城"),("蓟",116.40,39.90,90,"幽燕重镇，北控塞外"),("常山",114.57,38.04,70,"真定府，燕赵慷慨之地"),("信都",115.42,37.55,60,"冀州腹心")],
 "shandong":[("临淄",118.31,36.81,90,"海岱之间第一都会"),("曲阜",116.99,35.58,70,"孔孟故里"),("历城",117.00,36.67,55,"济水之南"),("琅琊",120.38,36.07,45,"滨海港城")],
 "zhongyuan":[("汴梁",114.31,34.80,140,"汴渠漕运中枢"),("洛阳",112.45,34.62,110,"十三朝古都，天下之中"),("荥阳",113.45,34.79,55,"鸿沟敖仓所在"),("宋城",115.65,34.41,60,"商丘要冲"),("许昌",113.85,34.03,55,"颍川要地，曹魏旧都")],
 "jianghuai":[("寿春",116.79,32.63,70,"淮上锁钥，淝水故战场"),("合肥",117.28,31.86,55,"巢湖门户"),("钟离",117.57,32.94,45,"淮河中游重镇")],
 "bashu":[("成都",104.07,30.67,110,"天府锦官城"),("涪城",104.74,31.47,50,"金牛道要冲"),("梓潼",105.16,31.64,50,"剑阁屏障"),("江州",106.55,29.56,55,"两江汇流，巴渝门户")],
 "jingchu":[("江陵",112.24,30.33,90,"荆楚心脏"),("襄阳",112.14,32.04,75,"南船北马，天下腰膂"),("夏口",114.31,30.60,70,"两江交汇，水师锁钥"),("长沙",112.94,28.23,55,"湘水米粮之仓")],
 "jiangnan":[("建康",118.80,32.06,120,"龙蟠虎踞，六朝金粉"),("吴",120.62,31.32,65,"姑苏繁华"),("广陵",119.41,32.39,60,"运河长江第一渡"),("杭州",120.16,30.29,75,"钱塘形胜"),("洪州",115.89,28.68,55,"豫章故郡"),("福州",119.30,26.08,50,"闽江都会")],
 "lingnan":[("番禺",113.27,23.13,60,"南海商港"),("桂林",110.30,25.28,45,"岭南门户，灵渠通湘"),("韶州",113.60,24.81,40,"五岭孔道"),("龙川",114.93,24.10,35,"东江要津")],
}
REGION_NAME={"mobei":"漠北草原","longxi":"陇右凉州","guanzhong":"关中","hedong":"河东","hebei":"河北",
 "shandong":"山东","zhongyuan":"中原","jianghuai":"江淮","bashu":"巴蜀","jingchu":"荆楚",
 "jiangnan":"江南","lingnan":"岭南"}
regions={}
for rid,clist in CITIES.items():
    cities=[{"n":n,**{"x":proj(lon,lat)[0],"y":proj(lon,lat)[1]},"pop":p,"note":note} for n,lon,lat,p,note in clist]
    rpolys=[p for pr in provinces if pr["region"]==rid for p in pr["polys"]]
    allpts=[pt for poly in rpolys for pt in poly]
    # 区域标签取诸省面加重心的均值（偏南一点点更好看）
    cx=sum(p[0] for p in allpts)/len(allpts); cy=sum(p[1] for p in allpts)/len(allpts)
    regions[rid]={"name":REGION_NAME[rid],"label":[round(cx,0),round(cy,0)],
                  "cities":cities,"capital":cities[0]["n"]}

# 江河（真实走向的简化折线，经纬度）
HUANG=[(102.5,36.4),(103.8,36.1),(105.0,37.5),(106.3,38.9),(107.5,40.3),(109.5,40.7),(111.2,40.5),(112.5,39.5),(111.5,38.2),(110.5,36.5),(110.4,34.8),(111.5,34.7),(113.6,34.9),(115.0,35.5),(116.5,35.9),(117.9,36.9),(118.9,37.5),(119.3,37.8)]
CHANG=[(98.5,28.3),(100.5,28.4),(102.5,28.9),(104.4,28.6),(106.2,29.4),(108.4,30.4),(110.5,30.6),(112.5,30.4),(114.3,30.6),(116.2,30.9),(117.6,31.4),(118.8,32.0),(120.0,32.4),(121.2,32.0),(121.9,31.4)]
rivers={"huang":[proj(*p) for p in HUANG],"chang":[proj(*p) for p in CHANG]}

out={"viewBox":[VW,VH],"provinces":provinces,"regions":regions,"rivers":rivers}
path=os.path.join(SIM,"geometry2.json")
json.dump(out,open(path,"w",encoding="utf-8"),ensure_ascii=False,separators=(",",":"))
print("geometry2.json:",os.path.getsize(path)//1024,"KB; provinces:",len(provinces),
      "; play provinces:",sum(1 for p in provinces if p["region"]),
      "; wild:",sum(1 for p in provinces if p["wild"]))
