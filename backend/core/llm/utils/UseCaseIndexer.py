import os
import openai
import chromadb
from django.conf import settings
from content.models import UseCase, UseCaseTheme
from llama_index.embeddings.openai import OpenAIEmbedding
from core.llm.utils.unified_indexer import UnifiedIndexer

class UseCaseIndexer:
    def __init__(self, theme_name: str = None):
        # Set the OpenAI API key
        openai.api_key = settings.OPENAI_API_KEY
        
        # Create index name based on theme name
        self.index_name = f"theme_{theme_name.lower().replace(' ', '_')}" if theme_name else "all_use_cases"
        
        # Instantiate our unified indexer with the theme-specific index name
        self.unified_indexer = UnifiedIndexer(index_name=self.index_name, recreate=False)
        self.embedding = self.unified_indexer.embedding

    def index_use_case(self, use_case: UseCase):
        """
        Indexes a single use case into the theme's collection.
        """
        # Create a document from the use case
        use_case_text = f"""
        Use Case: {use_case.use_case_name}
        Company: {use_case.company or 'N/A'}
        Industry: {use_case.industry or 'N/A'}
        Type: {use_case.use_case_type or 'N/A'}
        Description: {use_case.use_case_description}
        Tools: {use_case.tools or 'N/A'}
        Performance Impact: {use_case.performance_impact or 'N/A'}
        Date: {use_case.use_case_date or 'N/A'}
        Source: {use_case.source or 'N/A'}
        """

        # Create chunk documents using the UnifiedIndexer method
        docs = self.unified_indexer.get_chunk_documents(
            use_case_text,
            {
                "use_case_id": use_case.id,
                "theme_id": use_case.theme.id if use_case.theme else None,
                "theme_name": use_case.theme.title if use_case.theme else None,
                "company": use_case.company or "",
                "industry": use_case.industry or "",
                "use_case_type": use_case.use_case_type or "",
                "credibility_score": use_case.credibility_score,
                "relevance_score": use_case.relevance_score
            }
        )

        # Prepare lists for adding to the collection
        documents = []
        metadatas = []
        ids = []
        embeddings = []

        for i, doc in enumerate(docs):
            documents.append(doc.text)
            metadatas.append(doc.extra_info)
            # Build a unique ID using use case id, chunk_index, and loop index
            chunk_index = doc.extra_info.get("chunk_index", i)
            unique_id = f"{use_case.id}_{chunk_index}_{i}"
            ids.append(unique_id)
            # Generate embedding for this chunk
            emb = self.embedding.get_text_embedding(doc.text)
            embeddings.append(emb)

        # Get the underlying Chroma collection
        collection = self.unified_indexer.chroma_client.get_or_create_collection(self.unified_indexer.index_name)
        
        # Add new documents to the collection
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
            embeddings=embeddings
        )

        # Refresh the in-memory index
        self.unified_indexer.load_or_create_index()

    def index_theme_use_cases(self, theme: UseCaseTheme):
        """
        Indexes all use cases belonging to a specific theme.
        """
        # Get all use cases for this theme
        use_cases = UseCase.objects.filter(theme=theme)
        
        # Index each use case
        for use_case in use_cases:
            self.index_use_case(use_case)

    def add_use_case_to_index(self, use_case: UseCase):
        """
        Adds a new use case to the existing index.
        """
        self.index_use_case(use_case)

    def get_theme_index_name(self, theme: UseCaseTheme) -> str:
        """
        Returns the index name for a specific theme.
        """
        return f"theme_{theme.title.lower().replace(' ', '_')}" 