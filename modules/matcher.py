"""智能匹配引擎 — 计算简历与职位的匹配度并生成原因"""
import re
from utils.helpers import get_education_level


def match_resumes_to_job(job, resumes, top_n=3):
    """
    将简历与职位进行匹配，返回匹配度最高的N份简历

    参数:
        job: 职位字典
        resumes: 简历字典列表
        top_n: 返回前N名

    返回:
        list: [{'resume': {...}, 'score': 85, 'reasons': [...]}, ...]
    """
    results = []

    for resume in resumes:
        score, reasons = _calculate_match(job, resume)
        results.append({
            'resume': resume,
            'score': round(score, 1),
            'reasons': reasons,
            'score_level': _get_score_level(score),
        })

    # 按分数降序排序，取前N
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:top_n]


def _calculate_match(job, resume):
    """
    计算单个简历与职位的匹配度

    评分维度与权重：
    - 学历匹配: 20%
    - 技能匹配: 35%
    - 经验匹配: 20%
    - 年龄匹配: 10%
    - 关键词匹配: 15%
    """
    reasons = []
    total_score = 0

    # 1. 学历匹配 (20%)
    edu_score, edu_reason = _match_education(job, resume)
    total_score += edu_score * 0.20
    if edu_reason:
        reasons.append(edu_reason)

    # 2. 技能匹配 (35%)
    skill_score, skill_reason = _match_skills(job, resume)
    total_score += skill_score * 0.35
    if skill_reason:
        reasons.append(skill_reason)

    # 3. 经验匹配 (20%)
    exp_score, exp_reason = _match_experience(job, resume)
    total_score += exp_score * 0.20
    if exp_reason:
        reasons.append(exp_reason)

    # 4. 年龄匹配 (10%)
    age_score, age_reason = _match_age(job, resume)
    total_score += age_score * 0.10
    if age_reason:
        reasons.append(age_reason)

    # 5. 关键词匹配 (15%) — 基于简历全文与职位描述的文本相似度
    text_score, text_reason = _match_keywords(job, resume)
    total_score += text_score * 0.15
    if text_reason:
        reasons.append(text_reason)

    # 转换为百分制 (以上各项满分100，加权后即为百分制)
    return total_score, reasons


def _match_education(job, resume):
    """学历匹配"""
    job_edu = job.get('education_required', '')
    resume_edu = resume.get('education', '')

    if not job_edu:
        return 100, None

    if not resume_edu:
        return 30, {'icon': '⚠️', 'text': f'学历未知，岗位要求{job_edu}'}

    job_level = get_education_level(job_edu)
    resume_level = get_education_level(resume_edu)

    if resume_level >= job_level:
        if resume_level == job_level:
            return 100, {'icon': '✅', 'text': f'学历匹配：{resume_edu}，满足岗位要求'}
        else:
            return 100, {'icon': '✅', 'text': f'学历超出要求：{resume_edu}，高于岗位要求的{job_edu}'}
    else:
        diff = job_level - resume_level
        score = max(0, 100 - diff * 25)
        return score, {'icon': '❌', 'text': f'学历不匹配：{resume_edu}，岗位要求{job_edu}'}


def _match_skills(job, resume):
    """技能匹配"""
    job_skills_str = job.get('skills_required', '')
    resume_skills_str = resume.get('skills', '')

    if not job_skills_str:
        return 100, None

    # 解析技能标签
    job_skills = set(s.strip() for s in re.split(r'[,，、\s]+', job_skills_str) if s.strip())
    resume_skills = set(s.strip() for s in re.split(r'[,，、\s]+', resume_skills_str) if s.strip())

    # 同时从简历内容中搜索技能
    content = resume.get('content_text', '')
    content_lower = content.lower()
    for skill in list(job_skills):
        if skill.lower() in content_lower:
            resume_skills.add(skill)

    if not job_skills:
        return 100, None

    matched = job_skills & resume_skills
    missing = job_skills - resume_skills

    if len(job_skills) == 0:
        return 100, None

    ratio = len(matched) / len(job_skills)
    score = ratio * 100

    parts = []
    if matched:
        parts.append(f'具备：{"、".join(sorted(matched)[:6])}')
    if missing:
        parts.append(f'欠缺：{"、".join(sorted(missing)[:6])}')

    icon = '✅' if ratio >= 0.7 else ('⚠️' if ratio >= 0.4 else '❌')

    return score, {'icon': icon, 'text': f'技能匹配度{score:.0f}%（{len(matched)}/{len(job_skills)}）。{"; ".join(parts)}'}


