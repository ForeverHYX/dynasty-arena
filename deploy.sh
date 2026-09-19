#!/bin/bash
# 推演每阶段裁定后运行：重建数据 → 提交 → 推送（GitHub Pages 约 1 分钟后自动更新）
cd "$(dirname "$0")"
python3 build_data.py && python3 build_progress.py
git add -A
git commit -m "推演数据更新: $(python3 -c "import json;print(json.load(open('progress.json'))['now_label'])")" >/dev/null
git push origin main
echo "pushed -> https://foreverhyx.github.io/dynasty-arena/"
