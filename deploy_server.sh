#!/bin/bash
# ============================================
# Daily Morning Vibes - 自动部署脚本
# 功能: 生成内容 + 构建静态站 + 推送到GitHub
# ============================================

set -e  # 遇到错误立即退出

# ==================== 配置区域 ====================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="/var/log/daily_vibes"
LOG_FILE="${LOG_DIR}/deploy_$(date +%Y%m%d_%H%M%S).log"
PROJECT_DIR="${SCRIPT_DIR}"
VENV_DIR="${PROJECT_DIR}/.venv"
PYTHON_BIN="${VENV_DIR}/bin/python"

# Git 配置
GIT_REPO="https://github.com/MrZhengliang/daily_morning_vibes.git"
GIT_BRANCH="main"

# ==================== 函数定义 ====================

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "${LOG_FILE}"
}

error_exit() {
    log "错误: $1"
    exit 1
}

# 创建日志目录
setup_logging() {
    mkdir -p "${LOG_DIR}"
    log "=========================================="
    log "开始部署任务"
    log "=========================================="
}

# 检查虚拟环境
check_venv() {
    log "检查虚拟环境..."
    if [ ! -d "${VENV_DIR}" ]; then
        error_exit "虚拟环境不存在: ${VENV_DIR}"
    fi

    if [ ! -f "${PYTHON_BIN}" ]; then
        error_exit "Python 不存在: ${PYTHON_BIN}"
    fi

    log "✓ 虚拟环境检查通过"
}

# 步骤1: 生成内容
generate_content() {
    log ""
    log "步骤1: 开始生成内容..."
    cd "${PROJECT_DIR}"

    "${PYTHON_BIN}" auto_daily_generator.py || error_exit "内容生成失败"
    log "✓ 内容生成完成"
}

# 步骤2: 构建静态网站
build_site() {
    log ""
    log "步骤2: 开始构建静态网站..."
    cd "${PROJECT_DIR}"

    "${PYTHON_BIN}" build.py || error_exit "静态站构建失败"
    log "✓ 静态站构建完成"
}

# 步骤3: Git 推送
git_push() {
    log ""
    log "步骤3: 推送到 GitHub..."

    # 检查是否有更改
    cd "${PROJECT_DIR}"
    if git diff --quiet && git diff --cached --quiet; then
        log "没有文件更改，跳过 Git 推送"
        return
    fi

    # 添加所有更改
    git add .

    # 提交
    git commit -m "Auto deploy $(date '+%Y-%m-%d %H:%M:%S')

- Generated new quotes
- Built static site
- Auto deployment" || {
        log "警告: Git commit 没有更改（可能已被提交）"
    }

    # 推送
    git push origin "${GIT_BRANCH}" || error_exit "Git 推送失败"
    log "✓ Git 推送完成"
}

# 清理旧日志
cleanup_old_logs() {
    log ""
    log "清理 30 天前的旧日志..."
    find "${LOG_DIR}" -name "*.log" -mtime +30 -delete 2>/dev/null || true
    log "✓ 日志清理完成"
}

# ==================== 主流程 ====================
main() {
    setup_logging
    check_venv

    local start_time=$(date +%s)

    generate_content
    build_site
    git_push
    cleanup_old_logs

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    log ""
    log "=========================================="
    log "部署任务完成! 总耗时: ${duration} 秒"
    log "=========================================="
}

# 执行主流程
main "$@"
