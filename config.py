import os
from dotenv import load_dotenv
import pymysql

load_dotenv()

class Config:
    # MySQL Configuration
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DB = os.getenv('MYSQL_DB', 'test')
    MYSQL_CHARSET = os.getenv('MYSQL_CHARSET', 'utf8mb4')
    
    DB_CONFIG = {
        'host': MYSQL_HOST,
        'user': MYSQL_USER,
        'password': MYSQL_PASSWORD,
        'db': MYSQL_DB,
        'charset': MYSQL_CHARSET,
        'cursorclass': pymysql.cursors.DictCursor
    }

    # Google AI Configuration
    GOOGLE_AI_API_KEY = os.getenv('GOOGLE_AI_API_KEY', '')

    # OSS Configuration
    OSS_ACCESS_KEY_ID = os.getenv('OSS_ACCESS_KEY_ID', '')
    OSS_ACCESS_KEY_SECRET = os.getenv('OSS_ACCESS_KEY_SECRET', '')
    OSS_BUCKET_NAME = os.getenv('OSS_BUCKET_NAME', '')
    OSS_ENDPOINT = os.getenv('OSS_ENDPOINT', 'oss-cn-hangzhou.aliyuncs.com')
    OSS_URL_PREFIX = os.getenv('OSS_URL_PREFIX', f"https://{OSS_BUCKET_NAME}.{OSS_ENDPOINT}/")

    @staticmethod
    def get_db_connection():
        return pymysql.connect(**Config.DB_CONFIG)
