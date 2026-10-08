from rag.ingestion.build_index import main
from rag.retrieval.service import RAGService
def test_rag():
 main(); r=RAGService('rag/index/index.json'); hits=r.retrieve('Boiler Feed Pump 101 low suction pressure operating procedure',3); assert hits; assert any('procedure' in h['source'] for h in hits)
