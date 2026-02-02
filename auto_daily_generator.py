#!/usr/bin/env python3
"""
自动每日内容生成脚本 - 每个分类生成3条内容
5个分类 x 3条 = 15条内容/天
"""
import os
import sys
import json
import time
import logging
import pymysql
import random
import textwrap
import shutil
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from config import Config
from zhipuai import ZhipuAI

# ==================== 配置区域 ====================
# ZhipuAI API Key
ZHIPUAI_API_KEY = "9169ae8a03ae409c8739f6c5e08bb828.JgwMF5y5nDrpaaay"

# 分类配置 - 每个分类生成3条
CATEGORIES = [
    "morning",
    "motivation",
    "gratitude",
    "mindfulness",
    "positivity"
]
QUOTES_PER_CATEGORY = 3  # 每个分类生成3条

# 日志配置 - 优先使用项目目录，如果是服务器环境则使用 /var/log
try:
    LOG_DIR = "/var/log/daily_vibes"
    os.makedirs(LOG_DIR, exist_ok=True)
except PermissionError:
    LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'{LOG_DIR}/generator_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)
logger.info(f"日志目录: {LOG_DIR}")

# ==================== 初始化 ====================
client = ZhipuAI(api_key=ZHIPUAI_API_KEY)


def get_db_connection():
    """获取数据库连接"""
    try:
        return Config.get_db_connection()
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        raise


def generate_simple_image(text_en, filename):
    """生成语录图片"""
    bg_dir = os.path.join("assets", "backgrounds")

    # 确保底图目录存在
    if not os.path.exists(bg_dir):
        os.makedirs(bg_dir)
        logger.warning(f"创建底图目录: {bg_dir}")

    # 选择背景图
    if not os.path.exists(bg_dir) or not os.listdir(bg_dir):
        logger.warning(f"底图目录为空，使用纯色背景")
        img = Image.new('RGB', (1080, 1080), color=(255, 165, 0))
    else:
        valid_images = [x for x in os.listdir(bg_dir) if x.lower().endswith(('.jpg', '.png', '.jpeg'))]
        if not valid_images:
            img = Image.new('RGB', (1080, 1080), color=(255, 165, 0))
        else:
            bg_file = random.choice(valid_images)
            img = Image.open(os.path.join(bg_dir, bg_file)).convert('RGB')
            img = img.resize((1080, 1080))

    # 添加半透明遮罩
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 80))
    img.paste(Image.alpha_composite(img.convert('RGBA'), overlay), (0, 0), overlay)
    img = img.convert('RGB')

    d = ImageDraw.Draw(img)

    # 加载字体
    font_size = 60
    font = None
    font_paths = [
        "PlayfairDisplay.ttf",
        "Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",  # Linux
    ]

    for path in font_paths:
        if os.path.exists(path):
            try:
                font = ImageFont.truetype(path, font_size)
                logger.debug(f"使用字体: {path}")
                break
            except Exception as e:
                logger.debug(f"字体加载失败 {path}: {e}")
                continue

    if font is None:
        font = ImageFont.load_default()
        logger.warning("使用默认字体")

    # 文字自动换行与居中
    wrap_width = 25
    lines = textwrap.wrap(text_en, width=wrap_width)

    line_height = font_size * 1.5
    total_text_height = len(lines) * line_height
    y_text = (1080 - total_text_height) / 2

    for line in lines:
        # 绘制阴影
        d.text((102, y_text+2), line, fill=(0, 0, 0), font=font)
        # 绘制主体
        d.text((100, y_text), line, fill=(255, 255, 255), font=font)
        y_text += line_height

    # 添加水印
    try:
        watermark_font = ImageFont.truetype(font_paths[0], 40) if font else ImageFont.load_default()
    except:
        watermark_font = ImageFont.load_default()

    d.text((350, 950), "DailyMorningVibes.com", fill=(200, 200, 200), font=watermark_font)

    # 保存临时文件
    local_path = f"temp_{filename}"
    img.save(local_path)
    return local_path


