import os
import json
import time
import pymysql
import oss2
import random
import textwrap
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from datetime import datetime
from config import Config
from aliyunsdkcore import client as aliyun_client
from aliyunsdksts.request.v20150401 import AssumeRoleRequest

# 1. 初始化 SiliconFlow 客户端
client = OpenAI(
    api_key=Config.SILICONFLOW_API_KEY, 
    base_url=Config.SILICONFLOW_BASE_URL
)

def get_db_connection():
    return Config.get_db_connection()

def get_sts_token():
    try:
        # 从 endpoint 中提取 region，例如 oss-cn-hangzhou.aliyuncs.com -> cn-hangzhou
        endpoint = Config.OSS_ENDPOINT.replace('https://', '').replace('http://', '')
        region = endpoint.split('.')[0]
        if region.startswith('oss-'):
            region = region[4:]
        else:
            region = 'cn-hangzhou' # 默认

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
        print(f"正在上传 {filename} 到 OSS (使用 STS)...")
        # 强制不使用代理 (排除网络环境干扰)
        os.environ['HTTP_PROXY'] = ''
        os.environ['HTTPS_PROXY'] = ''
        
        sts = get_sts_token()
        if not sts:
            print("无法获取STS Token，尝试使用普通Auth...")
            auth = oss2.Auth(Config.OSS_ACCESS_KEY_ID, Config.OSS_ACCESS_KEY_SECRET)
        else:
            auth = oss2.StsAuth(sts['access_key_id'], sts['access_key_secret'], sts['security_token'])
            
        # 尝试使用 http 协议绕过可能的 https 代理/证书问题
        endpoint = Config.OSS_ENDPOINT
        if not endpoint.startswith('http'):
            endpoint = 'http://' + endpoint
            
        print(f"使用 Endpoint: {endpoint}")
        bucket = oss2.Bucket(auth, endpoint, Config.OSS_BUCKET_NAME)
        with open(local_file_path, 'rb') as fileobj:
            bucket.put_object(filename, fileobj)
        return Config.OSS_URL_PREFIX + filename
    except Exception as e:
        print(f"OSS上传失败: {e}")
        # 尝试获取状态码，如果存在的话
        status = getattr(e, 'status', 'N/A')
        print(f"错误状态码: {status}")
        return None



def generate_simple_image(text_en, filename):
    """
    高端版：随机选取一张风景图 -> 加半透明遮罩 -> 写上高大上的英文
    """
    # 1. 随机选一张底图
    bg_dir = "assets/backgrounds"
    # 如果没有底图，就还是用橙色兜底
    if not os.path.exists(bg_dir) or not os.listdir(bg_dir):
        img = Image.new('RGB', (1080, 1080), color=(255, 165, 0))
    else:
        bg_file = random.choice([x for x in os.listdir(bg_dir) if x.endswith(('.jpg', '.png'))])
        img = Image.open(os.path.join(bg_dir, bg_file)).convert('RGB')
        # 强制裁剪/缩放为 1080x1080 (居中裁剪)
        target_size = 1080
        width, height = img.size
        # ...这里省略复杂的裁剪逻辑，直接强制缩放简单粗暴，或者你手动裁好...
        img = img.resize((target_size, target_size))

    # 2. 加一层黑色半透明遮罩 (让白色文字更清晰)
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 100)) # 100是透明度(0-255)
    img.paste(Image.alpha_composite(img.convert('RGBA'), overlay), (0,0), overlay)
    img = img.convert('RGB')

    d = ImageDraw.Draw(img)
    
    # 3. 加载字体 (务必传一个好看的英文手写体或衬线体到目录，比如 'PlayfairDisplay.ttf')
    font_size = 60
    try:
        font = ImageFont.truetype("PlayfairDisplay.ttf", font_size)
    except:
        font = ImageFont.load_default()

    # 4. 文字自动换行与居中
    # 根据字数动态调整每行字符数
    wrap_width = 25 
    lines = textwrap.wrap(text_en, width=wrap_width)
    
    # 计算总高度
    line_height = font_size * 1.5
    total_text_height = len(lines) * line_height
    y_text = (1080 - total_text_height) / 2 # 垂直居中
    
    for line in lines:
        # 获取文字宽度 (Pillow 新旧版本方法不同，这里用简单的)
        # 简单居中：假设每个字宽度固定（虽然不准但够用）
        # 更精准的方法是 d.textbbox，这里为了不报错先简化
        d.text((100, y_text), line, fill=(255, 255, 255), font=font, stroke_width=2, stroke_fill='black')
        y_text += line_height

    # 5. 加上你的域名水印 (AdSense 很喜欢这个，显得专业)
    d.text((350, 950), "DailyMorningVibes.com", fill=(200, 200, 200), font=font)

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
    # 确保连接使用 UTF-8
    conn.set_charset('utf8mb4')
    cursor = conn.cursor()
    
    # 强制执行一次 SET NAMES
    cursor.execute("SET NAMES utf8mb4")
    
    count = 0
    for item in quotes:
        local_img_path = None
        try:
            file_suffix = str(int(time.time() * 1000))[-6:]
            filename = f"quote_{file_suffix}_{count}.jpg"
            
            print(f"正在处理第 {count+1} 条: {item['text_en'][:30]}...")
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
            else:
                print(f"跳过入库，因为 OSS 上传失败")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
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