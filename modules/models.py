"""数据库模型与操作"""
import sqlite3
import os
from datetime import datetime
from config import DATABASE_PATH


def get_db():
    """获取数据库连接"""
    # 确保数据库目录存在
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # 使查询结果可以通过列名访问
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """初始化数据库表结构"""
    conn = get_db()
    cursor = conn.cursor()

    # 简历表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT DEFAULT '',
            gender TEXT DEFAULT '',
            age INTEGER DEFAULT 0,
            phone TEXT DEFAULT '',
            email TEXT DEFAULT '',
            education TEXT DEFAULT '',
            school TEXT DEFAULT '',
            major TEXT DEFAULT '',
            skills TEXT DEFAULT '',
            experience_years INTEGER DEFAULT 0,
            current_company TEXT DEFAULT '',
            current_position TEXT DEFAULT '',
            content_text TEXT DEFAULT '',
            file_path TEXT DEFAULT '',
            file_type TEXT DEFAULT '',
            parsed_json TEXT DEFAULT '',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 兼容旧数据库：如果 parsed_json 列不存在则添加
    try:
        cursor.execute('ALTER TABLE resumes ADD COLUMN parsed_json TEXT DEFAULT ""')
    except sqlite3.OperationalError:
        pass  # 列已存在

    # 职位表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            department TEXT DEFAULT '',
            salary_min INTEGER DEFAULT 0,
            salary_max INTEGER DEFAULT 0,
            education_required TEXT DEFAULT '',
            experience_required INTEGER DEFAULT 0,
            age_min INTEGER DEFAULT 0,
            age_max INTEGER DEFAULT 0,
            skills_required TEXT DEFAULT '',
            description TEXT DEFAULT '',
            requirements TEXT DEFAULT '',
            status TEXT DEFAULT '招聘中',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 用户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            display_name TEXT DEFAULT '',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 系统设置表（键值对存储）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT DEFAULT ''
        )
    ''')

    conn.commit()
    conn.close()


# ========== 系统设置操作 ==========

def get_setting(key, default=''):
    """获取单个设置值"""
    conn = get_db()
    row = conn.execute('SELECT value FROM settings WHERE key = ?', (key,)).fetchone()
    conn.close()
    return row['value'] if row else default


def save_setting(key, value):
    """保存设置（存在则更新，不存在则插入）"""
    conn = get_db()
    conn.execute('''
        INSERT INTO settings (key, value) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
    ''', (key, str(value)))
    conn.commit()
    conn.close()


def get_all_settings():
    """获取所有设置"""
    conn = get_db()
    rows = conn.execute('SELECT * FROM settings').fetchall()
    conn.close()
    return {r['key']: r['value'] for r in rows}


def create_default_admin():
    """创建默认管理员账号（如果不存在）"""
    from werkzeug.security import generate_password_hash
    conn = get_db()
    existing = conn.execute(
        'SELECT id FROM users WHERE username = ?', ('admin',)
    ).fetchone()
    if not existing:
        conn.execute(
            'INSERT INTO users (username, password_hash, display_name) VALUES (?, ?, ?)',
            ('admin', generate_password_hash('admin123'), '系统管理员')
        )
        conn.commit()
    conn.close()


def verify_user(username, password):
    """验证用户名密码，成功返回用户信息，失败返回None"""
    from werkzeug.security import check_password_hash
    conn = get_db()
    user = conn.execute(
        'SELECT * FROM users WHERE username = ?', (username,)
    ).fetchone()
    conn.close()
    if user and check_password_hash(user['password_hash'], password):
        return dict(user)
    return None


def get_user_by_id(user_id):
    """根据ID获取用户"""
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return dict(user) if user else None


# ========== 简历 CRUD 操作 ==========

def add_resume(data):
    """添加简历"""
    conn = get_db()
    conn.execute('''
        INSERT INTO resumes (name, gender, age, phone, email, education, school,
            major, skills, experience_years, current_company, current_position,
            content_text, file_path, file_type, parsed_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data.get('name', ''),
        data.get('gender', ''),
        data.get('age', 0),
        data.get('phone', ''),
        data.get('email', ''),
        data.get('education', ''),
        data.get('school', ''),
        data.get('major', ''),
        data.get('skills', ''),
        data.get('experience_years', 0),
        data.get('current_company', ''),
        data.get('current_position', ''),
        data.get('content_text', ''),
        data.get('file_path', ''),
        data.get('file_type', ''),
        data.get('parsed_json', ''),
    ))
    conn.commit()
    resume_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.close()
    return resume_id


def get_all_resumes(page=1, per_page=20):
    """获取简历列表（分页）"""
    conn = get_db()
    offset = (page - 1) * per_page
    total = conn.execute('SELECT COUNT(*) FROM resumes').fetchone()[0]
    resumes = conn.execute(
        'SELECT * FROM resumes ORDER BY created_at DESC LIMIT ? OFFSET ?',
        (per_page, offset)
    ).fetchall()
    conn.close()
    return [dict(r) for r in resumes], total


