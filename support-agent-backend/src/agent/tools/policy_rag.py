import numpy as np
from langchain_core.tools import tool
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from sqlalchemy import select

from core.config import settings
from core.redis_cache import (
    get_cached_docs,
    get_cached_embeddings,
    set_cached_docs,
    set_cached_embeddings,
)
from db.database import AsyncSessionLocal
from db.models import Policy

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
    """Fetch policies from DB and cache docs + embeddings in Redis."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Policy))
        policies = result.scalars().all()

        if not policies:
            return False, None, None

        docs = [
            {"title": p.title, "content": p.content} for p in policies
        ]

        await set_cached_docs(docs, ttl=3600)

        # Generate and cache embeddings in Redis
        doc_texts = [f"{doc['title']}: {doc['content']}" for doc in docs]
        embeddings_model = _get_embeddings_model()
        doc_vectors = embeddings_model.embed_documents(doc_texts)
        embeddings_array = np.array(doc_vectors)
        await set_cached_embeddings(embeddings_array, ttl=3600)

        return True, docs, embeddings_array


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
        cached_docs = await get_cached_docs()
        cached_embeddings = await get_cached_embeddings()

        # If cache miss, initialize from database
        if cached_docs is None or cached_embeddings is None:
            success, docs, embeddings = await _initialize_embeddings_from_db()
            if not success:
                return "No store policies found in the database."
            cached_docs = docs
            cached_embeddings = embeddings

        embeddings_model = _get_embeddings_model()
        query_vector = np.array(embeddings_model.embed_query(query))

        similarities = _cosine_similarity(query_vector, cached_embeddings)
        top_index = int(np.argmax(similarities))

        matched_doc = cached_docs[top_index]
        return f"Policy: {matched_doc['title']}\nDetails: {matched_doc['content']}"

    except Exception as e:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Policy))
            policies = result.scalars().all()
            query_lower = query.lower()
            
            for doc in policies:
                if any(word in doc.content.lower() or word in doc.title.lower() for word in query_lower.split()):
                    return f"Policy: {doc.title}\nDetails: {doc.content}"
                    
        return "No relevant policy found for your query. Please contact customer support directly."