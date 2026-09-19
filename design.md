# 网页规格书 · index.html（单文件）—— 全屏地图沙盘（文明风）

产出：`/Users/foreverhyx/dynasty-arena/index.html`。零外部依赖，HTML+CSS+原生 JS 单文件；数据 `const SIM = {...}` 内嵌（粘贴自 sim/web/sim-data.json）。面向桌面浏览器（≥1280px），中文。

**核心理念：地图即应用。** 全屏 SVG 中国沙盘地图是主背景与主界面，所有信息以 HUD 浮层/可点开的卡片呈现——像文明游戏的上帝视角+运营复盘，而不是文章页面。

## 数据结构（sim-data.json 顶层）
- `meta`: { title, subtitle, months_total(N), months_label:[N], end_reason, end_reason_cn, agents_note }
- `factions`: { id: { name, leader, leader_title, color, crest, start_region, doctrine, bio, ministers:[{name,role,note}], leader_fate, minister_fates:[{name,fate}] } }
- `regions`: { id: { name, terrain, pop, grain, capital(州治城名), cities:[{n(名),x,y,pop(万),note(一句城市特色)}] (3~4城/州,含州治), poly:[[x,y]...] viewBox 1000×780, label:[x,y], adj:[...] } }
- `timeline`: { "1":[{month,type,faction,region,city,title,desc,actors,delta,inter}], ... } type ∈ war/politics/internal/diplomacy/economy/crisis/character
- `ownership`: { "1":{州id:势力id|"neutral"},... }
- `power`: { 势力id: { regions:[N], troops:[N], food:[N], morale:[N], stability:[N] } }
- `epilogue`: { world_verdict, end_reason_cn, fates:{势力id:{leader,ministers:[{name,fate}]}}, turning_points:[{month,title,why}], ranking:[{faction,title,score}] }

## 布局（地图全屏 + 浮层 HUD）
```
┌─────────────────────────────────────────────────────────────────┐
│ [顶栏·半透明] 天命二年七月  ▶‖ 速度 0.5/1/2x  ╓════月份滑杆══════╗ 终局徽标│
│ ┌───────────────┐                                              │
│ │◤左浮层·势力榜    │            全 屏 地 图 (SVG)                │
│ │ 8张迷你卡可点开  │   疆域色块/州界/江河/城市点位/事件标记          │
│ └───────────────┘   点击城市→城市卡；点击州→州卡；点击事件标→事件卡  │
│ ┌───────────────┐                                              │
│ │◤左下·事件推送流  │        ┌────────────────┐                  │
│ │ (最近事件滚动)   │        │右侧详情卡(点开时) │                  │
│ └───────────────┘        └────────────────┘                  │
│ [底栏·半透明] 8势力状态条(纹章/州/兵/粮微条) · 图例 · 说明          │
└─────────────────────────────────────────────────────────────────┘
```

## 地图（主背景，占满视口）
- `<svg id="map" viewBox="0 0 1000 780" preserveAspectRatio="xMidYMid meet">`，body 背景深蓝黑 `#070a10`，地图区域外画海洋波纹与罗盘装饰。
- 每州 `<g class="region">`：polygon（poly 顶点，州界 `stroke:#05070b;stroke-width:2.5`），fill=当月归属势力色（中立 `#5d5a4e`）；同势力相邻州在视觉上融为一体（州界用半透明内描边 rgba(0,0,0,.35) 细分）；势力外边界自然形成"国界"观感。
- 每势力疆域中心放**势力纹章+国名**（大标签，带阴影，灭亡后消失）；州名小字若干（label 坐标）。
- **城市**：每州 3~4 座（cities），州治=方形大点+城名，其余=圆点+小字城名；城市点用深色描边白心，当前月有事件发生的城市外圈金色光环+脉冲动画，war 事件城市红色⚔标记。
- **事件定位**：timeline 事件的 region/city 落到地图坐标；当月事件→地图对应位置显示标记（⚔战争/🤝外交/⚡危机/🏛政令 图标+微光），悬停显示 title，点击打开事件详情卡并把该处放大高亮。
- 江河装饰 polyline（黄河 `rgba(190,170,90,.5)`、长江 `rgba(110,160,220,.5)`，路径同前一版），东部海域三组波浪纹。
- 交互：悬停州→高亮+tooltip（州名/归属/人口/月粮/地形）；**点击州→右侧州详情卡**（州况+该州历史事件列表）；**点击城市→城市卡**（人口、所属、一句状态简述=该城相关最近事件 desc 或区域现状、该城相关事件时间线）；悬停底栏势力条→该势力疆域高亮其余压暗；拖拽平移+滚轮缩放（简单的 viewBox 变换即可，限制范围 0.5x~3x）。

