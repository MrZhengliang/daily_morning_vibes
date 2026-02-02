import os
import json
from flask_frozen import Freezer
from app import app, get_db_connection  # 导入你原来的 Flask app

# 配置静态文件生成路径
# 生成到 build 文件夹，并且生成漂亮的 URL (例如 /quote/1 而不是 /quote/1.html)
app.config['FREEZER_DESTINATION'] = 'build'
app.config['FREEZER_RELATIVE_URLS'] = False  # 改为 False，使用绝对路径，避免链接问题

freezer = Freezer(app)

# 告诉 Freezer 还有哪些动态路由需要生成 (比如 /quote/1, /quote/2...)
@freezer.register_generator
def detail():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        # 获取所有已发布的文章 ID
        sql = "SELECT id FROM content_library WHERE status=1"
        cursor.execute(sql)
        ids = cursor.fetchall()
    conn.close()
    
    for item in ids:
        yield {'quote_id': item['id']}

if __name__ == '__main__':
    print("开始生成静态网站...")
    freezer.freeze()

    # === 新增：给详情页添加 .html 扩展名 ===
    quote_dir = os.path.join('build', 'quote')
    if os.path.exists(quote_dir):
        print("正在给详情页添加 .html 扩展名...")
        for filename in os.listdir(quote_dir):
            file_path = os.path.join(quote_dir, filename)
            # 跳过已有 .html 扩展名的文件和目录
            if os.path.isfile(file_path) and not filename.endswith('.html'):
                new_path = os.path.join(quote_dir, f"{filename}.html")
                os.rename(file_path, new_path)
        print("✅ 详情页扩展名已添加！")

    # === 新增：自动生成 Vercel 配置文件 ===
    # 这告诉 Vercel：开启 Clean URLs (去掉 .html 后缀也能访问)
    vercel_config = {
        "cleanUrls": True,
        "trailingSlash": False
    }

    # 把配置文件写入 build 文件夹
    with open('build/vercel.json', 'w') as f:
        json.dump(vercel_config, f)

    print("✅ vercel.json 配置已生成！")

    # ... (原来的 CNAME 代码保持不变) ...
    with open('build/CNAME', 'w') as f:
        f.write('dailymorningvibes.com')

    print("静态网站生成完毕！文件在 /build 目录下。")