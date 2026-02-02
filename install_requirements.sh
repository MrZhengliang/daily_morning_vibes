#!/bin/bash
# ============================================
# 安装 Python 依赖包
# ============================================

set -e

INSTALL_DIR="/opt/daily_morning_vibes"
VENV_DIR="${INSTALL_DIR}/.venv"

echo "=========================================="
echo "安装 Python 依赖包"
echo "=========================================="

# 激活虚拟环境
source "${VENV_DIR}/bin/activate"

echo ""
echo "[1/4] 升级 pip..."
pip install --upgrade pip setuptools wheel

echo ""
echo "[2/4] 安装基础依赖..."
pip install flask pymysql python-dotenv

echo ""
echo "[3/4] 安装图片处理依赖..."
pip install pillow

echo ""
echo "[4/4] 安装其他依赖..."
pip install flask-frozen zhipuai

echo ""
echo "=========================================="
echo "验证安装..."
echo "=========================================="

python3.9 << 'PYEOF'
import sys
modules = [
    'flask',
    'pymysql',
    'PIL',  # Pillow
    'dotenv',
    'flask_frozen',
    'zhipuai'
]

failed = []
for module in modules:
    try:
        __import__(module)
        print(f"✓ {module}")
    except ImportError:
        print(f"✗ {module} - 未安装")
        failed.append(module)

if failed:
    print(f"\n错误: 以下模块未安装: {', '.join(failed)}")
    sys.exit(1)
else:
    print("\n✓ 所有依赖安装成功！")
    sys.exit(0)
PYEOF

echo ""
echo "=========================================="
echo "安装完成！"
echo "=========================================="
