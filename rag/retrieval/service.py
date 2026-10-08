from __future__ import annotations
import json,math,re
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
class RAGService:
    def __init__(self,index_path='rag/index/index.json'):
        self.path=Path(index_path); self.data=json.loads(self.path.read_text()) if self.path.exists() else None
        if not self.data: raise RuntimeError('RAG index missing. Run: python -m rag.ingestion.build_index')
        self.records=self.data['records']
        self.vectorizer=TfidfVectorizer(stop_words='english',ngram_range=(1,2),vocabulary=self.data['vocabulary'])
        self.vectorizer.idf_=self.data['idf']
        self.vectorizer._tfidf._idf_diag=None
        # fit a local compatible vocabulary on corpus for robust scoring
        self.vectorizer=TfidfVectorizer(stop_words='english',ngram_range=(1,2),vocabulary=self.data['vocabulary'])
        self.matrix=self.vectorizer.fit_transform([r['text'] for r in self.records])
    def retrieve(self,query,top_k=4):
        q=self.vectorizer.transform([query]); scores=cosine_similarity(q,self.matrix)[0]
        ranked=sorted(enumerate(scores),key=lambda x:x[1],reverse=True)
        hits=[]
        for i,s in ranked[:top_k]:
            if s<=0: continue
            r=self.records[i].copy(); r['score']=round(float(s),4); hits.append(r)
        return hits