def _match_experience(job, resume):
    """经验匹配"""
    job_exp = job.get('experience_required', 0)
    resume_exp = resume.get('experience_years', 0)

    if not job_exp or job_exp == 0:
        return 100, None

    if resume_exp >= job_exp:
        return 100, {'icon': '✅', 'text': f'经验匹配：{resume_exp}年工作经验，满足{job_exp}年要求'}
    else:
        ratio = resume_exp / job_exp
        score = ratio * 100
        return score, {'icon': '⚠️', 'text': f'经验不足：{resume_exp}年工作经验，岗位要求{job_exp}年'}


def _match_age(job, resume):
    """年龄匹配"""
    age_min = job.get('age_min', 0)
    age_max = job.get('age_max', 0)
    age = resume.get('age', 0)

    # 如果未设置年龄要求或候选人未填年龄
    if (age_min == 0 and age_max == 0) or age == 0:
        return 100, None

    if age_min > 0 and age_max > 0:
        if age_min <= age <= age_max:
            return 100, {'icon': '✅', 'text': f'年龄符合：{age}岁，在{age_min}-{age_max}范围内'}
        elif age < age_min:
            diff = age_min - age
            score = max(0, 100 - diff * 10)
            return score, {'icon': '⚠️', 'text': f'年龄偏小：{age}岁，要求{age_min}-{age_max}'}
        else:
            diff = age - age_max
            score = max(0, 100 - diff * 10)
            return score, {'icon': '⚠️', 'text': f'年龄偏大：{age}岁，要求{age_min}-{age_max}'}
    elif age_min > 0:
        if age >= age_min:
            return 100, {'icon': '✅', 'text': f'年龄符合：{age}岁，满足最低{age_min}岁要求'}
        else:
            return 50, {'icon': '⚠️', 'text': f'年龄不符：{age}岁，要求不低于{age_min}岁'}
    elif age_max > 0:
        if age <= age_max:
            return 100, {'icon': '✅', 'text': f'年龄符合：{age}岁，满足最高{age_max}岁要求'}
        else:
            return 50, {'icon': '⚠️', 'text': f'年龄不符：{age}岁，要求不超过{age_max}岁'}

    return 100, None


def _match_keywords(job, resume):
    """关键词文本匹配（使用TF-IDF思想简化版）"""
    job_text = f"{job.get('title', '')} {job.get('description', '')} {job.get('requirements', '')} {job.get('skills_required', '')}"
    resume_text = f"{resume.get('content_text', '')} {resume.get('skills', '')}"

    if not job_text.strip() or not resume_text.strip():
        return 50, None

    # 使用jieba分词
    try:
        import jieba
        job_words = set(jieba.cut(job_text))
        resume_words = set(jieba.cut(resume_text))
    except Exception:
        # 如果jieba不可用，使用简单的字符匹配
        job_words = set(job_text)
        resume_words = set(resume_text)

    # 过滤停用词和短词
    stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
                  '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
                  '自己', '这', '他', '她', '它', '们', '那', '些', '所', '为', '所以', '因为',
                  '但是', '然而', '虽然', '如果', '可以', '能够', '需要', '应该', ' ', '\n', '\t'}
    job_words = {w for w in job_words if len(w) >= 2 and w not in stop_words}
    resume_words = {w for w in resume_words if len(w) >= 2 and w not in stop_words}

    if not job_words:
        return 50, None

    # 计算Jaccard相似度
    intersection = job_words & resume_words
    union = job_words | resume_words

    if len(union) == 0:
        return 50, None

    similarity = len(intersection) / len(union)
    score = similarity * 100

    # 调整：相似度通常较低，进行适当放大
    score = min(100, score * 3)

    if score >= 60:
        return score, {'icon': '✅', 'text': f'内容相关性高：简历内容与岗位描述匹配度较高'}
    elif score >= 30:
        return score, {'icon': '⚠️', 'text': f'内容相关性一般：简历内容与岗位描述部分匹配'}
    else:
        return score, {'icon': '⚠️', 'text': f'内容相关性较低：简历内容与岗位描述匹配度不高'}


def _get_score_level(score):
    """获取匹配等级"""
    if score >= 80:
        return 'high'       # 绿色
    elif score >= 60:
        return 'medium'     # 黄色
    else:
        return 'low'        # 红色
