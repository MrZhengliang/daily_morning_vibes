import os
import json
import time
import pymysql
import oss2
from openai import OpenAI  # 硅基流动也是用这个库，完全兼容
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from config import Config

# ================= 关键修改区域 =================

# 1. 初始化 SiliconFlow 客户端
client = OpenAI(
    api_key=Config.SILICONFLOW_API_KEY, 
    base_url=Config.SILICONFLOW_BASE_URL
)

# ================= 下面的逻辑几乎不用动 =================

def get_db_connection():
    return Config.get_db_connection()

def upload_to_oss(local_file_path, filename):
    try:
        auth = oss2.Auth(Config.OSS_ACCESS_KEY_ID, Config.OSS_ACCESS_KEY_SECRET)
        bucket = oss2.Bucket(auth, Config.OSS_ENDPOINT, Config.OSS_BUCKET_NAME)
        with open(local_file_path, 'rb') as fileobj:
            bucket.put_object(filename, fileobj)
        return Config.OSS_URL_PREFIX + filename
    except Exception as e:
        print(f"OSS上传失败: {e}")
        return None

def generate_simple_image(text_en, filename):
    # 简单的图片生成逻辑
    img = Image.new('RGB', (1080, 1080), color=(255, 165, 0)) # 橙色背景
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 50) 
    except:
        font = ImageFont.load_default()

    import textwrap
    lines = textwrap.wrap(text_en, width=30)
    
    # 简单的垂直居中计算
    line_height = 70
    total_height = len(lines) * line_height
    y_text = (1080 - total_height) / 2 
    
    for line in lines:
        # 简单的水平居中计算 (粗略估算)
        d.text((100, y_text), line, fill=(255, 255, 255), font=font)
        y_text += line_height

    local_path = f"temp_{filename}"
    img.save(local_path)
    return local_path

def fetch_quotes_from_siliconflow():
    """核心：调用 SiliconFlow 生成 JSON"""
    
    system_prompt = """
    You are a helpful assistant. 
    Strictly output raw JSON only. Do not use Markdown (no ```json).
    """
    
    user_prompt = """
    Please generate 5 unique, inspiring "Morning Quotes".
    Format:
    [
        {
            "text_cn": "Chinese translation (Warm and inspiring)",
            "text_en": "Original English Quote",
            "category": "morning"
        }
    ]
    """
    
    try:
        response = client.chat.completions.create(
            # 硅基流动上的模型ID，通常推荐用 DeepSeek-V3
            model="deepseek-ai/DeepSeek-V3", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            stream=False,
            temperature=1.3 # 稍微调高一点，让文案更有创意
        )
        
        content = response.choices[0].message.content or ""
        clean_text = content.replace('```json', '').replace('```', '').strip()
        print("AI 返回内容:", clean_text)
        
        return json.loads(clean_text)
    except Exception as e:
        print(f"API 调用失败: {e}")
        return []

def main():
    print(f"[{datetime.now()}] 启动 SiliconFlow 生产线...")
    
    quotes = fetch_quotes_from_siliconflow()
    if not quotes:
        print("未获取到内容，请检查 API Key 或余额。")
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    
    count = 0
    for item in quotes:
        local_img_path = None
        try:
            file_suffix = str(int(time.time() * 1000))[-6:]
            filename = f"quote_{file_suffix}_{count}.jpg"
            
            local_img_path = generate_simple_image(item['text_en'], filename)
            oss_url = upload_to_oss(local_img_path, f"daily_quotes/{filename}")
            
            if oss_url:
                sql = """
                INSERT INTO content_library (category, text_cn, text_en, image_oss_url, status)
                VALUES (%s, %s, %s, %s, 1)
                """
                cursor.execute(sql, (item['category'], item['text_cn'], item['text_en'], oss_url))
                conn.commit()
                count += 1
                print(f"成功入库: {item['text_en'][:20]}...")
            
        except Exception as e:
            print(f"单条处理失败: {e}")
            conn.rollback()
        finally:
            if local_img_path and os.path.exists(local_img_path):
                os.remove(local_img_path)

    cursor.close()
    conn.close()
    print(f"任务结束，新增 {count} 条资产。")

if __name__ == "__main__":
    main()