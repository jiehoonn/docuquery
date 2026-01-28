"""
  app/services/chunker.py - Text Chunking Service

  Splits extracted text into smaller overlapping chunks for embedding.
  This is the second step in the document processing pipeline.

  Pipeline: Extract Text → Chunk → Embed → Store in Qdrant
                           ^^^^^
                          (this file)

  Why chunking?
  - Embedding models have token/character limits
  - Smaller chunks give more precise search results
  - Overlap ensures context isn't lost at chunk boundaries
"""

def chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> list[str]:
    """
    Split text into overlapping chunks.

    Args:
        text: The full document text
        chunk_size: Maximum characters per chunk (default: 512)
        overlap: Characters to overlap between chunks (default: 50)

    Returns:
        List of text chunks
    """

    # Handle empty text
    if not text or not text.strip():
        return []
    
    chunks = []
    len_text = len(text)

    # l = left pointer (start of current chunk)
    # r = right pointer (end of current chunk)
    l, r, = 0, 0

    while l < len_text:
        # Move right pointer by chunk_size
        r += chunk_size

        # If we've reached or passed the end, grab remaining text and stop
        if r >= len_text:
            chunks.append(text[l:])
            break
        
        # Extract the chunk
        chunk = text[l:r]
        chunks.append(chunk)

        # Move left pointer forward, but keep 'overlap' characters
        # This creates the overlap with the next chunk
        r -= overlap
        l = r

    return chunks