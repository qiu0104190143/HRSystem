"""系统设置路由"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from modules.models import get_setting, save_setting, get_all_settings
from modules.auth import login_required

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')


@settings_bp.before_request
@login_required
def before_request():
    pass


@settings_bp.route('/', methods=['GET', 'POST'])
def settings_view():
    """系统设置页面"""
    if request.method == 'POST':
        # 保存API配置
        save_setting('ai_api_key', request.form.get('ai_api_key', '').strip())
        save_setting('ai_api_url', request.form.get('ai_api_url', 'https://api.deepseek.com/v1/chat/completions').strip())
        save_setting('ai_model', request.form.get('ai_model', 'deepseek-chat').strip())
        flash('设置已保存！AI解析功能已就绪', 'success')
        return redirect(url_for('settings.settings_view'))

    # 读取当前设置
    config = {
        'ai_api_key': get_setting('ai_api_key', ''),
        'ai_api_url': get_setting('ai_api_url', 'https://api.deepseek.com/v1/chat/completions'),
        'ai_model': get_setting('ai_model', ''),
    }
    # 隐藏API Key中间部分
    masked_key = ''
    if config['ai_api_key']:
        key = config['ai_api_key']
        if len(key) > 8:
            masked_key = key[:4] + '*' * (len(key) - 8) + key[-4:]
        else:
            masked_key = '****'

    return render_template('settings/index.html', config=config, masked_key=masked_key)
