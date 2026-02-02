#!/bin/bash
# ============================================
# 快速测试脚本 - 验证自动化流程
# ============================================

set -e

echo "=========================================="
echo "自动化流程测试"
echo "=========================================="
echo ""

PROJECT_DIR="/Users/fuzhengliang/Desktop/project-source/workspace-haiwai/daily_morning_vibes"
cd "${PROJECT_DIR}"

# 1. 检查虚拟环境
echo "1. 检查虚拟环境..."
if [ ! -d ".venv" ]; then
    echo "   ❌ 虚拟环境不存在"
    exit 1
fi
source .venv/bin/activate
echo "   ✅ 虚拟环境激活成功"
echo ""

# 2. 检查依赖
echo "2. 检查依赖包..."
python -c "import flask, pymysql, zhipuai" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "   ✅ 依赖包完整"
else
    echo "   ❌ 缺少依赖包，请运行: pip install -r requirements.txt"
    exit 1
fi
echo ""

# 3. 检查数据库连接
echo "3. 检查数据库连接..."
python -c "from config import Config; conn = Config.get_db_connection(); print('   ✅ 数据库连接成功'); conn.close()" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "   ❌ 数据库连接失败，请检查 .env 配置"
    exit 1
fi
echo ""

# 4. 检查 Git 配置
echo "4. 检查 Git 配置..."
git remote -v | grep -q "github.com"
if [ $? -eq 0 ]; then
    echo "   ✅ Git 仓库已配置"
else
    echo "   ❌ Git 仓库未配置"
    exit 1
fi
echo ""

# 5. 测试内容生成（可选）
echo "5. 是否测试内容生成？(y/n)"
read -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "   测试生成 1 条内容..."
    python auto_daily_generator.py
    echo "   ✅ 内容生成测试完成"
else
    echo "   ⏭️  跳过内容生成测试"
fi
echo ""

# 6. 测试静态站构建（可选）
echo "6. 是否测试静态站构建？(y/n)"
read -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "   测试构建静态站..."
    python build.py
    echo "   ✅ 静态站构建完成"
else
    echo "   ⏭️  跳过静态站构建测试"
fi
echo ""

echo "=========================================="
echo "测试完成！"
echo ""
echo "定时任务将在每天凌晨 5:00 自动运行"
echo "查看日志: tail -f logs/cron.log"
echo "=========================================="
