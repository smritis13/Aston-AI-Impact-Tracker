import openai
from core.llm.utils.unified_indexer import UnifiedIndexer
from content.models import Content  
from django.conf import settings

class AdvancedAugmentedResponse:
    def __init__(self, index_name="combined_context", recreate=False, content_queryset=None):
        """
        Initializes the system by loading or creating a vector index from your scraped Content.
        """
        self.indexer = UnifiedIndexer(index_name=index_name, recreate=recreate)
        self.content_queryset = content_queryset
        self.index = self.indexer.load_or_create_index(content_queryset)
        # Optionally, initialize a chat engine if needed elsewhere
        self.chat_engine = self.index.as_chat_engine()
    
    def extract_references(self, retrieved_docs: list) -> list:
        references = []
        for doc in retrieved_docs:
            ref_info = doc.node.extra_info  # Assumes extra_info contains metadata
            new_ref = {
                "title": ref_info.get("title", "Untitled"),
                "url": ref_info.get("url", ""),
                "content_id": ref_info.get("content_id", None)
            }
            
            # Determine uniqueness: use content_id if available, otherwise url.
            if new_ref["content_id"]:
                if any(ref.get("content_id") == new_ref["content_id"] for ref in references):
                    continue
            elif new_ref["url"]:
                if any(ref.get("url") == new_ref["url"] for ref in references):
                    continue
            
            references.append(new_ref)
            
        return references

    def answer_question(self, question: str, top_k: int = 5) -> dict:                           
        """
        Answers a question by:
          1. Retrieving top-k document chunks relevant to the question.
          2. Using a chain-of-thought prompt (via chat API) to extract key points.
          3. Generating a comprehensive answer that integrates the key points.
        
        Args:
            question (str): The question to answer.
            top_k (int): Number of top matching document chunks to retrieve.

        Returns:
            dict: Contains 'answer', 'key_points' (for debugging/transparency), and 'references'.
        """
        # Step 1: Retrieve relevant document chunks using a query engine.
        query_engine = self.index.as_query_engine(similarity_top_k=top_k)
        result = query_engine.query(question)
        # Assuming each retrieved source node has a 'node' attribute with text and extra_info.
        retrieved_docs = result.source_nodes
        
        # Build a context block from the retrieved documents.
        context = "\n\n".join([doc.node.text for doc in retrieved_docs])
        
        # Step 2: Extract key points using a chat completion call.
        extraction_prompt = (
            f"Read the following context extracted from several web articles and provide a detailed, step-by-step "
            f"list of key points that are relevant to answering the question.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {question}\n\n"
            f"Step-by-Step Key Points:"
        )
        extraction_response = openai.chat.completions.create(
            model="gpt-5.4-mini",
            messages=[{"role": "user", "content": extraction_prompt}],
            max_tokens=150,      # adjust as needed
            temperature=0.5      # adjust as needed
        )
        key_points = extraction_response.choices[0].message.content.strip()
        
        # Step 3: Generate the final answer using the extracted key points.
        answer_prompt = (
            f"Using the key points provided below, generate a comprehensive and detailed answer to the following question. "
            f"Ensure that each key point is addressed and integrated into a cohesive explanation.\n\n"
            f"give the Final Answer and Key Points in markdown format. do not add Final Answer: as a label\n\n"
            f"Key Points:\n{key_points}\n\n"
            f"Question: {question}"
        )
        answer_response = openai.chat.completions.create(
            model="gpt-5.4",
            messages=[{"role": "user", "content": answer_prompt}],
            max_tokens=300,      # adjust as needed
            temperature=0.7      # adjust as needed
        )
        final_answer = answer_response.choices[0].message.content.strip()
        
        # Step 4: Collect references from the retrieved documents.
        references = self.extract_references(retrieved_docs)
        
        return {
            "answer": final_answer,
            "key_points": key_points,  # Useful for debugging and transparency
            "references": references
        }