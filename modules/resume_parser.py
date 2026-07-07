"""简历解析模块 — 支持 txt、docx、pdf 格式"""
import os


def parse_resume(filepath, file_type):
    """
    解析简历文件，提取文本内容和结构化信息

    参数:
        filepath: 文件路径
        file_type: 文件类型 (txt/docx/pdf)

    返回:
        dict: {
            'content_text': 全文内容,
            'name': 提取的姓名,
            'age': 提取的年龄,
            'education': 提取的学历,
            'skills': 提取的技能,
            ...
        }
    """
    # 1. 提取纯文本内容
    if file_type == 'txt':
        content_text = _parse_txt(filepath)
    elif file_type == 'docx':
        content_text = _parse_docx(filepath)
    elif file_type == 'pdf':
        content_text = _parse_pdf(filepath)
    else:
        content_text = ''

    if not content_text:
        return {'content_text': '', 'name': '', 'age': 0}

    # 2. 从文本中智能提取结构化信息
    info = _extract_info(content_text)
    info['content_text'] = content_text

    return info


def _parse_txt(filepath):
    """解析纯文本文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            with open(filepath, 'r', encoding='gbk') as f:
                return f.read()
        except Exception:
            return ''


def _parse_docx(filepath):
    """解析Word文档(.docx)"""
    try:
        from docx import Document
        doc = Document(filepath)
        paragraphs = []
        for para in doc.paragraphs:
            if para.text.strip():
                paragraphs.append(para.text.strip())
        # 也读取表格中的内容
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text.strip():
                        paragraphs.append(cell.text.strip())
        return '\n'.join(paragraphs)
    except Exception as e:
        return f'[Word解析错误: {e}]'


def _parse_pdf(filepath):
    """解析PDF文件"""
    # 优先使用 pdfplumber（效果更好）
    try:
        import pdfplumber
        text_parts = []
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
        return '\n'.join(text_parts)
    except Exception:
        pass

    # 回退到 PyPDF2
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(filepath)
        text_parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        return '\n'.join(text_parts)
    except Exception as e:
        return f'[PDF解析错误: {e}]'


def _extract_info(text):
    """
    从简历文本中智能提取结构化信息
    使用正则表达式和关键词匹配
    """
    import re

    info = {
        'name': '',
        'gender': '',
        'age': 0,
        'phone': '',
        'email': '',
        'education': '',
        'school': '',
        'major': '',
        'skills': '',
        'experience_years': 0,
        'current_company': '',
        'current_position': '',
    }

    lines = text.split('\n')

    # ---- 提取姓名 ----
    # 通常简历第一行是姓名
    for line in lines[:5]:
        line = line.strip()
        # 排除明显不是姓名的行
        if line and len(line) >= 2 and len(line) <= 6 and not any(
            kw in line for kw in ['简历', '个人', '联系', '电话', '邮箱', '求职', '应聘']
        ):
            # 中文姓名通常是2-4个字
            if re.match(r'^[一-龥·]{2,6}$', line):
                info['name'] = line
                break

    # ---- 提取邮箱 ----
    email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    if email_match:
        info['email'] = email_match.group()

    # ---- 提取电话 ----
    phone_match = re.search(r'1[3-9]\d{9}', text)
    if phone_match:
        info['phone'] = phone_match.group()

    # ---- 提取性别 ----
    if '男' in text[:200]:
        info['gender'] = '男'
    elif '女' in text[:200]:
        info['gender'] = '女'

    # ---- 提取年龄 ----
    age_patterns = [
        r'年龄[：:]\s*(\d{1,2})',
        r'(\d{1,2})\s*岁',
    ]
    for pattern in age_patterns:
        age_match = re.search(pattern, text)
        if age_match:
            age = int(age_match.group(1))
            if 18 <= age <= 70:
                info['age'] = age
                break

    # ---- 提取学历 ----
    edu_keywords = ['博士', '博士后', '硕士', '研究生', '本科', '学士', '大专', '中专', '高中']
    for edu in edu_keywords:
        if edu in text[:500]:
            if edu == '研究生':
                info['education'] = '硕士'
            elif edu == '学士':
                info['education'] = '本科'
            else:
                info['education'] = edu
            break

    # ---- 提取毕业院校 ----
    school_patterns = [
        r'(?:毕业院校|学校|院校|大学|学院)[：:]\s*([^\n]{2,20})',
        r'([^\n]{2,20})(?:大学|学院)',
    ]
    for pattern in school_patterns:
        school_match = re.search(pattern, text[:500])
        if school_match:
            school = school_match.group(1).strip()
            if len(school) >= 2 and not any(kw in school for kw in ['联系', '电话', '邮箱']):
                info['school'] = school
                break

    # ---- 提取专业 ----
    major_match = re.search(r'(?:专业)[：:]\s*([^\n]{2,20})', text[:500])
    if major_match:
        info['major'] = major_match.group(1).strip()

    # ---- 提取技能 ----
    info['skills'] = _extract_skills(text)

    # ---- 提取工作年限 ----
    exp_patterns = [
        r'(\d{1,2})\s*年(?:工作)?经验',
        r'工作经验[：:]\s*(\d{1,2})\s*年',
        r'工作年限[：:]\s*(\d{1,2})',
    ]
    for pattern in exp_patterns:
        exp_match = re.search(pattern, text)
        if exp_match:
            info['experience_years'] = int(exp_match.group(1))
            break

    # ---- 提取当前公司 ----
    company_match = re.search(r'(?:公司|企业)[：:]\s*([^\n]{2,30})', text[:800])
    if company_match:
        info['current_company'] = company_match.group(1).strip()

    # ---- 提取当前职位 ----
    position_match = re.search(r'(?:职位|岗位|职务)[：:]\s*([^\n]{2,20})', text[:800])
    if position_match:
        info['current_position'] = position_match.group(1).strip()

    return info


# 常见技能关键词库
SKILL_KEYWORDS = [
    # 编程语言
    'Python', 'Java', 'JavaScript', 'TypeScript', 'C++', 'C#', 'Go', 'Rust',
    'PHP', 'Ruby', 'Swift', 'Kotlin', 'Scala', 'R', 'MATLAB', 'Shell',
    # Web前端
    'HTML', 'CSS', 'React', 'Vue', 'Angular', 'jQuery', 'Bootstrap',
    'Node.js', 'Webpack', 'Vite', 'Next.js', 'Nuxt',
    # 后端框架
    'Spring', 'Django', 'Flask', 'Express', 'FastAPI', 'MyBatis', 'Hibernate',
    '.NET', 'Laravel', 'Rails', 'Gin',
    # 数据库
    'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'Oracle', 'SQL Server',
    'SQLite', 'Elasticsearch', 'DynamoDB', 'HBase',
    # 云计算与DevOps
    'AWS', 'Azure', '阿里云', 'Docker', 'Kubernetes', 'Jenkins', 'Git',
    'CI/CD', 'Nginx', 'Linux', 'Tomcat', 'Ansible', 'Terraform',
    # 大数据与AI
    'Hadoop', 'Spark', 'Flink', 'Kafka', 'TensorFlow', 'PyTorch',
    '机器学习', '深度学习', 'NLP', '数据分析', '数据挖掘',
    # 通用技能
    '项目管理', '团队管理', '产品设计', 'UI/UX', 'Figma', 'Sketch',
    'Photoshop', 'Office', 'Excel', 'PPT', '沟通能力', '英语', '日语',
    # 财务与人力资源
    '财务分析', '会计', '审计', '税务', '招聘', '培训', '绩效管理',
    '薪酬福利', '人力资源', 'HR', '财务', '出纳',
]


def _extract_skills(text):
    """从文本中提取技能关键词"""
    found_skills = []
    text_lower = text.lower()
    for skill in SKILL_KEYWORDS:
        if skill.lower() in text_lower:
            found_skills.append(skill)
    return '，'.join(found_skills)
