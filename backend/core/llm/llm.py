import os
import uuid
from django.conf import settings
from core.llm.langchain.langgraph.LangGraphChatEngine import LangGraphChatEngine
from core.llm.utils.unified_indexer import UnifiedIndexer
from core.llm.utils.RetrievalEngine import RetrievalEngine
from core.llm.utils.WebSearcher import WebSearcher
from core.llm.utils.pusher_service import PusherService

class LLM:
    def __init__(self, conversation_id: str = None, index_name="combined_context", recreate=False):
        self.index_name = index_name
        self.conversation_id = conversation_id or str(uuid.uuid4())
        self.pusher_service = PusherService()

        # Instantiate the UnifiedIndexer which handles index building, chunking, etc.
        self.unified_indexer = UnifiedIndexer(index_name=index_name, recreate=recreate)
        self.index = self.unified_indexer.index

        # Set up the query and chat engines from the index.
        self.query_engine = self.index.as_query_engine()
        self.chat_engine = self.index.as_chat_engine()

        # Use the unified indexer's Chroma client and embedding.
        self.chroma_client = self.unified_indexer.chroma_client
        self.embedding = self.unified_indexer.embedding

        # Initialize retrieval engine and web searcher as before.
        self.retrieval_engine = RetrievalEngine(
            index_name=self.index_name,
            embedding=self.embedding,
            client=self.chroma_client
        )

        self.langgraph_chat_engine = LangGraphChatEngine(conversation_id=self.conversation_id)

    def stream_thought(self, thought: str):
        """Stream a thought to the frontend."""
        self.pusher_service.stream_thought(self.conversation_id, thought)

    def query(self, prompt: str) -> str:
        response = self.query_engine.query(prompt)
        return str(response)

    def chat(self, prompt: str) -> str:
        markdown_prompt = f"Please answer the following in Markdown format:\n\n{prompt}"
        response = self.chat_engine.chat(markdown_prompt)
        return str(response)

    def retrieve_and_chat(self, query: str, k: int = 10) -> dict:
        """
        Uses the RetrievalEngine to fetch relevant context, aggregates internal references,
        then constructs a final prompt and gets a chat response.
        """
        self.stream_thought("Searching for relevant context...")
        retrieval_results = self.retrieval_engine.retrieve(query, k=k)
        static_context = retrieval_results["combined_context"]

        # we want to be able to search the usecase table here

        # If no context is found, fallback to LangGraph WebQA
        if not static_context.strip():
            self.stream_thought("No local context found. Falling back to web search...")
            return self.langgraph_chat_engine.answer(query)

        self.stream_thought("Processing retrieved context...")
        # Extract internal references as an array.
        references = self.extract_internal_references(retrieval_results)
        # Create a Markdown string of references.
        references_markdown = "\n\n".join(
            f"- **Result {i+1}:** [{ref['title']}]({ref['url']})"
            for i, ref in enumerate(references)
        )

        max_context_chars = 8000  # Adjust as needed.
        combined_context = static_context + "\n\n" + references_markdown
        if len(combined_context) > max_context_chars:
            combined_context = combined_context[:max_context_chars] + "..."

        final_prompt = (
            f"Using the following context:\n{combined_context}\n\n"
            f"Answer the query: {query}\n\n"
            f"Please provide your answer in Markdown format."
        )

        self.stream_thought("Generating response...")
        answer = self.chat(final_prompt)
        return {"answer": answer, "references": references, "conversation_id": self.conversation_id}
    
    def retrieve_and_chat_with_WebSearch(self, query: str) -> dict:
        """
        Uses OpenAI's search-enabled model to perform a web search and answer the query.
        
        This function sends the query to the OpenAI API with web search enabled,
        retrieves the generated answer (which incorporates web search results),
        and returns the answer along with any references provided by the API.
        """
        from openai import OpenAI
        
        # Initialize the OpenAI client with your API key.
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Create a chat completion request with web search options enabled.
        response = client.chat.completions.create(
            model="gpt-5-search-api",  # NOTE: verify this is still the correct search-enabled model id for your account
            web_search_options={},  # Customize search options if needed.
            messages=[
                {
                    "role": "user",
                    "content": query,
                }
            ],
        )
        # Extract the answer from the API response.
        answer = response.choices[0].message.content
        
        # Optionally extract references if the API returns them.
        # references = response.get("references", [])
        
        return {"answer": answer, "references": [], "conversation_id": self.conversation_id}

    def extract_internal_references(self, results: dict) -> list:
        """
        Extracts internal document metadata references as an array from the retrieval results.
        """
        raw_metadatas = results.get("metadatas", [])
        flattened_metadatas = []
        def flatten(metas):
            for item in metas:
                if isinstance(item, list):
                    flatten(item)
                else:
                    flattened_metadatas.append(item)
        flatten(raw_metadatas)

        references = []
        seen = set()  # To track unique references.
        for meta in flattened_metadatas:
            title = meta.get("title") or meta.get("file_name") or "Untitled"
            url = meta.get("url") or meta.get("file_url") or ""
            if meta.get("file_id"):
                file_id = meta.get("file_id")
                _, ext = os.path.splitext(title)
                file_type = ext.lower() if ext else "unknown"
                server_url = f"https://yourserver.com/documents/{file_id}/download"
                if not url:
                    url = server_url
                reference = {
                    "title": title,
                    "url": url,
                    "file_type": file_type,
                }
                key = (title, url, file_type, server_url)
            else:
                reference = {
                    "title": title,
                    "url": url or "No URL provided"
                }
                key = (title, url)
            if key not in seen:
                seen.add(key)
                references.append(reference)
        return references
