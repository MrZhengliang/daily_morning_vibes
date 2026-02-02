#!/bin/bash
# ============================================
# 快速设置定时任务脚本
# ============================================

INSTALL_DIR="/opt/daily_morning_vibes"
LOG_DIR="/var/log/daily_vibes"

echo "=========================================="
echo "设置定时任务"
echo "=========================================="
echo ""

# 检查目录是否存在
if [ ! -d "${INSTALL_DIR}" ]; then
    echo "错误: 项目目录不存在: ${INSTALL_DIR}"
    echo "请先运行 install_server.sh 或手动上传项目文件"
    exit 1
fi

# 创建日志目录
sudo mkdir -p "${LOG_DIR}"
sudo chown -R $USER:$USER "${LOG_DIR}"

# 显示当前 crontab
echo "当前定时任务:"
crontab -l 2>/dev/null || echo "(无定时任务)"
echo ""

# 询问是否要设置定时任务
read -p "是否要设置每天凌晨 5:00 自动执行? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # 检查是否已存在
    if crontab -l 2>/dev/null | grep -q "deploy_server.sh"; then
        echo "定时任务已存在，将被更新"
        # 移除旧任务
        crontab -l 2>/dev/null | grep -v "deploy_server.sh" | crontab -
    fi

    # 添加新任务
    (crontab -l 2>/dev/null; echo "0 5 * * * cd ${INSTALL_DIR} && bash deploy_server.sh >> ${LOG_DIR}/cron.log 2>&1") | crontab -

    echo ""
    echo "✓ 定时任务设置成功!"
    echo ""
    echo "定时任务详情:"
    crontab -l | grep deploy_server.sh
    echo ""
    echo "日志文件: ${LOG_DIR}/cron.log"
    echo ""
    echo "其他有用的命令:"
    echo "  查看定时任务: crontab -l"
    echo "  删除定时任务: crontab -e (删除相关行)"
    echo "  查看运行日志: tail -f ${LOG_DIR}/cron.log"
    echo "  立即测试运行: cd ${INSTALL_DIR} && bash deploy_server.sh"
else
    echo "跳过定时任务设置"
fi
