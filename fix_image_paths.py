"""
修复数据库中的图片路径，将所有 OSS 和外部链接替换为本地 static 路径
"""
import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    return pymysql.connect(
        host=os.getenv('MYSQL_HOST'),
        user=os.getenv('MYSQL_USER'),
        password=os.getenv('MYSQL_PASSWORD'),
        db=os.getenv('MYSQL_DB'),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def get_available_static_images():
    """获取 static/images 目录中可用的图片文件"""
    static_dir = os.path.join('static', 'images')
    if not os.path.exists(static_dir):
        return []

    images = [f for f in os.listdir(static_dir) if f.endswith(('.jpg', '.png', '.jpeg'))]
    return sorted(images)

def fix_database_paths():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 获取所有需要更新的记录
    cursor.execute("""
        SELECT id, image_oss_url
        FROM content_library
        WHERE image_oss_url NOT LIKE '/static/%'
        ORDER BY id ASC
    """)
    records = cursor.fetchall()

    print(f"找到 {len(records)} 条需要更新的记录")

    if not records:
        print("没有需要更新的记录")
        conn.close()
        return

    # 获取可用的本地图片
    available_images = get_available_static_images()
    print(f"本地可用图片数量: {len(available_images)}")

    if not available_images:
        print("错误：static/images 目录中没有图片文件")
        conn.close()
        return

    # 更新每条记录
    updated_count = 0
    for i, record in enumerate(records):
        # 循环使用本地图片
        image_index = i % len(available_images)
        image_file = available_images[image_index]
        new_path = f"/static/images/{image_file}"

        cursor.execute(
            "UPDATE content_library SET image_oss_url = %s WHERE id = %s",
            (new_path, record['id'])
        )
        updated_count += 1

        if updated_count % 10 == 0:
            print(f"已更新 {updated_count} 条记录...")

    conn.commit()
    print(f"\n✅ 成功更新 {updated_count} 条记录")

    # 验证更新结果
    cursor.execute("SELECT COUNT(*) as count FROM content_library WHERE image_oss_url LIKE '/static/%'")
    static_count = cursor.fetchone()['count']
    print(f"现在共有 {static_count} 条记录使用 static 路径")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    print("开始修复数据库图片路径...\n")
    fix_database_paths()
    print("\n修复完成！")
