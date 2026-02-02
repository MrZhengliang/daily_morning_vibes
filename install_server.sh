#!/bin/bash
# ============================================
# Daily Morning Vibes - 服务器环境安装脚本
# 适用于: CentOS 7/8, Ubuntu 18.04+, AliLinux 3
# ============================================

set -e

# ==================== 配置区域 ====================
INSTALL_DIR="/opt/daily_morning_vibes"
LOG_DIR="/var/log/daily_vibes"
PYTHON_VERSION="3.9"
VENV_DIR="${INSTALL_DIR}/.venv"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ==================== 函数定义 ====================

print_step() {
    echo -e "${GREEN}[步骤] $1${NC}"
}

print_info() {
    echo -e "${YELLOW}[信息] $1${NC}"
}

print_success() {
    echo -e "${GREEN}[成功] $1${NC}"
}

print_error() {
    echo -e "${RED}[错误] $1${NC}"
}

# 检测系统类型
detect_os() {
    print_step "检测操作系统..."
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        OS_VERSION=$VERSION_ID
        print_success "检测到系统: $OS $OS_VERSION"
    else
        print_error "无法检测操作系统"
        exit 1
    fi
}

# 安装系统依赖
install_system_dependencies() {
    print_step "安装系统依赖..."

    case $OS in
        centos|rhel|rocky|almalinux|alinux)
            sudo yum install -y epel-release
            sudo yum install -y python39 python39-pip python39-devel git mysql-client \
                libffi-devel openssl-devel gcc gcc-c++ make
            ;;
        ubuntu|debian)
            sudo apt-get update
            sudo apt-get install -y python3.9 python3.9-venv python3.9-dev git mysql-client \
                libffi-dev libssl-dev gcc g++ make build-essential
            ;;
        *)
            print_error "不支持的操作系统: $OS"
            exit 1
            ;;
    esac

    print_success "系统依赖安装完成"
}

# 安装 Pillow 图片依赖
install_image_dependencies() {
    print_step "安装图片处理依赖..."

    case $OS in
        centos|rhel|rocky|almalinux|alinux)
            sudo yum install -y libjpeg-turbo-devel zlib-devel freetype-devel lcms2-devel \
                libwebp-devel tcl-devel tk-devel
            ;;
        ubuntu|debian)
            sudo apt-get install -y libjpeg-dev zlib1g-dev libfreetype6-dev liblcms2-dev \
                libwebp-dev libtcl8.6 libtk8.6
            ;;
    esac

    print_success "图片处理依赖安装完成"
}

# 创建项目目录
setup_project_dir() {
    print_step "设置项目目录..."

    sudo mkdir -p "${INSTALL_DIR}"
    sudo mkdir -p "${LOG_DIR}"
    sudo chown -R $USER:$USER "${INSTALL_DIR}"
    sudo chown -R $USER:$USER "${LOG_DIR}"

    print_success "项目目录创建完成: ${INSTALL_DIR}"
}

# 创建虚拟环境
create_virtualenv() {
    print_step "创建 Python 虚拟环境..."

    if [ ! -d "${VENV_DIR}" ]; then
        python3.9 -m venv "${VENV_DIR}"
        print_success "虚拟环境创建完成"
    else
        print_info "虚拟环境已存在，跳过创建"
    fi

    # 激活虚拟环境并升级 pip
    source "${VENV_DIR}/bin/activate"
    pip install --upgrade pip setuptools wheel
}

# 安装 Python 依赖
install_python_dependencies() {
    print_step "安装 Python 依赖包..."

    source "${VENV_DIR}/bin/activate"

    # 基础依赖
    pip install flask pymysql pillow python-dotenv flask-frozen

    # ZhipuAI SDK
    pip install zhipuai

    print_success "Python 依赖安装完成"
}

# 配置 crontab 定时任务
setup_crontab() {
    print_step "配置定时任务 (每天凌晨 5:00 执行)..."

    # 获取当前 crontab（如果有的话）
    CRONTAB_BACKUP=$(crontab -l 2>/dev/null || true)

    # 检查是否已经存在我们的任务
    if echo "${CRONTAB_BACKUP}" | grep -q "deploy_server.sh"; then
        print_info "定时任务已存在，跳过配置"
        return
    fi

    # 添加新的定时任务
    (echo "${CRONTAB_BACKUP}"; echo "") | crontab -

    # 添加定时任务: 每天凌晨 5:00 执行
    (crontab -l 2>/dev/null; echo "0 5 * * * cd ${INSTALL_DIR} && bash deploy_server.sh >> ${LOG_DIR}/cron.log 2>&1") | crontab -

    print_success "定时任务配置完成"
    print_info "任务将在每天凌晨 5:00 自动执行"
    print_info "查看定时任务: crontab -l"
}

# 显示完成信息
show_completion_info() {
    print_step "=========================================="
    print_success "服务器环境安装完成!"
    print_step "=========================================="
    echo ""
    echo "下一步操作:"
    echo ""
    echo "1. 上传项目文件到服务器:"
    echo "   scp -r /Users/fuzhengliang/Desktop/project-source/workspace-haiwai/daily_morning_vibes/* root@YOUR_SERVER_IP:${INSTALL_DIR}/"
    echo ""
    echo "2. 配置数据库连接:"
    echo "   编辑 ${INSTALL_DIR}/.env 文件"
    echo ""
    echo "3. 配置 Git SSH 密钥:"
    echo "   ssh-keygen -t ed25519 -C \"your_email@example.com\""
    echo "   cat ~/.ssh/id_ed25519.pub  # 添加到 GitHub"
    echo ""
    echo "4. 手动测试部署:"
    echo "   cd ${INSTALL_DIR}"
    echo "   bash deploy_server.sh"
    echo ""
    echo "5. 查看日志:"
    echo "   tail -f ${LOG_DIR}/deploy_*.log"
    echo ""
    echo "6. 查看定时任务:"
    echo "   crontab -l"
    echo ""
}

# ==================== 主流程 ====================
main() {
    echo "=========================================="
    echo "  Daily Morning Vibes - 服务器安装"
    echo "=========================================="
    echo ""

    detect_os
    install_system_dependencies
    install_image_dependencies
    setup_project_dir
    create_virtualenv
    install_python_dependencies
    setup_crontab
    show_completion_info

    echo "=========================================="
    print_success "安装完成!"
    echo "=========================================="
}

# 执行主流程
main "$@"
