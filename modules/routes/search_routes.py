"""智能搜索匹配路由"""
from flask import Blueprint, render_template, request
from modules.models import get_all_resumes, get_job_by_id, get_all_jobs_simple
from modules.matcher import match_resumes_to_job
from modules.auth import login_required

search_bp = Blueprint('search', __name__, url_prefix='/search')

@search_bp.before_request
@login_required
def before_request():
    pass


@search_bp.route('/', methods=['GET', 'POST'])
def search_view():
    """搜索匹配页面"""
    # 获取所有招聘中的职位（用于下拉选择）
    jobs = get_all_jobs_simple()
    match_results = []
    selected_job_id = None
    filters = {}

    if request.method == 'POST':
        selected_job_id = request.form.get('job_id', type=int)
        filters = {
            'age_min': request.form.get('age_min', type=int, default=0),
            'age_max': request.form.get('age_max', type=int, default=0),
            'education': request.form.get('education', ''),
            'skill_keyword': request.form.get('skill_keyword', ''),
            'experience_min': request.form.get('experience_min', type=int, default=0),
        }

        if selected_job_id:
            job = get_job_by_id(selected_job_id)
            if job:
                # 如果用户没有设置筛选条件，使用职位的默认条件
                if filters['age_min'] == 0:
                    filters['age_min'] = job.get('age_min', 0)
                if filters['age_max'] == 0:
                    filters['age_max'] = job.get('age_max', 0)
                if not filters['education']:
                    filters['education'] = job.get('education_required', '')
                if filters['experience_min'] == 0:
                    filters['experience_min'] = job.get('experience_required', 0)

                # 获取所有简历
                resumes, _ = get_all_resumes(page=1, per_page=1000)

                # 应用筛选条件过滤简历
                filtered_resumes = _filter_resumes(resumes, filters)

                # 对过滤后的简历进行匹配打分
                if filtered_resumes:
                    match_results = match_resumes_to_job(job, filtered_resumes, top_n=3)

    return render_template('search/search.html',
                           jobs=jobs,
                           match_results=match_results,
                           selected_job_id=selected_job_id,
                           filters=filters)


def _filter_resumes(resumes, filters):
    """根据筛选条件过滤简历"""
    filtered = list(resumes)

    # 年龄过滤
    if filters.get('age_min', 0) > 0:
        filtered = [r for r in filtered if r.get('age', 0) >= filters['age_min']]
    if filters.get('age_max', 0) > 0:
        filtered = [r for r in filtered if r.get('age', 0) <= filters['age_max']]

    # 学历过滤
    if filters.get('education'):
        from utils.helpers import get_education_level
        required_level = get_education_level(filters['education'])
        if required_level > 0:
            filtered = [r for r in filtered
                        if get_education_level(r.get('education', '')) >= required_level]

    # 技能关键词过滤
    if filters.get('skill_keyword'):
        keyword = filters['skill_keyword'].lower()
        filtered = [r for r in filtered
                    if keyword in (r.get('skills', '') + r.get('content_text', '')).lower()]

    # 经验过滤
    if filters.get('experience_min', 0) > 0:
        filtered = [r for r in filtered
                    if r.get('experience_years', 0) >= filters['experience_min']]

    return filtered
