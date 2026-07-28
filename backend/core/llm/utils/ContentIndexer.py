import os
import openai
import chromadb
from django.conf import settings
from content.models import Content
from llama_index.embeddings.openai import OpenAIEmbedding
from core.llm.utils.unified_indexer import UnifiedIndexer

class ContentIndexer:
    def __init__(self):
        # Set the OpenAI API key
        openai.api_key = settings.OPENAI_API_KEY
        # Instantiate our unified indexer – this gives us access to the Chroma client,
        # embedding function, and our chunking method.
        self.unified_indexer = UnifiedIndexer(index_name="combined_context", recreate=False)
        self.embedding = self.unified_indexer.embedding

    def index_content(self, content: Content):
        """
        Uses the unified indexer to convert the Content object's original_content
        into chunk documents, adds them into the current index (the underlying Chroma collection),
        and refreshes the in-memory index.
        Optionally, it can delete the file after indexing.
        """
        # Create chunk documents using the UnifiedIndexer method.
        docs = self.unified_indexer.get_chunk_documents(
            content.original_content,
            {
                "content_id": content.id,
                "url": content.url,
                "title": content.title or "",
                "category": content.category.name if content.category else ""
            }
        )
        # Prepare lists for adding to the collection.
        documents = []
        metadatas = []
        ids = []
        embeddings = []
        for i, doc in enumerate(docs):
            documents.append(doc.text)
            metadatas.append(doc.extra_info)
            # Build a unique ID using content id, chunk_index, and loop index
            chunk_index = doc.extra_info.get("chunk_index", i)
            unique_id = f"{content.id}_{chunk_index}_{i}"
            ids.append(unique_id)
            # Generate embedding for this chunk
            emb = self.embedding.get_text_embedding(doc.text)
            embeddings.append(emb)
        
        # Get the underlying Chroma collection from our unified indexer.
        collection = self.unified_indexer.chroma_client.get_or_create_collection(self.unified_indexer.index_name)
        # Add new documents to the collection.
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
            embeddings=embeddings
        )
        # Refresh or rebuild the in-memory index so that queries include the new content.
        self.unified_indexer.load_or_create_index()

        # Optionally, delete the file associated with the content if needed.
        # For example, if your Content model has a file_path attribute:
        # if hasattr(content, 'file_path') and os.path.exists(content.file_path):
        #     os.remove(content.file_path)
