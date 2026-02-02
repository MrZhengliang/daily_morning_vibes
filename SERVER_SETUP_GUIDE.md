# Daily Morning Vibes - 阿里云服务器自动化部署指南

## 方案概述

每天凌晨 5:00 自动执行以下任务：
1. 为每个分类生成 3 条新内容（5 个分类 × 3 条 = 15 条/天）
2. 构建静态网站
3. 推送到 GitHub (自动部署到 Vercel)

## 文件说明

| 文件 | 说明 |
|------|------|
| `auto_daily_generator.py` | 自动内容生成脚本（每个分类3条）|
| `deploy_server.sh` | 主部署脚本（生成+构建+推送）|
| `install_server.sh` | 服务器环境一键安装脚本 |
| `setup_cron.sh` | 快速设置定时任务脚本 |

---

## 快速开始

### 1. 服务器安装（推荐）

在你的阿里云服务器上执行：

```bash
# 下载并运行安装脚本
curl -fsSL https://raw.githubusercontent.com/你的仓库/main/install_server.sh -o install_server.sh
bash install_server.sh
```

安装脚本会自动：
- 安装 Python 3.9 和系统依赖
- 创建虚拟环境
- 安装 Python 依赖包
- 配置定时任务

### 2. 上传项目文件

```bash
# 从本地上传到服务器
scp -r /Users/fuzhengliang/Desktop/project-source/workspace-haiwai/daily_morning_vibes/* root@YOUR_SERVER_IP:/opt/daily_morning_vibes/

# 或者使用 rsync
rsync -avz --exclude='.venv' --exclude='__pycache__' \
  /Users/fuzhengliang/Desktop/project-source/workspace-haiwai/daily_morning_vibes/ \
  root@YOUR_SERVER_IP:/opt/daily_morning_vibes/
```

### 3. 配置环境变量

在服务器上编辑 `.env` 文件：

```bash
ssh root@YOUR_SERVER_IP
cd /opt/daily_morning_vibes
nano .env  # 或 vim .env
```

配置内容：
```env
# MySQL 数据库配置
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DB=daily_vibes
MYSQL_CHARSET=utf8mb4

# 阿里云 OSS 配置（如果使用）
OSS_ACCESS_KEY_ID=your_access_key
OSS_ACCESS_KEY_SECRET=your_secret
OSS_BUCKET_NAME=your_bucket
OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
```

### 4. 配置 Git SSH

```bash
# 生成 SSH 密钥
ssh-keygen -t ed25519 -C "your_email@example.com"

# 查看公钥，添加到 GitHub
cat ~/.ssh/id_ed25519.pub

# 测试连接
ssh -T git@github.com
```

### 5. 手动测试部署

```bash
cd /opt/daily_morning_vibes
bash deploy_server.sh
```

检查日志确认成功：
```bash
tail -f /var/log/daily_vibes/deploy_*.log
```

---

## 定时任务说明

定时任务会在每天凌晨 5:00 自动执行 `deploy_server.sh`

### 查看定时任务
```bash
crontab -l
```

### 编辑定时任务
```bash
crontab -e
```

### 修改执行时间
crontab 格式：`分钟 小时 日 月 周`

示例：
```bash
# 凌晨 5:00
0 5 * * * cd /opt/daily_morning_vibes && bash deploy_server.sh

# 早上 8:00
0 8 * * * cd /opt/daily_morning_vibes && bash deploy_server.sh

# 每天凌晨 5:00 和 下午 5:00
0 5,17 * * * cd /opt/daily_morning_vibes && bash deploy_server.sh

# 每 6 小时执行一次
0 */6 * * * cd /opt/daily_morning_vibes && bash deploy_server.sh
```

---

## 日志管理

### 日志位置
```bash
/var/log/daily_vibes/
├── generator_20250202.log    # 生成器日志
├── deploy_20250202_050001.log # 部署日志
└── cron.log                  # 定时任务日志
```

### 查看实时日志
```bash
# 生成器日志
tail -f /var/log/daily_vibes/generator_*.log

# 部署日志
tail -f /var/log/daily_vibes/deploy_*.log

# 定时任务日志
tail -f /var/log/daily_vibes/cron.log
```

### 清理旧日志（30天前）
```bash
find /var/log/daily_vibes -name "*.log" -mtime +30 -delete
```

---

## 手动执行命令

### 仅生成内容
```bash
cd /opt/daily_morning_vibes
.venv/bin/python auto_daily_generator.py
```

### 仅构建静态站
```bash
cd /opt/daily_morning_vibes
.venv/bin/python build.py
```

### 完整部署流程
```bash
cd /opt/daily_morning_vibes
bash deploy_server.sh
```

---

## 故障排查

### 1. 检查定时任务是否执行
```bash
# 查看 cron 日志
tail -f /var/log/daily_vibes/cron.log

# 查看 syslog 中的 cron 记录
grep CRON /var/log/syslog  # Ubuntu/Debian
grep CRON /var/log/cron    # CentOS
```

### 2. 测试脚本是否正常
```bash
cd /opt/daily_morning_vibes
bash -x deploy_server.sh  # 调试模式
```

### 3. 检查数据库连接
```bash
.venv/bin/python -c "from config import Config; print(Config.get_db_connection())"
```

### 4. 检查 Git 推送
```bash
cd /opt/daily_morning_vibes
git status
git remote -v
git push origin main --dry-run  # 模拟推送
```

### 5. 常见问题

**问题：字体找不到**
```bash
# 安装字体
sudo apt-get install fonts-dejavu-core  # Ubuntu
sudo yum install dejavu-sans-fonts      # CentOS

# 或者上传自定义字体到项目根目录
```

**问题：数据库连接失败**
- 检查 `.env` 配置
- 确认 MySQL 服务运行：`systemctl status mysql`
- 检查防火墙：`firewall-cmd --list-all`

**问题：Git 推送失败**
- 配置 SSH 密钥
- 测试连接：`ssh -T git@github.com`
- 检查仓库权限

---

## 修改配置

### 修改每个分类生成数量

编辑 `auto_daily_generator.py`：

```python
# 第 24 行
QUOTES_PER_CATEGORY = 3  # 改成你想要的数量
```

### 修改分类

编辑 `auto_daily_generator.py`：

```python
# 第 18-24 行
CATEGORIES = [
    "morning",
    "motivation",
    "gratitude",
    "mindfulness",
    "positivity"
]
```

---

## 目录结构

```
/opt/daily_morning_vibes/
├── .env                      # 环境变量配置
├── .venv/                    # Python 虚拟环境
├── auto_daily_generator.py   # 自动生成脚本
├── deploy_server.sh          # 部署脚本
├── install_server.sh         # 安装脚本
├── setup_cron.sh             # 定时任务设置
├── config.py                 # 配置文件
├── generatorclaude.py        # 原生成脚本
├── build.py                  # 构建脚本
├── app.py                    # Flask 应用
├── assets/
│   └── backgrounds/          # 背景图片目录
├── static/
│   └── images/               # 生成的图片
├── templates/                # HTML 模板
└── build/                    # 静态站输出
```

---

## 联系与支持

如有问题，请检查日志文件或联系技术支持。