def get_resume_by_id(resume_id):
    """根据ID获取简历"""
    conn = get_db()
    row = conn.execute('SELECT * FROM resumes WHERE id = ?', (resume_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_resume(resume_id, data):
    """更新简历"""
    conn = get_db()
    conn.execute('''
        UPDATE resumes SET name=?, gender=?, age=?, phone=?, email=?, education=?,
            school=?, major=?, skills=?, experience_years=?, current_company=?,
            current_position=?, content_text=?, parsed_json=?
        WHERE id=?
    ''', (
        data.get('name', ''),
        data.get('gender', ''),
        data.get('age', 0),
        data.get('phone', ''),
        data.get('email', ''),
        data.get('education', ''),
        data.get('school', ''),
        data.get('major', ''),
        data.get('skills', ''),
        data.get('experience_years', 0),
        data.get('current_company', ''),
        data.get('current_position', ''),
        data.get('content_text', ''),
        data.get('parsed_json', ''),
        resume_id
    ))
    conn.commit()
    conn.close()


def delete_resume(resume_id):
    """删除简历"""
    conn = get_db()
    # 先获取文件路径
    row = conn.execute('SELECT file_path FROM resumes WHERE id = ?', (resume_id,)).fetchone()
    conn.execute('DELETE FROM resumes WHERE id = ?', (resume_id,))
    conn.commit()
    conn.close()
    # 删除上传的文件
    if row and row['file_path'] and os.path.exists(row['file_path']):
        try:
            os.remove(row['file_path'])
        except Exception:
            pass


def get_resume_count():
    """获取简历总数"""
    conn = get_db()
    count = conn.execute('SELECT COUNT(*) FROM resumes').fetchone()[0]
    conn.close()
    return count


def get_week_resume_count():
    """获取本周新增简历数"""
    from utils.helpers import get_week_start
    conn = get_db()
    count = conn.execute(
        'SELECT COUNT(*) FROM resumes WHERE created_at >= ?',
        (get_week_start().strftime('%Y-%m-%d'),)
    ).fetchone()[0]
    conn.close()
    return count


def get_recent_resumes(limit=5):
    """获取最近上传的简历"""
    conn = get_db()
    rows = conn.execute(
        'SELECT * FROM resumes ORDER BY created_at DESC LIMIT ?', (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ========== 职位 CRUD 操作 ==========

def add_job(data):
    """添加职位"""
    conn = get_db()
    conn.execute('''
        INSERT INTO jobs (title, department, salary_min, salary_max,
            education_required, experience_required, age_min, age_max,
            skills_required, description, requirements, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data.get('title', ''),
        data.get('department', ''),
        data.get('salary_min', 0),
        data.get('salary_max', 0),
        data.get('education_required', ''),
        data.get('experience_required', 0),
        data.get('age_min', 0),
        data.get('age_max', 0),
        data.get('skills_required', ''),
        data.get('description', ''),
        data.get('requirements', ''),
        data.get('status', '招聘中'),
    ))
    conn.commit()
    job_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.close()
    return job_id


def get_all_jobs(page=1, per_page=20):
    """获取职位列表（分页）"""
    conn = get_db()
    offset = (page - 1) * per_page
    total = conn.execute('SELECT COUNT(*) FROM jobs').fetchone()[0]
    jobs = conn.execute(
        'SELECT * FROM jobs ORDER BY created_at DESC LIMIT ? OFFSET ?',
        (per_page, offset)
    ).fetchall()
    conn.close()
    return [dict(j) for j in jobs], total


def get_job_by_id(job_id):
    """根据ID获取职位"""
    conn = get_db()
    row = conn.execute('SELECT * FROM jobs WHERE id = ?', (job_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_job(job_id, data):
    """更新职位"""
    conn = get_db()
    conn.execute('''
        UPDATE jobs SET title=?, department=?, salary_min=?, salary_max=?,
            education_required=?, experience_required=?, age_min=?, age_max=?,
            skills_required=?, description=?, requirements=?, status=?
        WHERE id=?
    ''', (
        data.get('title', ''),
        data.get('department', ''),
        data.get('salary_min', 0),
        data.get('salary_max', 0),
        data.get('education_required', ''),
        data.get('experience_required', 0),
        data.get('age_min', 0),
        data.get('age_max', 0),
        data.get('skills_required', ''),
        data.get('description', ''),
        data.get('requirements', ''),
        data.get('status', '招聘中'),
        job_id
    ))
    conn.commit()
    conn.close()


def delete_job(job_id):
    """删除职位"""
    conn = get_db()
    conn.execute('DELETE FROM jobs WHERE id = ?', (job_id,))
    conn.commit()
    conn.close()


def get_job_count():
    """获取职位总数"""
    conn = get_db()
    count = conn.execute('SELECT COUNT(*) FROM jobs').fetchone()[0]
    conn.close()
    return count


def get_active_job_count():
    """获取招聘中的职位数"""
    conn = get_db()
    count = conn.execute(
        "SELECT COUNT(*) FROM jobs WHERE status = '招聘中'"
    ).fetchone()[0]
    conn.close()
    return count


def get_recent_jobs(limit=5):
    """获取最近发布的职位"""
    conn = get_db()
    rows = conn.execute(
        'SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?', (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_jobs_simple():
    """获取所有职位（简单列表，用于下拉选择）"""
    conn = get_db()
    rows = conn.execute(
        "SELECT id, title FROM jobs WHERE status = '招聘中' ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
