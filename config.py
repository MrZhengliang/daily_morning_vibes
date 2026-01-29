import os
from dotenv import load_dotenv
import pymysql
import pymysql.cursors

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
        'charset': 'utf8mb4',
        'use_unicode': True,
        'cursorclass': pymysql.cursors.DictCursor
    }

    # Google AI Configuration
    GOOGLE_AI_API_KEY = os.getenv('GOOGLE_AI_API_KEY', '')

    # SiliconFlow Configuration
    SILICONFLOW_API_KEY = os.getenv('SILICONFLOW_API_KEY', '')
    SILICONFLOW_BASE_URL = os.getenv('SILICONFLOW_BASE_URL', 'https://api.siliconflow.cn/v1')

    # OSS Configuration
    OSS_ACCESS_KEY_ID = os.getenv('OSS_ACCESS_KEY_ID', '')
    OSS_ACCESS_KEY_SECRET = os.getenv('OSS_ACCESS_KEY_SECRET', '')
    OSS_BUCKET_NAME = os.getenv('OSS_BUCKET_NAME', '')
    OSS_ENDPOINT = os.getenv('OSS_ENDPOINT', 'oss-cn-hangzhou.aliyuncs.com')
    _endpoint_clean = OSS_ENDPOINT.replace('https://', '').replace('http://', '').rstrip('/')
    OSS_URL_PREFIX = os.getenv('OSS_URL_PREFIX', f"https://{OSS_BUCKET_NAME}.{_endpoint_clean}/")

    # STS 配置
    OSS_ROLE_ARN = os.getenv('OSS_ROLE_ARN', 'acs:ram::1236776035847340:role/oss-arn')
    OSS_STS_ENDPOINT = os.getenv('OSS_STS_ENDPOINT', 'sts.aliyuncs.com')

    @staticmethod
    def get_db_connection():
        return pymysql.connect(**Config.DB_CONFIG)
