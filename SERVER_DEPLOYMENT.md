# 阿里云服务器部署指南

## 前置准备

### 1. 服务器要求
- 阿里云 ECS (AliLinux 3 / CentOS 7+ / Ubuntu 18.04+)
- 至少 1GB 内存
- 已安装 MySQL 数据库
- 已配置 Git SSH 密钥

### 2. 本地准备
```bash
# 确保本地代码已提交
cd /Users/fuzhengliang/Desktop/project-source/workspace-haiwai/daily_morning_vibes
git add .
git commit -m "Fix: Add AliLinux support"
git push origin main
```

---

## 部署步骤

### 步骤 1: 连接到服务器

```bash
# SSH 登录服务器
ssh root@YOUR_SERVER_IP

# 或使用密钥
ssh -i ~/.ssh/your_key.pem root@YOUR_SERVER_IP
```

### 步骤 2: 安装系统依赖

```bash
# 上传并运行安装脚本
# (在本地执行)
scp install_server.sh root@YOUR_SERVER_IP:/tmp/
ssh root@YOUR_SERVER_IP "bash /tmp/install_server.sh"

# 或直接在服务器上执行
cd /tmp
wget https://raw.githubusercontent.com/MrZhengliang/daily_morning_vibes/main/install_server.sh
bash install_server.sh
```

### 步骤 3: 克隆项目代码

```bash
# 在服务器上执行
cd /opt/daily_morning_vibes

# 方式1: 使用 HTTPS
git clone https://github.com/MrZhengliang/daily_morning_vibes.git .

# 方式2: 使用 SSH (推荐，需要配置 SSH 密钥)
git clone git@github.com:MrZhengliang/daily_morning_vibes.git .
```

### 步骤 4: 配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑配置文件
vim .env
```

`.env` 配置示例:

```bash
# MySQL 数据库配置
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DB=daily_vibes
MYSQL_CHARSET=utf8mb4

# ZhipuAI API Key
ZHIPUAI_API_KEY=9169ae8a03ae409c8739f6c5e08bb828.JgwMF5y5nDrpaaay
```

### 步骤 5: 配置 Git 推送权限

```bash
# 生成 SSH 密钥 (如果还没有)
ssh-keygen -t ed25519 -C "your_email@example.com"

# 查看公钥
cat ~/.ssh/id_ed25519.pub

# 将公钥添加到 GitHub:
# 1. 访问 https://github.com/settings/keys
# 2. 点击 "New SSH key"
# 3. 粘贴公钥内容

# 测试 SSH 连接
ssh -T git@github.com
```

### 步骤 6: 初始化数据库

```bash
# 创建数据库
mysql -u root -p

CREATE DATABASE daily_vibes CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE daily_vibes;

-- 创建内容表
CREATE TABLE content_library (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category VARCHAR(50) NOT NULL,
    text_cn TEXT NOT NULL,
    text_en TEXT NOT NULL,
    image_oss_url VARCHAR(500),
    status TINYINT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_category (category),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

EXIT;
```

### 步骤 7: 测试运行

```bash
# 激活虚拟环境
source /opt/daily_morning_vibes/.venv/bin/activate

# 测试内容生成
cd /opt/daily_morning_vibes
python auto_daily_generator.py

# 测试静态站构建
python build.py

# 完整部署测试
bash deploy_server.sh
```

### 步骤 8: 验证定时任务

```bash
# 查看定时任务
crontab -l

# 应该看到类似输出:
# 0 5 * * * cd /opt/daily_morning_vibes && bash deploy_server.sh >> /var/log/daily_vibes/cron.log 2>&1

# 查看日志
tail -f /var/log/daily_vibes/cron.log
```

---

## 常用命令

### 查看日志

```bash
# Cron 日志
tail -f /var/log/daily_vibes/cron.log

# 生成日志
tail -f /var/log/daily_vibes/generator_$(date +%Y%m%d).log

# 部署日志
tail -f /var/log/daily_vibes/deploy_*.log
```

### 手动触发任务

```bash
cd /opt/daily_morning_vibes
bash deploy_server.sh
```

### 修改定时任务时间

```bash
# 编辑定时任务
crontab -e

# 修改时间格式:
# 0 5 * * *    => 每天凌晨 5:00
# 0 23 * * *   => 每天晚上 23:00
# 0 */6 * * *  => 每 6 小时一次

# 保存后重新加载服务 (如果需要)
sudo systemctl reload crond
```

### 查看 Git 状态

```bash
cd /opt/daily_morning_vibes
git status
git log --oneline -5
```

---

## 故障排查

### 1. 权限问题

```bash
# 确保目录权限正确
sudo chown -R $USER:$USER /opt/daily_morning_vibes
sudo chown -R $USER:$USER /var/log/daily_vibes
```

### 2. Python 依赖问题

```bash
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Git 推送失败

```bash
# 检查 Git 配置
git config --list

# 检查远程仓库
git remote -v

# 测试连接
ssh -T git@github.com
```

### 4. Cron 任务不执行

```bash
# 查看 cron 日志 (CentOS/AliLinux)
sudo tail -f /var/log/cron

# 查看 cron 是否运行
sudo systemctl status crond

# 重启 cron 服务
sudo systemctl restart crond
```

### 5. 数据库连接失败

```bash
# 测试数据库连接
mysql -h localhost -u root -p

# 检查 .env 配置
cat /opt/daily_morning_vibes/.env
```

---

## 防火墙配置

```bash
# 如果需要开放端口 (可选)
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --reload
```

---

## 监控和告警 (可选)

### 安装监控工具

```bash
# 使用简单的监控脚本
cat > /opt/daily_morning_vibes/monitor.sh << 'EOF'
#!/bin/bash
LOG_FILE="/var/log/daily_vibes/cron.log"
if [ -f "$LOG_FILE" ]; then
    LAST_RUN=$(tail -1 "$LOG_FILE" | grep "部署任务完成")
    if [ -z "$LAST_RUN" ]; then
        echo "警告: 最后一次任务可能未完成"
        # 可以添加邮件或钉钉通知
    fi
fi
EOF

chmod +x /opt/daily_morning_vibes/monitor.sh
```

---

## Vercel 部署配置

确保 Vercel 配置正确:

1. 访问 https://vercel.com/
2. 导入 GitHub 仓库
3. 配置构建命令: 留空 (使用预构建的 build 目录)
4. 配置输出目录: `build`
5. 配置自定义域名 (如需要)

---

## 更新和维护

### 更新代码

```bash
cd /opt/daily_morning_vibes
git pull origin main
```

### 重新部署

```bash
bash deploy_server.sh
```

### 备份数据库

```bash
# 创建备份脚本
cat > /opt/daily_morning_vibes/backup_db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/backups/daily_vibes"
mkdir -p "$BACKUP_DIR"
mysqldump -u root -p daily_vibes > "$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql"
# 保留最近 7 天的备份
find "$BACKUP_DIR" -name "backup_*.sql" -mtime +7 -delete
EOF

chmod +x /opt/daily_morning_vibes/backup_db.sh
```

---

## 支持

如有问题，请查看:
- 项目日志: `/var/log/daily_vibes/`
- Cron 日志: `/var/log/cron`
- GitHub Issues: https://github.com/MrZhengliang/daily_morning_vibes/issues
