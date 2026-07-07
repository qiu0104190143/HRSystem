"""工具函数模块"""
import socket
from datetime import datetime, timedelta


def get_local_ip():
    """获取本机局域网IP地址"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'


def format_datetime(dt):
    """格式化日期时间为友好格式"""
    if dt is None:
        return ''
    if isinstance(dt, str):
        try:
            dt = datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return dt
    return dt.strftime('%Y-%m-%d %H:%M')


def get_week_start():
    """获取本周一的日期"""
    today = datetime.now()
    return today - timedelta(days=today.weekday())


def get_education_level(education):
    """将学历转换为数值用于比较"""
    level_map = {
        '高中': 1, '中专': 2, '大专': 3,
        '本科': 4, '学士': 4,
        '硕士': 5, '研究生': 5,
        '博士': 6, '博士后': 7
    }
    return level_map.get(education, 0)


def get_education_name(level):
    """将数值转回学历名称"""
    name_map = {
        1: '高中', 2: '中专', 3: '大专',
        4: '本科', 5: '硕士', 6: '博士', 7: '博士后'
    }
    return name_map.get(level, '未知')
