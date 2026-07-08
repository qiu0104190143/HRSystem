"""简历管理路由"""
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from modules.models import (
    add_resume, get_all_resumes, get_resume_by_id,
    update_resume, delete_resume
)
from modules.resume_parser import parse_resume

from modules.auth import login_required

resume_bp = Blueprint('resumes', __name__, url_prefix='/resumes')

@resume_bp.before_request
@login_required
def before_request():
    pass

ALLOWED_EXTENSIONS = {'txt', 'docx', 'pdf'}


def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@resume_bp.route('/')
def list_view():
    """简历列表页"""
    page = request.args.get('page', 1, type=int)
    resumes, total = get_all_resumes(page=page)
    total_pages = max(1, (total + 19) // 20)
    return render_template('resumes/list.html',
                           resumes=resumes, page=page,
                           total=total, total_pages=total_pages)


@resume_bp.route('/upload', methods=['GET', 'POST'])
def upload_view():
    """上传简历页"""
    if request.method == 'POST':
        # 检查是否有文件
        if 'file' not in request.files:
            flash('请选择文件', 'warning')
            return render_template('resumes/upload.html')

        file = request.files['file']
        if file.filename == '':
            flash('请选择文件', 'warning')
            return render_template('resumes/upload.html')

        if not allowed_file(file.filename):
            flash('不支持的文件格式，请上传 txt、docx 或 pdf 文件', 'warning')
            return render_template('resumes/upload.html')

        # 保存文件
        file_type = file.filename.rsplit('.', 1)[1].lower()
        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)

        # 用时间戳避免文件名重复
        import time
        saved_filename = f"{int(time.time())}_{file.filename}"
        filepath = os.path.join(upload_folder, saved_filename)
        file.save(filepath)

        # 解析简历
        parsed = parse_resume(filepath, file_type)

        # 合并用户手动输入的信息
        parsed['name'] = request.form.get('name', parsed.get('name', ''))
        parsed['gender'] = request.form.get('gender', parsed.get('gender', ''))
        parsed['age'] = int(request.form.get('age', parsed.get('age', 0)))
        parsed['phone'] = request.form.get('phone', parsed.get('phone', ''))
        parsed['email'] = request.form.get('email', parsed.get('email', ''))
        parsed['education'] = request.form.get('education', parsed.get('education', ''))
        parsed['school'] = request.form.get('school', parsed.get('school', ''))
        parsed['major'] = request.form.get('major', parsed.get('major', ''))
        parsed['skills'] = request.form.get('skills', parsed.get('skills', ''))
        parsed['experience_years'] = int(request.form.get('experience_years', parsed.get('experience_years', 0)))
        parsed['current_company'] = request.form.get('current_company', parsed.get('current_company', ''))
        parsed['current_position'] = request.form.get('current_position', parsed.get('current_position', ''))
        parsed['file_path'] = filepath
        parsed['file_type'] = file_type

        # 保存到数据库
        resume_id = add_resume(parsed)
        flash(f'简历 "{parsed["name"] or "未知姓名"}" 上传成功！', 'success')
        return redirect(url_for('resumes.detail_view', resume_id=resume_id))

    return render_template('resumes/upload.html')


@resume_bp.route('/<int:resume_id>')
def detail_view(resume_id):
    """简历详情页"""
    resume = get_resume_by_id(resume_id)
    if not resume:
        flash('简历不存在', 'danger')
        return redirect(url_for('resumes.list_view'))
    return render_template('resumes/detail.html', resume=resume)


@resume_bp.route('/<int:resume_id>/edit', methods=['GET', 'POST'])
def edit_view(resume_id):
    """编辑简历"""
    resume = get_resume_by_id(resume_id)
    if not resume:
        flash('简历不存在', 'danger')
        return redirect(url_for('resumes.list_view'))

    if request.method == 'POST':
        data = {
            'name': request.form.get('name', ''),
            'gender': request.form.get('gender', ''),
            'age': int(request.form.get('age', 0)),
            'phone': request.form.get('phone', ''),
            'email': request.form.get('email', ''),
            'education': request.form.get('education', ''),
            'school': request.form.get('school', ''),
            'major': request.form.get('major', ''),
            'skills': request.form.get('skills', ''),
            'experience_years': int(request.form.get('experience_years', 0)),
            'current_company': request.form.get('current_company', ''),
            'current_position': request.form.get('current_position', ''),
            'content_text': resume.get('content_text', ''),
        }
        update_resume(resume_id, data)
        flash('简历更新成功！', 'success')
        return redirect(url_for('resumes.detail_view', resume_id=resume_id))

    return render_template('resumes/edit.html', resume=resume)


@resume_bp.route('/<int:resume_id>/delete', methods=['POST'])
def delete_view(resume_id):
    """删除简历"""
    delete_resume(resume_id)
    flash('简历已删除', 'info')
    return redirect(url_for('resumes.list_view'))
