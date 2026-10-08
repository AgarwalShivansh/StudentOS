import io, re
import numpy as np
from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None

class StudyRAG:
    def __init__(self):
        self.chunks=[]
        self.vectorizer=None
        self.tfidf=None
        self.embedder=None
        self.embeddings=None

    def ingest(self, files):
        chunks=[]
        for file in files:
            reader=PdfReader(io.BytesIO(file.getvalue()))
            for page_no,page in enumerate(reader.pages,1):
                text=page.extract_text() or ''
                text=re.sub(r'\s+',' ',text).strip()
                if not text: continue
                words=text.split()
                size, overlap=220, 40
                for start in range(0,len(words),size-overlap):
                    part=' '.join(words[start:start+size]).strip()
                    if len(part)>=80:
                        chunks.append({'text':part,'source':file.name,'page':page_no})
        self.chunks=chunks
        if not chunks: raise ValueError('No extractable text was found. This PDF may be scanned/image-only and needs OCR.')
        texts=[c['text'] for c in chunks]
        self.vectorizer=TfidfVectorizer(ngram_range=(1,2),sublinear_tf=True,max_features=30000,stop_words='english')
        self.tfidf=self.vectorizer.fit_transform(texts)
        if SentenceTransformer:
            try:
                self.embedder=SentenceTransformer('all-MiniLM-L6-v2')
                self.embeddings=self.embedder.encode(texts,normalize_embeddings=True,show_progress_bar=False)
            except Exception:
                self.embedder=None
        return len(chunks)

    def search(self, query, k=5):
        if not self.chunks: return []
        q_tfidf=self.vectorizer.transform([query])
        sparse=cosine_similarity(q_tfidf,self.tfidf)[0]
        if self.embedder is not None:
            q=self.embedder.encode([query],normalize_embeddings=True)
            dense=(self.embeddings @ q[0])
            scores=0.35*sparse+0.65*dense
        else:
            scores=sparse
        idx=np.argsort(scores)[::-1]
        results=[]; seen=set()
        for i in idx:
            c=self.chunks[int(i)]
            key=(c['source'],c['page'])
            if key in seen: continue
            seen.add(key)
            results.append({**c,'score':float(scores[i])})
            if len(results)>=k: break
        return results
