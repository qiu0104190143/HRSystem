"""智能匹配引擎 — 计算简历与职位的匹配度并生成原因"""
import re
import json
from utils.helpers import get_education_level


def _get_parsed_data(resume):
    """优先从parsed_json读取结构化数据，回退到普通字段"""
    pj = resume.get('parsed_json', '')
    if pj:
        try:
            return json.loads(pj)
        except (json.JSONDecodeError, TypeError):
            pass
    return None


# 技能别名映射（模糊匹配）
SKILL_ALIASES = {
    'react': ['react', 'react.js', 'reactjs'],
    'vue': ['vue', 'vue.js', 'vuejs'],
    'node.js': ['node', 'node.js', 'nodejs'],
    'python': ['python', 'python3'],
    'javascript': ['javascript', 'js', 'ecmascript'],
    'typescript': ['typescript', 'ts'],
    'c++': ['c++', 'cpp', 'c plus plus'],
    'c#': ['c#', 'csharp', 'c sharp'],
    'docker': ['docker', 'docker容器', 'docker容器化'],
    'kubernetes': ['kubernetes', 'k8s', 'k8s容器'],
    'mysql': ['mysql', 'my sql'],
    'postgresql': ['postgresql', 'postgres', 'pg'],
    'mongodb': ['mongodb', 'mongo'],
    'aws': ['aws', 'amazon web services'],
    'azure': ['azure', '微软云'],
    'machine learning': ['机器学习', 'machine learning', 'ml'],
    'deep learning': ['深度学习', 'deep learning', 'dl'],
    'nlp': ['nlp', '自然语言处理', '自然语言'],
    'tensorflow': ['tensorflow', 'tf'],
    'pytorch': ['pytorch', 'torch'],
    'spring': ['spring', 'springboot', 'spring boot'],
    '.net': ['.net', 'dotnet', 'asp.net'],
}


def _normalize_skill(skill):
    """将技能标准化，用于模糊匹配"""
    skill_lower = skill.lower().strip()
    for standard, aliases in SKILL_ALIASES.items():
        if skill_lower in [a.lower() for a in aliases]:
            return standard
    return skill_lower


def match_resumes_to_job(job, resumes, top_n=3):
    """
    将简历与职位进行匹配，返回匹配度最高的N份简历
    返回中包含每个维度的独立分数，用于前端雷达图
    """
    results = []
    for resume in resumes:
        scores, reasons, dimension_scores = _calculate_match(job, resume)
        total = sum(s * w for s, w in scores)
        results.append({
            'resume': resume,
            'score': round(total, 1),
            'dimension_scores': dimension_scores,
            'reasons': reasons,
            'score_level': _get_score_level(total),
        })

    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:top_n]


def _calculate_match(job, resume):
    """
    计算单个简历与职位的匹配度
    权重: 学历20% 技能35% 经验20% 年龄10% 关键词15%
    """
    reasons = []
    dimension_scores = {}

    edu_score, edu_reason = _match_education(job, resume)
    dimension_scores['education'] = round(edu_score, 1)
    if edu_reason:
        reasons.append(edu_reason)

    skill_score, skill_reason = _match_skills(job, resume)
    dimension_scores['skills'] = round(skill_score, 1)
    if skill_reason:
        reasons.append(skill_reason)

    exp_score, exp_reason = _match_experience(job, resume)
    dimension_scores['experience'] = round(exp_score, 1)
    if exp_reason:
        reasons.append(exp_reason)

    age_score, age_reason = _match_age(job, resume)
    dimension_scores['age'] = round(age_score, 1)
    if age_reason:
        reasons.append(age_reason)

    text_score, text_reason = _match_keywords(job, resume)
    dimension_scores['text'] = round(text_score, 1)
    if text_reason:
        reasons.append(text_reason)

    # 加权合并
    weights = [0.20, 0.35, 0.20, 0.10, 0.15]
    scores = [edu_score, skill_score, exp_score, age_score, text_score]
    total_score = sum(s * w for s, w in zip(scores, weights))

    return list(zip(scores, weights)), reasons, dimension_scores


def _match_education(job, resume):
    job_edu = job.get('education_required', '')
    resume_edu = resume.get('education', '')
    if not job_edu:
        return 100, None
    if not resume_edu:
        return 30, {'icon': 'warning', 'text': f'学历信息缺失，岗位要求{job_edu}'}
    job_level = get_education_level(job_edu)
    resume_level = get_education_level(resume_edu)
    if resume_level >= job_level:
        if resume_level == job_level:
            return 100, {'icon': 'success', 'text': f'学历满足：{resume_edu}'}
        else:
            return 100, {'icon': 'success', 'text': f'学历优秀：{resume_edu}，高于要求的{job_edu}'}
    else:
        diff = job_level - resume_level
        score = max(0, 100 - diff * 25)
        return score, {'icon': 'danger', 'text': f'学历不符：{resume_edu}，岗位要求{job_edu}'}


