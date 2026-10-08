import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

SKILLS=['python','c++','java','sql','pandas','numpy','scikit-learn','tensorflow','pytorch','machine learning','deep learning','nlp','computer vision','llm','rag','langchain','streamlit','fastapi','docker','git','aws','azure','power bi','tableau','excel','statistics','data structures','algorithms','react','node.js','mongodb','postgresql','faiss','chromadb']

def extract_skills(text):
    low=text.lower()
    return sorted({s for s in SKILLS if re.search(r'(?<![a-z0-9])'+re.escape(s)+r'(?![a-z0-9])',low)})

def match(resume,jd):
    vector=TfidfVectorizer(ngram_range=(1,2),stop_words='english')
    mat=vector.fit_transform([resume,jd])
    similarity=float(cosine_similarity(mat[0:1],mat[1:2])[0][0]*100)
    rs=set(extract_skills(resume)); js=set(extract_skills(jd))
    covered=sorted(rs&js); missing=sorted(js-rs)
    skill_score=100 if not js else len(covered)/len(js)*100
    final=0.55*similarity+0.45*skill_score
    return {'similarity':similarity,'skill_score':skill_score,'final':final,'covered':covered,'missing':missing}
