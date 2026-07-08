"""HR招聘管理系统 — 主程序入口"""
import os
import sys
import io
from flask import Flask, render_template, session

# 解决Windows控制台中文乱码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 确保项目根目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import DATABASE_PATH, UPLOAD_FOLDER, SECRET_KEY, DEBUG, HOST, PORT
from modules.models import init_db, create_default_admin, get_user_by_id, get_resume_count, get_job_count, get_active_job_count, get_week_resume_count, get_recent_resumes, get_recent_jobs
from modules.routes.resume_routes import resume_bp
from modules.routes.job_routes import job_bp
from modules.routes.search_routes import search_bp
from modules.stats import stats_bp
from modules.auth import auth_bp, login_required
from modules.routes.settings_routes import settings_bp
from utils.helpers import get_local_ip


def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

    # 确保必要的目录存在
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

    # 初始化数据库
    init_db()
    create_default_admin()

    # 注册蓝图
    app.register_blueprint(auth_bp)
    app.register_blueprint(resume_bp)
    app.register_blueprint(job_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(stats_bp)
    app.register_blueprint(settings_bp)

    # 全局上下文：所有模板可用的变量
    @app.context_processor
    def inject_globals():
        user = None
        if 'user_id' in session:
            user = get_user_by_id(session['user_id'])
        return {
            'local_ip': get_local_ip(),
            'port': PORT,
            'current_user': user,
        }

    # 首页路由
    @app.route('/')
    @login_required
    def index():
        stats = {
            'resume_count': get_resume_count(),
            'job_count': get_job_count(),
            'active_job_count': get_active_job_count(),
            'week_resume_count': get_week_resume_count(),
        }
        recent_resumes = get_recent_resumes(5)
        recent_jobs = get_recent_jobs(5)
        local_ip = get_local_ip()
        return render_template('index.html',
                               stats=stats,
                               recent_resumes=recent_resumes,
                               recent_jobs=recent_jobs,
                               local_ip=local_ip,
                               port=PORT)

    return app


if __name__ == '__main__':
    app = create_app()
    local_ip = get_local_ip()
    print('=' * 60)
    print('  [HR] HR招聘管理系统 已启动！')
    print('=' * 60)
    print(f'  本机访问: http://localhost:{PORT}')
    print(f'  局域网访问: http://{local_ip}:{PORT}')
    print('  按 Ctrl+C 停止服务')
    print('=' * 60)
    app.run(host=HOST, port=PORT, debug=DEBUG)
