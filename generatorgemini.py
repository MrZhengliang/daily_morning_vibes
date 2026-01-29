import os
import json
import time
import pymysql
import oss2
import random
import textwrap
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from datetime import datetime
from config import Config
from aliyunsdkcore import client as aliyun_client
from aliyunsdksts.request.v20150401 import AssumeRoleRequest

# 1. Google Gemini API 配置
def get_gemini_url():
    key = Config.GOOGLE_AI_API_KEY
    return f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}"

def get_db_connection():
    return Config.get_db_connection()

def get_sts_token():
    try:
        # OSS 访问强制禁用代理
        os.environ['NO_PROXY'] = '*'
        endpoint = Config.OSS_ENDPOINT.replace('https://', '').replace('http://', '')
        region = endpoint.split('.')[0]
        if region.startswith('oss-'):
            region = region[4:]
        else:
            region = 'cn-hangzhou'

        clt = aliyun_client.AcsClient(Config.OSS_ACCESS_KEY_ID, Config.OSS_ACCESS_KEY_SECRET, region)
        request = AssumeRoleRequest.AssumeRoleRequest()
        request.set_RoleArn(Config.OSS_ROLE_ARN)
        request.set_RoleSessionName('oss-session')
        request.set_DurationSeconds(3600)
        
        response = clt.do_action_with_exception(request)
        if response is None:
            return None
        
        data = json.loads(str(response, encoding='utf-8') if isinstance(response, bytes) else response)
        return {
            'access_key_id': data['Credentials']['AccessKeyId'],
            'access_key_secret': data['Credentials']['AccessKeySecret'],
            'security_token': data['Credentials']['SecurityToken']
        }
    except Exception as e:
        print(f"获取STS Token失败: {e}")
        return None

def upload_to_oss(local_file_path, filename):
    try:
        # OSS 访问强制禁用代理
        os.environ['NO_PROXY'] = '*'
        print(f"正在上传 {filename} 到 OSS (使用 STS)...")
        
        sts = get_sts_token()
        if not sts:
            auth = oss2.Auth(Config.OSS_ACCESS_KEY_ID, Config.OSS_ACCESS_KEY_SECRET)
        else:
            auth = oss2.StsAuth(sts['access_key_id'], sts['access_key_secret'], sts['security_token'])
            
        endpoint = Config.OSS_ENDPOINT
        if not endpoint.startswith('http'):
            endpoint = 'http://' + endpoint
            
        bucket = oss2.Bucket(auth, endpoint, Config.OSS_BUCKET_NAME)
        with open(local_file_path, 'rb') as fileobj:
            bucket.put_object(filename, fileobj)
        return Config.OSS_URL_PREFIX + filename
    except Exception as e:
        print(f"OSS上传失败: {e}")
        status = getattr(e, 'status', 'N/A')
        if status != 'N/A':
            print(f"错误状态码: {status}")
        return None

def generate_simple_image(text_en, filename):
    bg_dir = "assets/backgrounds"
    if not os.path.exists(bg_dir) or not os.listdir(bg_dir):
        img = Image.new('RGB', (1080, 1080), color=(255, 165, 0))
    else:
        bg_files = [x for x in os.listdir(bg_dir) if x.endswith(('.jpg', '.png'))]
        if not bg_files:
            img = Image.new('RGB', (1080, 1080), color=(255, 165, 0))
        else:
            bg_file = random.choice(bg_files)
            img = Image.open(os.path.join(bg_dir, bg_file)).convert('RGB')
            img = img.resize((1080, 1080))

    overlay = Image.new('RGBA', img.size, (0, 0, 0, 100))
    img.paste(Image.alpha_composite(img.convert('RGBA'), overlay), (0,0), overlay)
    img = img.convert('RGB')
    d = ImageDraw.Draw(img)
    
    font_size = 60
    font = None
    font_paths = [
        "PlayfairDisplay.ttf", 
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Cache/Arial.ttf",
        "/Library/Fonts/Arial.ttf"
    ]
    
    for path in font_paths:
        try:
            if os.path.exists(path) or path == "PlayfairDisplay.ttf":
                font = ImageFont.truetype(path, font_size)
                break
        except:
            continue
            
    if font is None:
        font = ImageFont.load_default()
        text_en = text_en.encode('latin-1', 'replace').decode('latin-1')

    wrap_width = 25 
    lines = textwrap.wrap(text_en, width=wrap_width)
    line_height = font_size * 1.5
    total_text_height = len(lines) * line_height
    y_text = (1080 - total_text_height) / 2
    
    for line in lines:
        d.text((100, y_text), line, fill=(255, 255, 255), font=font, stroke_width=2, stroke_fill='black')
        y_text += line_height

    d.text((350, 950), "DailyMorningVibes.com", fill=(200, 200, 200), font=font)
    local_path = f"temp_gemini_{filename}"
    img.save(local_path)
    return local_path

def fetch_quotes_from_gemini():
    """核心：调用 Google Gemini (gemini-2.0-flash) 生成 JSON"""
    prompt = """
    Please generate 5 unique, inspiring "Morning Quotes".
    Format: Strictly output raw JSON only. Do not use Markdown (no ```json).
    [
        {
            "text_cn": "Chinese translation (Warm and inspiring)",
            "text_en": "Original English Quote",
            "category": "morning"
        }
    ]
    """
    
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 1.0,
            "maxOutputTokens": 2048,
        }
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    response = None
    try:
        url = get_gemini_url()
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # 提取生成的内容
        content = data['candidates'][0]['content']['parts'][0]['text']
        clean_text = content.replace('```json', '').replace('```', '').strip()
        print("Gemini 返回内容:", clean_text)
        return json.loads(clean_text)
    except Exception as e:
        print(f"Gemini API 调用失败: {e}")
        if response is not None:
            print(f"错误详情: {response.text}")
        return []

def main():
    print(f"[{datetime.now()}] 启动 Google Gemini 生产线...")
    quotes = fetch_quotes_from_gemini()
    if not quotes:
        print("未获取到内容，请检查 Gemini API Key。")
        return

    conn = get_db_connection()
    conn.set_charset('utf8mb4')
    cursor = conn.cursor()
    cursor.execute("SET NAMES utf8mb4")
    
    count = 0
    for item in quotes:
        local_img_path = None
        try:
            file_suffix = str(int(time.time() * 1000))[-6:]
            filename = f"gemini_{file_suffix}_{count}.jpg"
            print(f"正在处理第 {count+1} 条: {item['text_en'][:30]}...")
            local_img_path = generate_simple_image(item['text_en'], filename)
            oss_url = upload_to_oss(local_img_path, f"daily_quotes/{filename}")
            
            if oss_url:
                sql = "INSERT INTO content_library (category, text_cn, text_en, image_oss_url, status) VALUES (%s, %s, %s, %s, 1)"
                cursor.execute(sql, (item['category'], item['text_cn'], item['text_en'], oss_url))
                conn.commit()
                count += 1
                print(f"成功入库: {item['text_en'][:20]}...")
            else:
                print(f"跳过入库，因为 OSS 上传失败")
        except Exception as e:
            print(f"单条处理失败: {e}")
            conn.rollback()
        finally:
            if local_img_path and os.path.exists(local_img_path):
                os.remove(local_img_path)

    cursor.close()
    conn.close()
    print(f"任务结束，Gemini 新增 {count} 条资产。")

if __name__ == "__main__":
    main()
