"""用户认证模块 — 登录/退出/权限验证"""
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from modules.models import verify_user

auth_bp = Blueprint('auth', __name__)


def login_required(f):
    """登录验证装饰器：未登录自动跳转到登录页"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login_view'))
        return f(*args, **kwargs)
    return decorated_function


@auth_bp.route('/login', methods=['GET', 'POST'])
def login_view():
    """登录页面"""
    # 如果已登录，直接跳到首页
    if 'user_id' in session:
        return redirect(url_for('index'))

    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            error = '请输入账号和密码'
        else:
            user = verify_user(username, password)
            if user:
                session['user_id'] = user['id']
                session['username'] = user['username']
                flash(f'欢迎回来，{user["display_name"] or user["username"]}！', 'success')
                return redirect(url_for('index'))
            else:
                error = '账号或密码错误'

    return render_template('login.html', error=error)


@auth_bp.route('/logout')
def logout_view():
    """退出登录"""
    session.clear()
    flash('已安全退出', 'info')
    return redirect(url_for('auth.login_view'))
