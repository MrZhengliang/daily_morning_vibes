#!/bin/bash
# ============================================
# 从 GitHub 拉取最新代码 + 部署
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="/var/log/daily_vibes"
LOG_FILE="${LOG_DIR}/update_and_deploy_$(date +%Y%m%d_%H%M%S).log"

mkdir -p "${LOG_DIR}"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "${LOG_FILE}"
}

log "=========================================="
log "开始自动更新和部署任务"
log "=========================================="

cd "${SCRIPT_DIR}"

# 步骤1: 拉取最新代码
log "步骤1: 从 GitHub 拉取最新代码..."
git pull origin main || {
    log "警告: Git pull 失败，使用本地代码继续"
}

# 步骤2: 生成内容
log "步骤2: 生成内容..."
source .venv/bin/activate
python auto_daily_generator.py || {
    log "错误: 内容生成失败"
    exit 1
}

# 步骤3: 构建静态站
log "步骤3: 构建静态网站..."
python build.py || {
    log "错误: 静态站构建失败"
    exit 1
}

# 步骤4: Git 推送（如果有更改）
log "步骤4: 推送到 GitHub..."
if git diff --quiet && git diff --cached --quiet; then
    log "没有文件更改，跳过推送"
else
    git add .
    git commit -m "Auto deploy $(date '+%Y-%m-%d %H:%M:%S')" || {
        log "注意: 没有需要提交的更改"
    }
    git push origin main || {
        log "警告: Git push 失败"
    }
fi

log "=========================================="
log "部署任务完成！"
log "=========================================="
