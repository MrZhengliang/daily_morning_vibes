import os
from flask import Flask, render_template, abort, request
import pymysql
import pymysql.cursors
from dotenv import load_dotenv

# 加载 .env 变量
load_dotenv()

# === 关键点：这里定义了 app 变量 ===
app = Flask(__name__)

# 从环境变量读取配置
DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST'),
    'user': os.getenv('MYSQL_USER'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'db': os.getenv('MYSQL_DB'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

# === 关键点：这里定义了 get_db_connection 函数 ===
def get_db_connection():
    return pymysql.connect(**DB_CONFIG)

@app.route('/')
def index():
    """首页：展示最新的 20 条语录，支持分页"""
    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 获取总数
            cursor.execute("SELECT COUNT(*) as total FROM content_library WHERE status=1")
            total = cursor.fetchone()['total']

            # 获取当前页数据
            sql = "SELECT * FROM content_library WHERE status=1 ORDER BY id DESC LIMIT %s OFFSET %s"
            cursor.execute(sql, (per_page, offset))
            quotes = cursor.fetchall()

            # 计算总页数
            total_pages = (total + per_page - 1) // per_page
        conn.close()
    except Exception as e:
        print(f"数据库连接失败: {e}")
        quotes = []
        total_pages = 1

    return render_template('index.html',
                          quotes=quotes,
                          current_page=page,
                          total_pages=total_pages)

@app.route('/quote/<int:quote_id>')
def detail(quote_id):
    """详情页"""
    conn = get_db_connection()
    with conn.cursor() as cursor:
        sql = "SELECT * FROM content_library WHERE id=%s AND status=1"
        cursor.execute(sql, (quote_id,))
        quote = cursor.fetchone()
    conn.close()

    if quote is None:
        abort(404)

    return render_template('detail.html', quote=quote)

@app.route('/category/<category_name>')
def category(category_name):
    """分类页：按分类展示语录，支持分页"""
    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 获取总数
            cursor.execute("SELECT COUNT(*) as total FROM content_library WHERE category=%s AND status=1", (category_name,))
            total = cursor.fetchone()['total']

            # 获取当前页数据
            sql = "SELECT * FROM content_library WHERE category=%s AND status=1 ORDER BY id DESC LIMIT %s OFFSET %s"
            cursor.execute(sql, (category_name, per_page, offset))
            quotes = cursor.fetchall()

            # 计算总页数
            total_pages = (total + per_page - 1) // per_page
        conn.close()
    except Exception as e:
        print(f"数据库连接失败: {e}")
        quotes = []
        total_pages = 1

    return render_template('index.html',
                          quotes=quotes,
                          current_category=category_name,
                          current_page=page,
                          total_pages=total_pages)

# 为了防止 build 报错，我们可以给个假的 sitemap 路由或者加上逻辑
@app.route('/sitemap.xml')
def sitemap():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        sql = "SELECT id FROM content_library WHERE status=1 ORDER BY id DESC LIMIT 1000"
        cursor.execute(sql)
        ids = cursor.fetchall()
    conn.close()
    
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for item in ids:
        xml += f'  <url><loc>https://dailymorningvibes.com/quote/{item["id"]}</loc></url>\n'
    xml += '</urlset>'
    return xml, {'Content-Type': 'application/xml'}

# 静态页面的路由（Vercel 需要）
@app.route('/privacy.html')
def privacy():
    return render_template('privacy.html')

@app.route('/terms.html')
def terms():
    return render_template('terms.html')

@app.route('/about.html')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True)