import numpy as np
from langchain_core.tools import tool
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from sqlalchemy import select

from core.config import settings
from db.database import AsyncSessionLocal
from db.models import Policy

_CACHED_DOCS = []
_EMBEDDINGS_CACHE = None
_embeddings_model = None


def _get_embeddings_model():
    global _embeddings_model
    if _embeddings_model is None:
        _embeddings_model = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=settings.GOOGLE_API_KEY
        )
    return _embeddings_model


async def _initialize_embeddings_from_db():
    """Loads policies from PostgreSQL DB and computes embeddings cache."""
    global _EMBEDDINGS_CACHE, _CACHED_DOCS

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Policy))
        policies = result.scalars().all()

        if not policies:
            return False

        _CACHED_DOCS = [
            {"title": p.title, "content": p.content} for p in policies
        ]

        doc_texts = [f"{p['title']}: {p['content']}" for p in _CACHED_DOCS]
        embeddings_model = _get_embeddings_model()
        doc_vectors = embeddings_model.embed_documents(doc_texts)
        _EMBEDDINGS_CACHE = np.array(doc_vectors)
        return True


def _cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b, axis=1))


@tool
async def lookup_policy(query: str) -> str:
    """
    Search the store policies knowledge base from the database for information regarding 
    returns, refunds, shipping, cancellations, warranties, or customer support guidelines.
    
    Args:
        query: The search term or user question about store policies.
    """
    try:
        if _EMBEDDINGS_CACHE is None or len(_CACHED_DOCS) == 0:
            success = await _initialize_embeddings_from_db()
            if not success:
                return "No store policies found in the database."

        embeddings_model = _get_embeddings_model()
        query_vector = np.array(embeddings_model.embed_query(query))

        similarities = _cosine_similarity(query_vector, _EMBEDDINGS_CACHE)
        top_index = int(np.argmax(similarities))

        matched_doc = _CACHED_DOCS[top_index]
        return f"Policy: {matched_doc['title']}\nDetails: {matched_doc['content']}"

    except Exception as e:
        # Fallback database keyword search
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Policy))
            policies = result.scalars().all()
            query_lower = query.lower()
            
            for doc in policies:
                if any(word in doc.content.lower() or word in doc.title.lower() for word in query_lower.split()):
                    return f"Policy: {doc.title}\nDetails: {doc.content}"
                    
        return "No relevant policy found for your query. Please contact customer support directly."