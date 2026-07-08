"""统计数据API模块 — 为前端图表提供数据"""
from flask import Blueprint, jsonify
from modules.models import get_db
from modules.auth import login_required
from collections import Counter
from datetime import datetime, timedelta

stats_bp = Blueprint('stats', __name__, url_prefix='/api/stats')

@stats_bp.before_request
@login_required
def before_request():
    pass


@stats_bp.route('/dashboard')
def dashboard_stats():
    """仪表盘综合统计数据"""
    conn = get_db()

    # 简历总数
    total_resumes = conn.execute('SELECT COUNT(*) FROM resumes').fetchone()[0]

    # 职位总数
    total_jobs = conn.execute('SELECT COUNT(*) FROM jobs').fetchone()[0]
    active_jobs = conn.execute("SELECT COUNT(*) FROM jobs WHERE status = '招聘中'").fetchone()[0]

    # 本月新增简历
    month_start = datetime.now().replace(day=1).strftime('%Y-%m-%d')
    month_resumes = conn.execute(
        'SELECT COUNT(*) FROM resumes WHERE created_at >= ?', (month_start,)
    ).fetchone()[0]

    conn.close()
    return jsonify({
        'total_resumes': total_resumes,
        'total_jobs': total_jobs,
        'active_jobs': active_jobs,
        'month_resumes': month_resumes,
    })


@stats_bp.route('/resume-trend')
def resume_trend():
    """简历上传趋势（最近30天）"""
    conn = get_db()
    data = []
    for i in range(29, -1, -1):
        day = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        count = conn.execute(
            'SELECT COUNT(*) FROM resumes WHERE date(created_at) = ?', (day,)
        ).fetchone()[0]
        data.append({'date': day[5:], 'count': count})  # 只显示MM-DD
    conn.close()
    return jsonify(data)


@stats_bp.route('/education-dist')
def education_dist():
    """学历分布"""
    conn = get_db()
    rows = conn.execute(
        'SELECT education, COUNT(*) as cnt FROM resumes WHERE education != "" GROUP BY education'
    ).fetchall()
    conn.close()
    return jsonify([{'name': r['education'], 'value': r['cnt']} for r in rows])


@stats_bp.route('/job-status')
def job_status():
    """职位状态分布"""
    conn = get_db()
    rows = conn.execute(
        'SELECT status, COUNT(*) as cnt FROM jobs GROUP BY status'
    ).fetchall()
    conn.close()
    return jsonify([{'name': r['status'], 'value': r['cnt']} for r in rows])


@stats_bp.route('/recent-activities')
def recent_activities():
    """最近动态（简历+职位）"""
    conn = get_db()
    resumes = conn.execute(
        "SELECT 'resume' as type, name, education, created_at FROM resumes ORDER BY created_at DESC LIMIT 5"
    ).fetchall()
    jobs = conn.execute(
        "SELECT 'job' as type, title as name, status, created_at FROM jobs ORDER BY created_at DESC LIMIT 5"
    ).fetchall()
    conn.close()

    activities = []
    for r in resumes:
        activities.append({
            'type': 'resume',
            'title': f"新简历：{r['name'] or '未命名'}",
            'subtitle': r['education'] or '',
            'time': r['created_at'],
            'icon': 'file-earmark-person',
            'color': 'primary',
        })
    for j in jobs:
        activities.append({
            'type': 'job',
            'title': f"{'发布' if j['status'] == '招聘中' else '更新'}职位：{j['name']}",
            'subtitle': j['status'] or '',
            'time': j['created_at'],
            'icon': 'briefcase',
            'color': 'success' if j['status'] == '招聘中' else 'secondary',
        })

    # 按时间排序，取最近10条
    activities.sort(key=lambda x: x['time'] or '', reverse=True)
    return jsonify(activities[:10])
