"""
Daily Morning Vibes Content Generator
使用 ZhipuAI GLM-4.7 生成早安语录

重要提醒：
- 详情页只显示英文内容（text_en）
- 中文翻译（text_cn）仍然保存在数据库中，但不显示在前端
- 保持内容的国际化和简洁性
"""
import os
import json
import time
import pymysql
import random
import textwrap
import shutil
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from datetime import datetime
from config import Config
from zhipuai import ZhipuAI

# ZhipuAI API Key
ZHIPUAI_API_KEY = "9169ae8a03ae409c8739f6c5e08bb828.JgwMF5y5nDrpaaay"

# Initialize ZhipuAI client
client = ZhipuAI(api_key=ZHIPUAI_API_KEY)

def get_db_connection():
    return Config.get_db_connection()

def generate_simple_image(text_en, filename):
    """
    高端版：随机选取一张风景图 -> 加半透明遮罩 -> 写上高大上的英文
    """
    # 1. 随机选一张底图
    bg_dir = os.path.join("assets", "backgrounds")

    # 确保底图目录存在，如果不存在则创建
    if not os.path.exists(bg_dir):
        os.makedirs(bg_dir)

    # 如果没有底图，就用橙色纯色兜底
    if not os.listdir(bg_dir):
        print(f"警告: {bg_dir} 为空，使用纯色背景。请放入 .jpg 图片！")
        img = Image.new('RGB', (1080, 1080), color=(255, 165, 0))
    else:
        # 过滤出图片文件
        valid_images = [x for x in os.listdir(bg_dir) if x.lower().endswith(('.jpg', '.png', '.jpeg'))]
        if not valid_images:
            img = Image.new('RGB', (1080, 1080), color=(255, 165, 0))
        else:
            bg_file = random.choice(valid_images)
            img = Image.open(os.path.join(bg_dir, bg_file)).convert('RGB')
            # 强制裁剪/缩放为 1080x1080
            img = img.resize((1080, 1080))

    # 2. 加一层黑色半透明遮罩 (让白色文字更清晰)
    # 最后一个参数 80 是透明度 (0全透 - 255全黑)，可根据喜好调整
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 80))
    img.paste(Image.alpha_composite(img.convert('RGBA'), overlay), (0, 0), overlay)
    img = img.convert('RGB')

    d = ImageDraw.Draw(img)

    # 3. 加载字体
    font_size = 60
    font = None
    # 尝试加载项目根目录下的字体文件，或者系统字体
    font_paths = [
        "PlayfairDisplay.ttf",  # 推荐：把你下载的好看字体放在根目录
        "Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf", # Mac路径
        "/Library/Fonts/Arial.ttf" # Mac路径
    ]

    for path in font_paths:
        if os.path.exists(path):
            try:
                font = ImageFont.truetype(path, font_size)
                break
            except:
                continue

    if font is None:
        font = ImageFont.load_default()
        # 如果是默认字体，强制处理编码防止报错
        text_en = text_en.encode('latin-1', 'replace').decode('latin-1')

    # 4. 文字自动换行与居中
    # 根据字数动态调整每行字符数，字越多每行越宽
    wrap_width = 25
    lines = textwrap.wrap(text_en, width=wrap_width)

    # 计算总高度
    line_height = font_size * 1.5
    total_text_height = len(lines) * line_height
    y_text = (1080 - total_text_height) / 2 # 垂直居中

    for line in lines:
        # 绘制文字阴影/描边 (黑色) 让文字更凸显
        d.text((102, y_text+2), line, fill=(0, 0, 0), font=font)
        # 绘制文字主体 (白色)
        # 注意：Pillow 旧版本可能不支持 stroke_width，如果报错删掉 stroke 参数
        d.text((100, y_text), line, fill=(255, 255, 255), font=font)
        y_text += line_height

    # 5. 加上域名水印
    try:
        watermark_font = ImageFont.truetype(font_paths[0], 40) if font else ImageFont.load_default()
    except:
        watermark_font = ImageFont.load_default()

    d.text((350, 950), "DailyMorningVibes.com", fill=(200, 200, 200), font=watermark_font)

    # 保存到临时路径
    local_path = f"temp_{filename}"
    img.save(local_path)
    return local_path

