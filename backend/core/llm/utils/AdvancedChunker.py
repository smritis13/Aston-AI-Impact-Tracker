class AdvancedChunker:
    """
    AdvancedChunker implements an improved text chunking strategy with:
      • Overlapping small chunks
      • Hierarchical grouping and summarization
      • Windowing for context retrieval
    """
    def __init__(
        self,
        small_chunk_size: int = 1000,
        small_overlap: int = 100,
        group_size: int = 5,
        summarizer: callable = None
    ):
        """
        Initialize the chunker.

        Args:
            small_chunk_size (int): Maximum size for small chunks.
            small_overlap (int): Overlap size between consecutive chunks.
            group_size (int): Number of small chunks per hierarchical group.
            summarizer (callable, optional): A function that takes text as input
                and returns a summary. If None, a fallback summary is generated.
        """
        self.small_chunk_size = small_chunk_size
        self.small_overlap = small_overlap
        self.group_size = group_size
        self.summarizer = summarizer

    def chunk_text(self, text: str) -> list[dict]:
        """
        Splits text into overlapping small chunks.
        
        Each chunk is returned as a dictionary containing:
            - text: the chunk text
            - chunk_index: a unique index
            - start: starting character index in the original text
            - end: ending character index

        Args:
            text (str): The input text to chunk.
        
        Returns:
            list[dict]: List of small chunk dictionaries.
        """
        chunks = []
        start = 0
        text_length = len(text)
        chunk_index = 0

        while start < text_length:
            end = min(start + self.small_chunk_size, text_length)
            chunk = text[start:end].strip()
            if chunk:
                chunks.append({
                    "text": chunk,
                    "chunk_index": chunk_index,
                    "start": start,
                    "end": end
                })
                chunk_index += 1
            start += (self.small_chunk_size - self.small_overlap)
        return chunks

    def create_summary_for_group(self, group_chunks: list[dict]) -> dict:
        """
        Generates a summary chunk for a group of small chunks.
        
        If a summarizer is provided, it is used; otherwise, a fallback summary
        (a short excerpt) is generated.

        Args:
            group_chunks (list[dict]): List of small chunk dictionaries.
        
        Returns:
            dict: A summary chunk dictionary containing:
                - text: the summary text
                - chunk_index: starting index of the group
                - group: True flag indicating a hierarchical summary
                - group_members: list of indices of the small chunks in the group
        """
        # Combine the texts of the group into one block.
        group_text = "\n".join(chunk["text"] for chunk in group_chunks)
        if self.summarizer:
            summary_text = self.summarizer(group_text)
        else:
            # Fallback: use the first 200 characters of the group text.
            summary_text = group_text[:200] + "..." if len(group_text) > 200 else group_text

        return {
            "text": summary_text,
            "chunk_index": group_chunks[0]["chunk_index"],
            "group": True,
            "group_members": [chunk["chunk_index"] for chunk in group_chunks]
        }

    def hierarchical_chunking(self, text: str) -> dict:
        """
        Performs hierarchical chunking on the provided text.
        
        It first creates small overlapping chunks, then groups them into larger
        chunks with summaries.

        Args:
            text (str): The input text to chunk.
        
        Returns:
            dict: A dictionary with two keys:
                - "small_chunks": list of all small chunk dictionaries.
                - "summary_chunks": list of hierarchical summary chunk dictionaries.
        """
        small_chunks = self.chunk_text(text)
        summary_chunks = []

        # Group small chunks into larger segments.
        for i in range(0, len(small_chunks), self.group_size):
            group = small_chunks[i:i+self.group_size]
            summary_chunk = self.create_summary_for_group(group)
            summary_chunks.append(summary_chunk)
        
        return {
            "small_chunks": small_chunks,
            "summary_chunks": summary_chunks
        }

    def get_window_for_chunk(self, chunks: list[dict], index: int, window_size: int = 1) -> list[dict]:
        """
        Retrieves a window of chunks around a specified chunk.
        
        The window includes the chunk at the given index plus the specified
        number of adjacent chunks before and after.

        Args:
            chunks (list[dict]): The list of chunk dictionaries.
            index (int): The index of the primary chunk.
            window_size (int): Number of adjacent chunks to include on each side.
        
        Returns:
            list[dict]: The list of chunk dictionaries in the window.
        """
        start_index = max(0, index - window_size)
        end_index = min(len(chunks), index + window_size + 1)
        return chunks[start_index:end_index]
