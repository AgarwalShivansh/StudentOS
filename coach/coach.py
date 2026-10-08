from core.groq_client import ask_groq

def build_prompt(profile, lifelog=None, question='Give me a personalized plan for today.'):
    context={'profile':profile}
    if lifelog:
        context['lifelog']={k:v for k,v in lifelog.items() if k not in ('data','topic')}
        context['weak_topics']=lifelog.get('topic',[]).head(5).to_dict('records') if hasattr(lifelog.get('topic'), 'head') else []
    return [
      {'role':'system','content':'You are StudentOS AI, a precise academic and career coach. Use only the supplied student context. Do not invent grades, achievements, activity, or career facts. Give concrete actions and explain why they are recommended.'},
      {'role':'user','content':f'Student context: {context}\n\nQuestion: {question}'}
    ]

def coach(profile,lifelog,question):
    return ask_groq(build_prompt(profile,lifelog,question),temperature=0.25,max_tokens=1800)
