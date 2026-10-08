import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

SKILLS=['python','c++','java','sql','pandas','numpy','scikit-learn','tensorflow','pytorch','machine learning','deep learning','nlp','computer vision','llm','rag','langchain','streamlit','fastapi','docker','git','github','aws','azure','power bi','tableau','excel','statistics','data structures','algorithms','react','node.js','mongodb','postgresql','faiss','chromadb','system design','communication','natural language processing','generative ai']

def extract_skills(text):
    low=text.lower()
    return sorted({s for s in SKILLS if re.search(r'(?<![a-z0-9])'+re.escape(s)+r'(?![a-z0-9])',low)})

def analyze_resume(resume):
    skills=extract_skills(resume)
    sections={
        'education': bool(re.search(r'education|b\.tech|bachelor|degree|university|college',resume,re.I)),
        'projects': bool(re.search(r'projects?|developed|built|implemented',resume,re.I)),
        'experience': bool(re.search(r'experience|internship|worked|employment',resume,re.I)),
        'contact': bool(re.search(r'@|linkedin|github|phone|mobile',resume,re.I)),
        'summary': bool(re.search(r'summary|objective|profile',resume,re.I)),
    }
    section_score=sum(sections.values())/len(sections)*100
    skill_score=min(100,len(skills)*7)
    length_score=100 if 250 <= len(resume.split()) <= 900 else 70 if len(resume.split()) >= 150 else 45
    score=0.45*section_score+0.35*skill_score+0.20*length_score
    suggestions=[]
    if not sections['summary']: suggestions.append('Add a concise professional summary tailored to the target role.')
    if not sections['projects']: suggestions.append('Add 2–4 measurable technical projects with outcomes and technologies.')
    if not sections['experience']: suggestions.append('If applicable, add internships, leadership, volunteering, or relevant experience.')
    if not sections['contact']: suggestions.append('Add professional contact links such as GitHub and LinkedIn.')
    if len(resume.split()) < 250: suggestions.append('The resume is quite short; add quantified project/experience bullets where relevant.')
    return {'score':score,'skills':skills,'sections':sections,'suggestions':suggestions}

def match(resume,jd):
    vector=TfidfVectorizer(ngram_range=(1,2),stop_words='english')
    mat=vector.fit_transform([resume,jd])
    similarity=float(cosine_similarity(mat[0:1],mat[1:2])[0][0]*100)
    rs=set(extract_skills(resume)); js=set(extract_skills(jd))
    covered=sorted(rs&js); missing=sorted(js-rs)
    skill_score=100 if not js else len(covered)/len(js)*100
    final=0.55*similarity+0.45*skill_score
    return {'similarity':similarity,'skill_score':skill_score,'final':final,'covered':covered,'missing':missing}
