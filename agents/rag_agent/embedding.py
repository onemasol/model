from sentence_transformers import SentenceTransformer
from langchain.embeddings.base import Embeddings

class KoSBERTEmbeddings(Embeddings):
    def __init__(self, model_name='jhgan/ko-sbert-nli'):
        self.model = SentenceTransformer(model_name)
     
    def embed_documents(self, texts):
        return self.model.encode(texts, convert_to_numpy=True).tolist()
     
    def embed_query(self, text):
        return self.model.encode([text], convert_to_numpy=True)[0].tolist()