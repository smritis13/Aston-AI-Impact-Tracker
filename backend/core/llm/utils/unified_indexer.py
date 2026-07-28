import os
import openai
import chromadb
from django.conf import settings
from llama_index.core import Document as LlamaDocument
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from content.models import Content  # local import to avoid circular dependency

# Import your chunker
from core.llm.utils.AdvancedChunker import AdvancedChunker

class UnifiedIndexer:
    def __init__(self, index_name="combined_context", recreate=False):
        self.index_name = index_name
        self.db_path = os.path.join(settings.BASE_DIR, "chromadb")
        self.chroma_client = chromadb.PersistentClient(path=self.db_path)
        openai.api_key = settings.OPENAI_API_KEY
        self.embedding = OpenAIEmbedding(api_key=openai.api_key)
        self.chunker = AdvancedChunker(small_chunk_size=1000, small_overlap=100, group_size=5)
        if recreate:
            self.recreate_index()
        else:
            self.load_or_create_index()

    def get_chunk_documents(self, text: str, extra_info: dict) -> list[LlamaDocument]:
        """
        Uses the AdvancedChunker to generate small and summary chunks,
        converting them into LlamaDocuments with extra metadata.
        """
        chunks_data = self.chunker.hierarchical_chunking(text)
        docs = []
        # Process small chunks.
        for chunk in chunks_data["small_chunks"]:
            info = extra_info.copy()
            info.update({
                "chunk_index": chunk["chunk_index"],
                "start": chunk["start"],
                "end": chunk["end"],
                "is_summary": False
            })
            docs.append(LlamaDocument(text=chunk["text"], extra_info=info))
        # Process summary chunks.
        for summary in chunks_data["summary_chunks"]:
            info = extra_info.copy()
            group_members_str = ",".join(str(x) for x in summary["group_members"])
            info.update({
                "chunk_index": summary["chunk_index"],
                "group_members": group_members_str,
                "is_summary": True
            })
            docs.append(LlamaDocument(text=summary["text"], extra_info=info))
        return docs

    def build_index(self, documents: list[LlamaDocument]) -> VectorStoreIndex:
        """
        Builds a VectorStoreIndex from a list of LlamaDocuments.
        """
        chroma_collection = self.chroma_client.get_or_create_collection(name=self.index_name)
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        return VectorStoreIndex.from_documents(
            documents,
            storage_context=storage_context,
            embedding=self.embedding
        )

    def load_documents_from_content(self, content_queryset=None) -> list[LlamaDocument]:
        """
        Loads documents from the Content model and converts them into LlamaDocuments.
        If no queryset is provided, it loads all Content objects.
        """
        if content_queryset is None:
            content_queryset = Content.objects.all()
        docs = []
        for obj in content_queryset:
            if not obj.original_content or not obj.original_content.strip():
                continue
            extra_info = {
                "content_id": obj.id,
                "url": obj.url,
                "title": obj.title or "",
                "category": obj.category.name if obj.category else ""
            }
            docs.extend(self.get_chunk_documents(obj.original_content, extra_info))
        return docs

    def load_or_create_index(self, content_queryset=None):
        """
        Loads an existing index or creates one from the given Content objects.
        """
        try:
            chroma_collection = self.chroma_client.get_collection(name=self.index_name)
        except Exception:
            chroma_collection = self.chroma_client.create_collection(name=self.index_name)

        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        try:
            self.index = VectorStoreIndex.from_vector_store(
                vector_store=vector_store,
                storage_context=storage_context,
                embedding=self.embedding
            )

            if content_queryset is not None:
                docs = self.load_documents_from_content(content_queryset)
                # Insert new documents into the index.
                # Adjust the method name based on your llama_index API.
                self.index.insert_documents(docs)
        except ValueError:
            # No index exists yet or it’s in an old format; build a new one.
            docs = self.load_documents_from_content(content_queryset)
            self.index = self.build_index(docs)
        return self.index

    def recreate_index(self, content_queryset=None):
        """
        Deletes the current collection and rebuilds the index with all documents.
        """
        try:
            self.chroma_client.delete_collection(name=self.index_name)
        except Exception:
            pass
        # Load all documents (or use the provided queryset) and rebuild the index
        print("Rebuilding index")
        docs = self.load_documents_from_content(content_queryset)
        self.index = self.build_index(docs)
        print("Index rebuilt")
        return self.index