## 浮层 HUD
- 顶栏（半透明 `rgba(10,14,22,.92)`，毛玻璃 backdrop-filter）：大字当前年月、播放/暂停、速度切换（0.5x/1x/2x，1.4s/月基准）、月份滑杆（年刻度）、右侧终局徽标。
- 左浮层·势力榜：8 张迷你卡（纹章/国名/君主/州数·兵力·民心·稳定微条），点击展开为**势力详情卡**（右侧大卡：bio/doctrine/幕僚表/逐月曲线小图/终局命运）。
- 左下·事件推送流：最近 6~8 条滚动（月+title+类型色边），点击跳到该月该位置。
- 右侧详情卡区（点开时显示，X 关闭）：州卡/城市卡/事件卡/势力卡共用此区域。
- 底栏：8 势力状态微条（可悬停高亮疆域）+ 图例（类型图标/中立色）+ 「数据图表」「天下终局」两个弹窗按钮。
- 弹窗（全屏遮罩+居中卡）：①数据图表——折线图模式切换（州数/兵力/粮/民心/稳定），8 曲线+图例+hover tooltip+当前月竖线；②天下终局——end_reason_cn 大标题+world_verdict+turning_points+ranking（未到 N 月时毛玻璃+剧透按钮）。
- URL hash `#m18` 记忆当前月；左右方向键切月；空格播放/暂停。

## 视觉
- 深蓝黑底 `#070a10`，面板半透明+1px 青蓝边 `#2a3a55`+内侧高光；强调金 `#d4af37`、战争红 `#e0503c`、信息青 `#4fc3f7`。
- UI 字体 `"PingFang SC",system-ui`；国名/纹章字用 `"Kaiti SC","STKaiti"` 点缀；数字 tabular-nums。
- 势力色（与实时页一致）：qin#8f9bb0 han#c94b3c donghan#6da85e sui#a06cc9 tang#e0ad3c song#4fa387 yuan#4f83d9 ming#d4628f。
- 数据条：高5px 圆角，底槽 #1c2436；兵力=势力色、粮=#d9a441、民心=#46b98c、稳定=#5b8def。
- 事件类型色：war⚔#e0503c / politics🏛#d4af37 / internal🌾#46b98c / diplomacy🤝#4fc3f7 / economy💰#d9a441 / crisis⚡#e8893c / character💀#9d8ec9；inter=true 加「交锋」徽标。

## 行为细节
- 播放推进：月变化→州色块更新（易手州闪金边脉冲）、城市事件标记增减、推送流推入新卡（250ms 入场）、顶栏年月大字滚动。
- 灭亡势力：疆域并入他国，势力榜卡片灰化盖「亡」印章，悬停显示 leader_fate。
- 无事月：推送流显示「本月天下无事」占位。
- 全部数据驱动自 SIM；N=months_total 自适应；无 JS 报错；document.title=meta.title。

## 质量要求
- `python3 -c "import json;d=json.load(open('sim/web/sim-data.json'));print(len(d['timeline']),len(d['ownership']),len(d['factions']),d['meta']['months_total'])"` 读通；HTML 内嵌 SIM 与之事件总数一致。
- regions 的 cities 坐标必须落在本州 poly 内（人工排布时自查）；相邻州共享边界顶点对齐（无缝拼图感）。
- 交付回复格式：`done|<一句话>|<文件大小KB>`
