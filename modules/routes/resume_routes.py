"""简历管理路由"""
import os
import json
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
    """上传简历页 — 支持批量上传"""
    if request.method == 'POST':
        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            flash('请选择至少一个文件', 'warning')
            return render_template('resumes/upload.html')

        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)
        import time

        results = []
        for file in files:
            result = {'filename': file.filename, 'success': False, 'error': '', 'resume_id': None, 'name': ''}
            if file.filename == '':
                result['error'] = '空文件名'
                results.append(result)
                continue
            if not allowed_file(file.filename):
                result['error'] = '不支持的格式'
                results.append(result)
                continue

            try:
                file_type = file.filename.rsplit('.', 1)[1].lower()
                saved_filename = f"{int(time.time() * 1000)}_{file.filename}"
                filepath = os.path.join(upload_folder, saved_filename)
                file.save(filepath)

                # 解析简历
                parsed = parse_resume(filepath, file_type)

                # 合并用户手动输入（批量上传时共用同一组补充信息）
                parsed['name'] = request.form.get('name', parsed.get('name', ''))
                parsed['gender'] = request.form.get('gender', parsed.get('gender', ''))
                try:
                    parsed['age'] = int(request.form.get('age', 0) or parsed.get('age', 0))
                except ValueError:
                    parsed['age'] = parsed.get('age', 0)
                parsed['phone'] = request.form.get('phone', parsed.get('phone', ''))
                parsed['email'] = request.form.get('email', parsed.get('email', ''))
                parsed['education'] = request.form.get('education', parsed.get('education', ''))
                parsed['school'] = request.form.get('school', parsed.get('school', ''))
                parsed['major'] = request.form.get('major', parsed.get('major', ''))
                parsed['skills'] = request.form.get('skills', parsed.get('skills', ''))
                try:
                    parsed['experience_years'] = int(request.form.get('experience_years', 0) or parsed.get('experience_years', 0))
                except ValueError:
                    parsed['experience_years'] = parsed.get('experience_years', 0)
                parsed['current_company'] = request.form.get('current_company', parsed.get('current_company', ''))
                parsed['current_position'] = request.form.get('current_position', parsed.get('current_position', ''))
                parsed['file_path'] = filepath
                parsed['file_type'] = file_type

                resume_id = add_resume(parsed)
                result['success'] = True
                result['resume_id'] = resume_id
                result['name'] = parsed.get('name', '') or '未命名'
            except Exception as e:
                result['error'] = str(e)[:100]

            results.append(result)

        success_count = sum(1 for r in results if r['success'])
        fail_count = len(results) - success_count

        if success_count > 0:
            flash(f'成功上传 {success_count} 份简历' + (f'，{fail_count} 份失败' if fail_count > 0 else ''), 'success')

        return render_template('resumes/upload_result.html',
                               results=results,
                               success_count=success_count,
                               fail_count=fail_count)

    return render_template('resumes/upload.html')


@resume_bp.route('/<int:resume_id>')
def detail_view(resume_id):
    """简历详情页"""
    resume = get_resume_by_id(resume_id)
    if not resume:
        flash('简历不存在', 'danger')
        return redirect(url_for('resumes.list_view'))

    # 解析parsed_json用于展示
    parsed_data = None
    if resume.get('parsed_json'):
        try:
            parsed_data = json.loads(resume['parsed_json'])
        except (json.JSONDecodeError, TypeError):
            pass

    return render_template('resumes/detail.html', resume=resume, parsed_data=parsed_data)


@resume_bp.route('/<int:resume_id>/reparse', methods=['POST'])
def reparse_view(resume_id):
    """重新解析已有简历的结构化信息"""
    resume = get_resume_by_id(resume_id)
    if not resume:
        flash('简历不存在', 'danger')
        return redirect(url_for('resumes.list_view'))

    filepath = resume.get('file_path', '')
    file_type = resume.get('file_type', '')
    content_text = resume.get('content_text', '')

    if filepath and os.path.exists(filepath) and file_type:
        # 重新解析原始文件
        parsed = parse_resume(filepath, file_type)
    elif content_text:
        # 文件丢失，从已存储的文本重新提取
        parsed = {}
        from modules.resume_parser import _extract_info
        info = _extract_info(content_text)
        parsed.update(info)
        parsed['content_text'] = content_text
        import json as _json
        parsed['parsed_json'] = _json.dumps({
            'basic': {'name': info.get('name',''),'gender': info.get('gender',''),'age': info.get('age',0),'phone': info.get('phone',''),'email': info.get('email','')},
            'education': {'level': info.get('education',''),'school': info.get('school',''),'major': info.get('major','')},
            'work': {'years': info.get('experience_years',0),'current_company': info.get('current_company',''),'current_position': info.get('current_position','')},
            'skills': [s.strip() for s in info.get('skills','').replace('，',',').split(',') if s.strip()],
            'raw_text': content_text,
        }, ensure_ascii=False)
    else:
        flash('无法重新解析：原始文件不存在且无存储文本', 'danger')
        return redirect(url_for('resumes.detail_view', resume_id=resume_id))

    # 保留用户已手动修改的信息
    for field in ['name','gender','age','phone','email','education','school','major',
                  'experience_years','current_company','current_position']:
        original = resume.get(field, '')
        if original and original != parsed.get(field, ''):
            parsed[field] = original  # 保留手动修改

    parsed['skills'] = request.form.get('skills_override', parsed.get('skills', resume.get('skills', '')))
    parsed['parsed_json'] = parsed.get('parsed_json', resume.get('parsed_json', ''))

    update_resume(resume_id, parsed)
    flash('简历信息已重新解析！可在下方查看更新后的结构化数据', 'success')
    return redirect(url_for('resumes.detail_view', resume_id=resume_id))


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
            'parsed_json': resume.get('parsed_json', ''),
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