def fetch_quotes_from_zhipuai():
    """调用 ZhipuAI 生成每个分类3条内容"""
    total_quotes = len(CATEGORIES) * QUOTES_PER_CATEGORY

    system_prompt = """
    You are a creative content curator specializing in inspirational quotes across different themes.
    Strictly output raw JSON only. Do not use Markdown (no ```json).
    """

    user_prompt = f"""
    Generate {total_quotes} UNIQUE quotes across {len(CATEGORIES)} categories.

    **Categories:**
    {', '.join(CATEGORIES)}

    **Requirements:**
    - Generate exactly {QUOTES_PER_CATEGORY} quotes for EACH category
    - Each quote must be UNIQUE and distinctly different
    - Keep quotes concise (under 25 words)
    - Use vivid imagery and metaphors
    - Avoid cliché phrases
    - Draw from diverse sources: literature, philosophy, poetry, wisdom traditions

    **Category Themes:**
    - morning: sunrise, new beginnings, fresh starts, dawn
    - motivation: strength, perseverance, achieving goals, success
    - gratitude: thankfulness, appreciation, counting blessings
    - mindfulness: being present, meditation, inner peace, awareness
    - positivity: optimism, positive thinking, spreading joy

    Format (JSON only):
    [
        {{
            "text_cn": "Chinese translation - warm and poetic",
            "text_en": "Original English quote - unique and creative",
            "category": "one of: {', '.join(CATEGORIES)}"
        }}
    ]

    IMPORTANT: Generate exactly {total_quotes} quotes, {QUOTES_PER_CATEGORY} for each of the {len(CATEGORIES)} categories.
    """

    max_retries = 3
    for attempt in range(max_retries):
        try:
            logger.info(f"调用 ZhipuAI API (尝试 {attempt + 1}/{max_retries})...")
            response = client.chat.completions.create(
                model="glm-4.7",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                thinking={"type": "enabled"},
                max_tokens=65536,
                temperature=1.0,
                stream=False
            )

            content = response.choices[0].message.content
            clean_text = content.replace('```json', '').replace('```', '').strip()
            quotes = json.loads(clean_text)

            # 验证数量
            if len(quotes) < total_quotes:
                logger.warning(f"获取 {len(quotes)} 条，期望 {total_quotes} 条")

            logger.info(f"成功获取 {len(quotes)} 条语录")
            return quotes

        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败 (尝试 {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
                continue
            else:
                raise
        except Exception as e:
            logger.error(f"API调用失败 (尝试 {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(10)
                continue
            else:
                raise

    return []


def main():
    """主函数"""
    start_time = datetime.now()
    logger.info("=" * 60)
    logger.info(f"开始每日内容生成任务 - {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"目标: {len(CATEGORIES)} 个分类 x {QUOTES_PER_CATEGORY} 条 = {len(CATEGORIES) * QUOTES_PER_CATEGORY} 条内容")

    try:
        # 1. 获取语录
        quotes = fetch_quotes_from_zhipuai()
        if not quotes:
            logger.error("未获取到内容，任务终止")
            return False

        # 2. 数据库连接
        conn = get_db_connection()
        conn.set_charset('utf8mb4')
        cursor = conn.cursor()
        cursor.execute("SET NAMES utf8mb4")

        # 3. 准备静态资源目录
        static_img_dir = os.path.join("static", "images")
        if not os.path.exists(static_img_dir):
            os.makedirs(static_img_dir)
            logger.info(f"创建目录: {static_img_dir}")

        # 4. 统计每个分类的数量
        category_count = {cat: 0 for cat in CATEGORIES}
        success_count = 0
        failed_count = 0

        # 5. 处理每条语录
        for idx, item in enumerate(quotes):
            temp_img_path = None
            try:
                category = item.get('category', '').lower()
                if category not in CATEGORIES:
                    logger.warning(f"未知分类: {category}, 跳过")
                    continue

                file_suffix = str(int(time.time() * 1000))[-6:]
                filename = f"zhipu_{file_suffix}_{idx}.jpg"

                logger.info(f"[{idx+1}/{len(quotes)}] 处理 {category} 分类...")

                # 生成图片
                temp_img_path = generate_simple_image(item['text_en'], filename)

                # 移动到静态目录
                target_path = os.path.join(static_img_dir, filename)
                shutil.move(temp_img_path, target_path)

                # 数据库URL
                db_image_url = f"/static/images/{filename}"

                # 入库
                sql = """
                INSERT INTO content_library (category, text_cn, text_en, image_oss_url, status)
                VALUES (%s, %s, %s, %s, 1)
                """
                cursor.execute(sql, (category, item['text_cn'], item['text_en'], db_image_url))
                conn.commit()

                category_count[category] += 1
                success_count += 1
                logger.info(f"✓ 成功: {category} - {item['text_en'][:30]}...")

            except Exception as e:
                logger.error(f"✗ 失败: {e}")
                failed_count += 1
                conn.rollback()
                if temp_img_path and os.path.exists(temp_img_path):
                    os.remove(temp_img_path)

        cursor.close()
        conn.close()

        # 6. 汇总结果
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info("=" * 60)
        logger.info("任务完成汇总:")
        logger.info(f"  成功: {success_count} 条")
        logger.info(f"  失败: {failed_count} 条")
        logger.info(f"  各分类统计:")
        for cat, count in category_count.items():
            logger.info(f"    - {cat}: {count} 条")
        logger.info(f"  耗时: {duration:.2f} 秒")
        logger.info("=" * 60)

        return success_count > 0

    except Exception as e:
        logger.error(f"任务执行失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
