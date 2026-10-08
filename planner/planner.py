from core.groq_client import ask_groq, get_client

def build_plan(profile, goals, lifelog=None, hours=3, days=7):
    weak=[]
    if lifelog and hasattr(lifelog.get('topic'), 'head'):
        weak=lifelog['topic'].head(5)['topic'].tolist()
    if get_client():
        prompt=f'''Create a realistic {days}-day student study plan. Student profile: {profile}. Goals: {goals}. Weak topics from activity data: {weak}. Available study time per day: {hours} hours. Do not invent facts. Return a clean day-by-day plan with subjects, durations, and one short reason for prioritization.'''
        return ask_groq([{'role':'system','content':'You are an academic planning assistant. Use only supplied context.'},{'role':'user','content':prompt}],temperature=0.2,max_tokens=2200)
    lines=[f'Study Plan — {days} days | {hours} hours/day']
    focus=weak or [g['title'] for g in goals[:5]] or ['Core academic subjects']
    for i in range(1,days+1):
        lines.append(f'\nDay {i}:')
        for item in focus[:3]: lines.append(f'- {item}: {max(30,int(hours*60/3))} minutes')
    return '\n'.join(lines)
