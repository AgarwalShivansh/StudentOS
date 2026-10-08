def career_readiness(profile, resume_analysis=None, goals=None, lifelog=None):
    resume=resume_analysis or {}
    skills=len(resume.get('skills',[]))
    resume_score=float(resume.get('score',0))
    project_score=85 if resume.get('sections',{}).get('projects') else 35
    academic=75 if float(profile.get('cgpa',0) or 0) >= 7 else 55
    goal_progress=0
    if goals:
        vals=[]
        for g in goals:
            t=float(g.get('target') or 0); c=float(g.get('current') or 0)
            if t: vals.append(min(100,c/t*100))
        goal_progress=sum(vals)/len(vals) if vals else 0
    dsa=goal_progress if any('dsa' in (g.get('category') or '').lower() or 'leetcode' in (g.get('title') or '').lower() for g in (goals or [])) else 50
    technical=min(100,skills*8)
    overall=0.28*resume_score+0.22*project_score+0.18*academic+0.17*technical+0.15*dsa
    gaps=[]
    if technical<70: gaps.append('Expand role-relevant technical skills.')
    if project_score<70: gaps.append('Add stronger projects with measurable outcomes.')
    if dsa<65: gaps.append('Increase DSA/problem-solving practice.')
    if resume_score<75: gaps.append('Improve resume structure and role-specific tailoring.')
    return {'overall':overall,'resume':resume_score,'projects':project_score,'academic':academic,'technical':technical,'dsa':dsa,'gaps':gaps}
