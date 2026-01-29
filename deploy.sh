#!/bin/bash

# 1. 生产内容 (你的生成脚本)
python3 generator.py

# 2. 静态化打包
python3 build.py

# 3. 推送到 GitHub
# 只有 build 文件夹里的内容是我们需要发布的
# 我们利用 git subtree 或者暴力一点，只把 build 目录变成 git 仓库推上去
# 这里用最简单稳妥的方法：把 build 目录推送到 gh-pages 分支

cd build
git init
git checkout -b main
git add .
git commit -m "Auto deploy $(date)"
# 注意：这里会强制覆盖远程仓库，适合静态站
git push -f git@github.com:981233589@qq.com/daily_morning_vibes.git main