def _match_skills(job, resume):
    job_skills_str = job.get('skills_required', '')
    resume_skills_str = resume.get('skills', '')

    if not job_skills_str:
        return 100, None

    # 优先从 parsed_json 读取技能列表
    parsed = _get_parsed_data(resume)
    if parsed and parsed.get('skills'):
        resume_skills_raw = set(parsed['skills'])
    else:
        resume_skills_raw = set(s.strip() for s in re.split(r'[,，、\s]+', resume_skills_str) if s.strip())

    # 解析职位技能
    job_skills_raw = set(s.strip() for s in re.split(r'[,，、\s]+', job_skills_str) if s.strip())

    # 从简历内容中补充搜索技能
    content = resume.get('content_text', '').lower()
    for skill in list(job_skills_raw):
        if skill.lower() in content:
            resume_skills_raw.add(skill)

    # 标准化
    job_skills = {_normalize_skill(s) for s in job_skills_raw}
    resume_skills = set()
    for s in resume_skills_raw:
        resume_skills.add(_normalize_skill(s))

    # 模糊匹配：检查简历内容是否包含技能别名
    for standard_skill, aliases in SKILL_ALIASES.items():
        for alias in aliases:
            if alias in content:
                resume_skills.add(standard_skill)
                break

    if not job_skills:
        return 100, None

    matched = job_skills & resume_skills
    missing = job_skills - resume_skills

    ratio = len(matched) / len(job_skills)
    score = ratio * 100

    parts = []
    if matched:
        matched_names = sorted(matched)
        # 还原为原始名称
        display_matched = []
        for m in matched_names:
            for raw in job_skills_raw:
                if _normalize_skill(raw) == m:
                    display_matched.append(raw)
                    break
            else:
                display_matched.append(m)
        parts.append(f"掌握{'、'.join(display_matched[:5])}")
    if missing:
        display_missing = []
        for m in sorted(missing):
            for raw in job_skills_raw:
                if _normalize_skill(raw) == m:
                    display_missing.append(raw)
                    break
            else:
                display_missing.append(m)
        parts.append(f"缺少{'、'.join(display_missing[:5])}")

    icon = 'success' if ratio >= 0.7 else ('warning' if ratio >= 0.4 else 'danger')
    return score, {'icon': icon, 'text': f'技能匹配 {len(matched)}/{len(job_skills)}（{score:.0f}%）。{"；".join(parts)}'}


def _match_experience(job, resume):
    job_exp = job.get('experience_required', 0)
    resume_exp = resume.get('experience_years', 0)
    if not job_exp or job_exp == 0:
        return 100, None
    if resume_exp >= job_exp:
        return 100, {'icon': 'success', 'text': f'经验满足：{resume_exp}年 ≥ {job_exp}年'}
    else:
        ratio = resume_exp / job_exp
        return ratio * 100, {'icon': 'warning', 'text': f'经验不足：{resume_exp}年，要求{job_exp}年'}


def _match_age(job, resume):
    age_min = job.get('age_min', 0)
    age_max = job.get('age_max', 0)
    age = resume.get('age', 0)
    if (age_min == 0 and age_max == 0) or age == 0:
        return 100, None
    if age_min > 0 and age_max > 0:
        if age_min <= age <= age_max:
            return 100, {'icon': 'success', 'text': f'年龄合适：{age}岁'}
        elif age < age_min:
            return max(0, 100 - (age_min - age) * 10), {'icon': 'warning', 'text': f'年龄偏小：{age}岁（要求{age_min}-{age_max}）'}
        else:
            return max(0, 100 - (age - age_max) * 10), {'icon': 'warning', 'text': f'年龄偏大：{age}岁（要求{age_min}-{age_max}）'}
    elif age_min > 0:
        if age >= age_min:
            return 100, {'icon': 'success', 'text': f'年龄合适：{age}岁 ≥ {age_min}'}
        return 50, {'icon': 'warning', 'text': f'年龄不够：{age}岁 < {age_min}'}
    elif age_max > 0:
        if age <= age_max:
            return 100, {'icon': 'success', 'text': f'年龄合适：{age}岁 ≤ {age_max}'}
        return 50, {'icon': 'warning', 'text': f'年龄超限：{age}岁 > {age_max}'}
    return 100, None


def _match_keywords(job, resume):
    job_text = f"{job.get('title', '')} {job.get('description', '')} {job.get('requirements', '')} {job.get('skills_required', '')}"
    resume_text = f"{resume.get('content_text', '')} {resume.get('skills', '')}"
    if not job_text.strip() or not resume_text.strip():
        return 50, {'icon': 'warning', 'text': '内容信息不足，无法完整评估文本匹配'}
    try:
        import jieba
        job_words = set(jieba.cut(job_text))
        resume_words = set(jieba.cut(resume_text))
    except Exception:
        job_words = set(job_text)
        resume_words = set(resume_text)
    stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
                  '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
                  '自己', '这', '他', '她', '它', '们', '那', '些', '所', '为', '所以', '因为',
                  '但是', '然而', '虽然', '如果', '可以', '能够', '需要', '应该', ' ', '\n', '\t'}
    job_words = {w for w in job_words if len(w) >= 2 and w not in stop_words}
    resume_words = {w for w in resume_words if len(w) >= 2 and w not in stop_words}
    if not job_words:
        return 50, None
    intersection = job_words & resume_words
    union = job_words | resume_words
    if len(union) == 0:
        return 50, None
    similarity = len(intersection) / len(union)
    score = min(100, similarity * 100 * 3)
    icon = 'success' if score >= 60 else ('warning' if score >= 30 else 'danger')
    return score, {'icon': icon, 'text': f'内容相关性{'高' if score>=60 else '一般' if score>=30 else '低'}（文本相似度 {similarity*100:.0f}%）'}


def _get_score_level(score):
    if score >= 80: return 'high'
    elif score >= 60: return 'medium'
    else: return 'low'