def fetch_quotes_from_zhipuai():
    """核心：调用 ZhipuAI GLM-4.7 生成 JSON - 生成不同分类的内容"""
    system_prompt = """
    You are a creative content curator specializing in inspirational quotes across different themes.
    Strictly output raw JSON only. Do not use Markdown (no ```json).
    """

    user_prompt = """
    Generate 5 UNIQUE quotes, each from a DIFFERENT category. CRITICAL REQUIREMENTS:

    **Categories (one quote per category):**
    1. "morning" - About sunrise, new beginnings, fresh starts
    2. "motivation" - About strength, perseverance, achieving goals
    3. "gratitude" - About thankfulness, appreciation, counting blessings
    4. "mindfulness" - About being present, meditation, inner peace
    5. "positivity" - About optimism, positive thinking, spreading joy

    **For each category:**
    - Match the quote's theme to the category
    - Keep quotes concise (under 25 words)
    - Use vivid imagery and metaphors
    - Make them thought-provoking and unique
    - Avoid cliché phrases
    - Draw from diverse sources: literature, philosophy, poetry, wisdom traditions

    **DIVERSITY RULES:**
    - Each quote MUST be from a different category
    - NO similar sentence structures between quotes
    - Each quote must be distinctly different in theme and expression

    Format (JSON only):
    [
        {
            "text_cn": "Chinese translation - warm and poetic",
            "text_en": "Original English quote - unique and creative",
            "category": "one of: morning, motivation, gratitude, mindfulness, positivity"
        }
    ]

    IMPORTANT: Generate exactly 5 quotes, one from each of the 5 categories listed above.
    """

    try:
        response = client.chat.completions.create(
            model="glm-4.7",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            thinking={
                "type": "enabled",  # 启用深度思考模式
            },
            max_tokens=65536,
            temperature=1.0,
            stream=False
        )

        # 获取完整回复
        content = response.choices[0].message.content
        # 清理可能的 markdown 标记
        clean_text = content.replace('```json', '').replace('```', '').strip()
        print("ZhipuAI 返回内容:", clean_text)
        return json.loads(clean_text)
    except Exception as e:
        print(f"ZhipuAI API 调用失败: {e}")
        return []

def main():
    print(f"[{datetime.now()}] 启动 ZhipuAI GLM-4.7 生产线...")

    quotes = fetch_quotes_from_zhipuai()
    if not quotes:
        print("未获取到内容，请检查 ZhipuAI API Key。")
        return

    conn = get_db_connection()
    conn.set_charset('utf8mb4')
    cursor = conn.cursor()
    cursor.execute("SET NAMES utf8mb4")

    count = 0

    # === 关键修改：定义本地静态资源目录 ===
    static_img_dir = os.path.join("static", "images")
    if not os.path.exists(static_img_dir):
        os.makedirs(static_img_dir)
        print(f"创建目录: {static_img_dir}")

    for item in quotes:
        temp_img_path = None
        try:
            file_suffix = str(int(time.time() * 1000))[-6:]
            filename = f"zhipu_{file_suffix}_{count}.jpg"

            print(f"正在处理第 {count+1} 条...")

            # 1. 生成图片 (临时文件)
            temp_img_path = generate_simple_image(item['text_en'], filename)

            # 2. 移动图片到 static/images 文件夹
            target_path = os.path.join(static_img_dir, filename)
            shutil.move(temp_img_path, target_path)

            # 3. 生成存入数据库的 URL (相对路径)
            # 这样 HTML 里的 <img src="/static/images/xxx.jpg"> 就能找到它
            db_image_url = f"/static/images/{filename}"

            # 4. 入库
            # 注意：仍然存入 image_oss_url 字段，但内容是本地路径
            sql = """
            INSERT INTO content_library (category, text_cn, text_en, image_oss_url, status)
            VALUES (%s, %s, %s, %s, 1)
            """
            cursor.execute(sql, (item['category'], item['text_cn'], item['text_en'], db_image_url))
            conn.commit()
            count += 1
            print(f"成功保存: {db_image_url}")

        except Exception as e:
            print(f"单条处理失败: {e}")
            conn.rollback()
            # 如果出错且临时文件还存在，清理掉
            if temp_img_path and os.path.exists(temp_img_path):
                os.remove(temp_img_path)

    cursor.close()
    conn.close()
    print(f"任务结束，新增 {count} 条本地内容。请执行 'python3 build.py' 并 git push。")

if __name__ == "__main__":
    main()
