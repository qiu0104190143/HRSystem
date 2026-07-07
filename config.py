"""应用配置文件"""
import os

# 项目根目录
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# 数据库配置
DATABASE_PATH = os.path.join(BASE_DIR, 'database', 'hr.db')

# 上传文件配置
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads', 'resumes')
ALLOWED_EXTENSIONS = {'txt', 'docx', 'pdf'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 最大上传 16MB

# Flask配置
SECRET_KEY = 'hr-system-secret-key-2026'
DEBUG = True
HOST = '0.0.0.0'
PORT = 8080
