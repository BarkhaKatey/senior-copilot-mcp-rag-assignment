from __future__ import annotations
import json,re
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
ROOT=Path(__file__).resolve().parents[2]; DOCS=ROOT/'rag/documents'; OUT=ROOT/'rag/index'; OUT.mkdir(exist_ok=True)

def chunks(text,max_chars=850):
    sections=re.split(r'\n(?=## )',text.strip())
    out=[]
    for sec in sections:
        if len(sec)<=max_chars: out.append(sec)
        else:
            words=sec.split(); cur=[]; n=0
            for w in words:
                cur.append(w); n+=len(w)+1
                if n>=max_chars: out.append(' '.join(cur)); cur=[]; n=0
            if cur: out.append(' '.join(cur))
    return [x.strip() for x in out if x.strip()]

def main():
    records=[]
    for p in sorted(DOCS.glob('*.md')):
        text=p.read_text(encoding='utf-8')
        for i,c in enumerate(chunks(text)):
            records.append({'chunk_id':f'{p.stem}-{i+1}','document_id':p.stem,'source':p.name,'section':c.splitlines()[0][:120],'text':c,'asset_scope':'Boiler Feed Pump 101' if 'bfp101' in p.stem or 'Boiler Feed Pump 101' in text else 'general'})
    vectorizer=TfidfVectorizer(stop_words='english',ngram_range=(1,2))
    matrix=vectorizer.fit_transform([r['text'] for r in records])
    payload={'records':records,'vocabulary':vectorizer.vocabulary_,'idf':vectorizer.idf_.tolist(),'shape':list(matrix.shape)}
    (OUT/'index.json').write_text(json.dumps(payload,indent=2),encoding='utf-8')
    print(f'Indexed {len(records)} chunks into {OUT}/index.json')
if __name__=='__main__': main()
