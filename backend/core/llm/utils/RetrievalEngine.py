import os
import openai
import chromadb
from django.conf import settings

class RetrievalEngine:
    """
    RetrievalEngine implements a hybrid search strategy that combines:
      • Dense vector search using embeddings.
      • Keyword-based search (BM25) via ChromaDB.
      • Multi-query expansion.
    • Re-ranking of retrieved documents using gpt-5.4-mini.
      • Top-K adjustments to retrieve a broader set of relevant documents.
    """
    def __init__(self, index_name="combined_context", embedding=None, client=None):
        """
        Args:
            index_name (str): Name of the ChromaDB collection.
            embedding: An embedding instance (e.g., from OpenAIEmbedding).
            client: A ChromaDB client instance. If not provided, a new one is created.
        """
        self.index_name = index_name
        self.db_path = os.path.join(settings.BASE_DIR, "chromadb")
        self.client = client if client else chromadb.PersistentClient(path=self.db_path)
        self.embedding = embedding
        openai.api_key = settings.OPENAI_API_KEY

    def expand_query(self, query: str) -> list[str]:
        """
        Uses OpenAI's GPT model to generate query variations.
        """
        prompt = (
            f"Generate three distinct search query variations for the following query "
            f"that would help in retrieving a wider range of relevant results:\n\n"
            f"Query: \"{query}\"\n\n"
            "Variations:"
        )
        response = openai.chat.completions.create(
            model="gpt-5.4-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            n=1,
            temperature=0.7
        )
        
        # Get the response text from the message content
        response_text = response.choices[0].message.content.strip()
        
        # Assuming each variation is on a new line:
        variations = response_text.split("\n")
        # Clean up any numbering or extra characters
        return [var.strip(" -0123456789.") for var in variations if var.strip()]

    def deduplicate_results(self, results: list[dict]) -> list[dict]:
        """
        Deduplicates retrieved documents based on their text.
        
        Args:
            results (list[dict]): List of result dictionaries.
            
        Returns:
            list[dict]: Deduplicated list of results.
        """
        seen = set()
        unique = []
        for res in results:
            text = res["text"]
            # If the text is a list, join it into a single string.
            text_key = " ".join(text) if isinstance(text, list) else text
            if text_key not in seen:
                unique.append(res)
                seen.add(text_key)
        return unique

    def rerank_documents(self, query: str, documents: list[dict]) -> list[dict]:
        prompt = f"Rank the following documents in order of relevance to the query.\n\nQuery: {query}\n\nDocuments:\n"
        for i, doc in enumerate(documents):
            text_val = doc["text"]
            # If text_val is a list, join it into a single string.
            if isinstance(text_val, list):
                text_val = " ".join(text_val)
            excerpt = text_val[:200].replace("\n", " ")
            prompt += f"{i+1}. {excerpt}...\n"
        prompt += "\nProvide the ranking as a comma-separated list of document numbers (highest relevance first)."

        try:
            response = openai.ChatCompletion.create(
                model="gpt-5.4-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0.0
            )
            ranking_text = response.choices[0].message.content.strip()
            ranking = [int(x.strip()) for x in ranking_text.split(",")]
        except Exception:
            ranking = list(range(1, len(documents) + 1))
        
        # Reorder documents based on ranking (1-indexed to 0-indexed).
        reranked = [documents[i - 1] for i in ranking if 0 < i <= len(documents)]
        return reranked


    def retrieve(self, query: str, k: int = 10) -> dict:
        """
        Retrieves documents using the following steps:
        1. Multi-query expansion.
        2. Hybrid search using both embeddings and raw query text.
        3. Deduplication of results.
        4. Re-ranking using a re-ranking model.
        5. Selection of the top-K documents.
        
        Args:
            query (str): The query string.
            k (int): Number of top documents to retrieve.
        
        Returns:
            dict: Contains:
                - combined_context: Combined text of top documents.
                - results: List of top document dictionaries.
                - metadatas: List of metadata dictionaries (e.g., URLs, titles).
        """
        sub_queries = self.expand_query(query)
        all_results = []
        # Get the ChromaDB collection.
        collection = self.client.get_collection(name=self.index_name)
        
        for sub in sub_queries:
            query_embedding = self.embedding.get_text_embedding(sub)
            results = collection.query(
                query_embeddings=[query_embedding],
                query_texts=[sub],
                n_results=k
            )
            # Assume results contain "documents" and "metadatas".
            for text, metadata in zip(results.get("documents", []), results.get("metadatas", [])):
                all_results.append({"text": text, "extra_info": metadata})
        
        unique_results = self.deduplicate_results(all_results)
        reranked_results = self.rerank_documents(query, unique_results)
        top_results = reranked_results[:k]
        
        # Ensure each document text is a string.
        combined_context = "\n\n".join(
            " ".join(doc["text"]) if isinstance(doc["text"], list) else doc["text"]
            for doc in top_results
        )
        
        # Extract metadata from the top results for further reference aggregation.
        metadatas = [doc["extra_info"] for doc in top_results]
        
        return {"combined_context": combined_context, "results": top_results, "metadatas": metadatas}
