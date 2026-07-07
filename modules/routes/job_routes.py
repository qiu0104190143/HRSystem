"""职位管理路由"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from modules.models import (
    add_job, get_all_jobs, get_job_by_id,
    update_job, delete_job, get_all_resumes
)
from modules.matcher import match_resumes_to_job

job_bp = Blueprint('jobs', __name__, url_prefix='/jobs')


@job_bp.route('/')
def list_view():
    """职位列表页"""
    page = request.args.get('page', 1, type=int)
    jobs, total = get_all_jobs(page=page)
    total_pages = max(1, (total + 19) // 20)
    return render_template('jobs/list.html',
                           jobs=jobs, page=page,
                           total=total, total_pages=total_pages)


@job_bp.route('/create', methods=['GET', 'POST'])
def create_view():
    """创建职位"""
    if request.method == 'POST':
        data = {
            'title': request.form.get('title', ''),
            'department': request.form.get('department', ''),
            'salary_min': int(request.form.get('salary_min', 0)),
            'salary_max': int(request.form.get('salary_max', 0)),
            'education_required': request.form.get('education_required', ''),
            'experience_required': int(request.form.get('experience_required', 0)),
            'age_min': int(request.form.get('age_min', 0)),
            'age_max': int(request.form.get('age_max', 0)),
            'skills_required': request.form.get('skills_required', ''),
            'description': request.form.get('description', ''),
            'requirements': request.form.get('requirements', ''),
            'status': '招聘中',
        }

        if not data['title']:
            flash('请输入职位名称', 'warning')
            return render_template('jobs/create.html', job=data)

        job_id = add_job(data)
        flash(f'职位 "{data["title"]}" 发布成功！', 'success')
        return redirect(url_for('jobs.detail_view', job_id=job_id))

    return render_template('jobs/create.html', job={})


@job_bp.route('/<int:job_id>')
def detail_view(job_id):
    """职位详情页（含匹配候选人）"""
    job = get_job_by_id(job_id)
    if not job:
        flash('职位不存在', 'danger')
        return redirect(url_for('jobs.list_view'))

    # 自动匹配该职位最合适的3份简历
    resumes, _ = get_all_resumes(page=1, per_page=1000)
    match_results = []
    if resumes:
        match_results = match_resumes_to_job(job, resumes, top_n=3)

    return render_template('jobs/detail.html', job=job, match_results=match_results)


@job_bp.route('/<int:job_id>/edit', methods=['GET', 'POST'])
def edit_view(job_id):
    """编辑职位"""
    job = get_job_by_id(job_id)
    if not job:
        flash('职位不存在', 'danger')
        return redirect(url_for('jobs.list_view'))

    if request.method == 'POST':
        data = {
            'title': request.form.get('title', ''),
            'department': request.form.get('department', ''),
            'salary_min': int(request.form.get('salary_min', 0)),
            'salary_max': int(request.form.get('salary_max', 0)),
            'education_required': request.form.get('education_required', ''),
            'experience_required': int(request.form.get('experience_required', 0)),
            'age_min': int(request.form.get('age_min', 0)),
            'age_max': int(request.form.get('age_max', 0)),
            'skills_required': request.form.get('skills_required', ''),
            'description': request.form.get('description', ''),
            'requirements': request.form.get('requirements', ''),
            'status': request.form.get('status', '招聘中'),
        }
        update_job(job_id, data)
        flash('职位更新成功！', 'success')
        return redirect(url_for('jobs.detail_view', job_id=job_id))

    return render_template('jobs/create.html', job=job)


@job_bp.route('/<int:job_id>/delete', methods=['POST'])
def delete_view(job_id):
    """删除职位"""
    delete_job(job_id)
    flash('职位已删除', 'info')
    return redirect(url_for('jobs.list_view'))


@job_bp.route('/<int:job_id>/toggle-status', methods=['POST'])
def toggle_status(job_id):
    """切换职位状态（招聘中/已关闭）"""
    job = get_job_by_id(job_id)
    if job:
        new_status = '已关闭' if job.get('status') == '招聘中' else '招聘中'
        job['status'] = new_status
        update_job(job_id, job)
        flash(f'职位状态已更新为"{new_status}"', 'success')
    return redirect(url_for('jobs.detail_view', job_id=job_id))
