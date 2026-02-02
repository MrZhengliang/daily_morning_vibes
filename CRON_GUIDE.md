# 定时任务使用指南

## 当前配置

- **执行时间**: 每天凌晨 5:00
- **执行路径**: `/Users/fuzhengliang/Desktop/project-source/workspace-haiwai/daily_morning_vibes`
- **日志目录**: `logs/`

## 常用命令

### 查看定时任务
```bash
crontab -l
```

### 编辑定时任务
```bash
crontab -e
```

### 删除定时任务
```bash
crontab -l 2>/dev/null | grep -v "deploy_server.sh" | crontab -
```

### 查看运行日志
```bash
# 查看最新日志
tail -f logs/cron.log

# 查看今天的生成日志
ls -lt logs/ | head -5
cat logs/generator_$(date +%Y%m%d).log

# 查看最近的部署日志
cat logs/deploy_*.log | tail -100
```

### 手动测试运行
```bash
# 完整部署流程
bash deploy_server.sh

# 单独测试内容生成
python auto_daily_generator.py

# 单独测试静态站构建
python build.py
```

### 临时修改执行时间
例如改成每天晚上 11:00 执行：
```bash
# 编辑定时任务
crontab -e

# 将 0 5 * * * 改为 0 23 * * *
```

## 工作流程

```
Cron (每天 5:00)
    ↓
deploy_server.sh
    ├─ auto_daily_generator.py (生成15条内容)
    ├─ build.py (构建静态网站)
    └─ git push (推送到 GitHub)
         ↓
    Vercel 自动部署
```

## 日志文件说明

| 文件 | 说明 |
|------|------|
| `logs/cron.log` | Cron 定时任务总日志 |
| `logs/generator_YYYYMMDD.log` | 内容生成日志 |
| `logs/deploy_YYYYMMDD_HHMMSS.log` | 部署任务日志 |

## 故障排查

### 检查 Cron 是否运行
```bash
# 查看 cron 服务状态（Mac 上通常自动运行）
log show --predicate 'process == "cron"' --last 1h
```

### 测试 Git 推送权限
```bash
git push origin main --dry-run
```

### 检查虚拟环境
```bash
source .venv/bin/activate
which python
python --version
```

## 服务器部署 (可选)

如果需要在服务器上运行，使用：

```bash
# 上传项目到服务器
scp -r daily_morning_vibes user@server:/opt/

# SSH 登录服务器
ssh user@server

# 运行安装脚本
cd /opt/daily_morning_vibes
bash install_server.sh

# 设置定时任务
bash setup_cron.sh
```
