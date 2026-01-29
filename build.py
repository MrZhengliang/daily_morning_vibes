import os
from flask_frozen import Freezer
from app import app, get_db_connection  # 导入你原来的 Flask app

# 配置静态文件生成路径
# 生成到 build 文件夹，并且生成漂亮的 URL (例如 /quote/1 而不是 /quote/1.html)
app.config['FREEZER_DESTINATION'] = 'build'
app.config['FREEZER_RELATIVE_URLS'] = True

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
    print("静态网站生成完毕！文件在 /build 目录下。")
    
    # 特殊处理：Vercel 需要一个 404.html，我们可以复制首页过去或者单独写
    # 这里简单处理，创建一个 CNAME 文件用于绑定域名 (GitHub Pages 需要，Vercel 不需要但留着无妨)
    with open('build/CNAME', 'w') as f:
        f.write('dailymorningvibes.com')