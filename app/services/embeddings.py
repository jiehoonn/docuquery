"""
app/services/embeddings.py - Vector Embedding Service

Generates vector embeddings from text using sentence-transformers.                                  
This is the third step in the document processing pipeline.                                               

Pipeline: Extract Text → Chunk → Embed → Store in Qdrant
                                ^^^^^                  
                                (this file)              

What are embeddings? 
    Embeddings convert text into a list of numbers (vector) that captures                                  
    semantic meaning. Similar text produces similar vectors, enabling                                       
    "search by meaning" rather than keyword matching.

    Example:
        "How do I return an item?"  → [0.12, -0.34, 0.56, ...]                                              
        "What's the return policy?" → [0.11, -0.32, 0.55, ...]  (similar!)                                  
        "What's the weather?"       → [0.87, 0.21, -0.45, ...]  (different)                                
                                                        
Model: all-MiniLM-L6-v2
    - Dimensions: 384 (each text becomes 384 numbers)
    - Speed: Fast (good for real-time queries)
    - Quality: Good for general-purpose semantic search
    - Cost: Free (runs locally, no API calls)

TODO(cloud): In production, consider deploying the embedding model as a
    separate service (e.g., on a GPU-enabled EC2 instance or as a SageMaker
    endpoint) to avoid loading the model in every app instance. This also
    enables horizontal scaling of the API servers independently from the
    embedding compute. Alternatively, could switch to an API-based embedding
    service (OpenAI, Cohere) if self-hosting becomes a bottleneck.
"""

from sentence_transformers import SentenceTransformer

# Load model once (expensive operation)
# We load this model once and reuse the model for all embedding requests.
model = SentenceTransformer("all-MiniLM-L6-v2")

def generate_embedding(text: str) -> list[float]:
    """
    Generate an embedding vector for a single text.

    Args:
        text: The text to embed (e.g., a query or a single chunk)
    
    Returns:
        A list of 384 floats representing the text's meaning
    
    Example:
        embedding = generate_embedding("What is the return policy?")
        len(embedding)  # 384
    """
    # model.encode() returns numpy array
    # Convert to list for JSON serialization and Qdrant compatibility
    embedding = model.encode(text)
    return embedding.tolist()

def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for multiple texts in a batch.

    Batch processing is more efficient than calling generate_embedding
    in a loop because the model can process multiple texts in parallel.

    Args:
        texts: List of texts to embed (e.g., all chunks from a document)
    
    Returns:
        List of embedding vectors, one per input text
    
    Example:
        chunks = ["chunk 1 text", "chunk 2 text", "chunk 3 text"]
        embeddings = generate_embeddings(chunks)
        len(embeddings)     # 3
        len(embeddings[0])  # 384
    """
    # Handle empty input
    if not texts:
        return []
    
    # Batch encode all texts at once (much faster than looping)
    embeddings = model.encode(texts)

    # Convert numpy arrays to Python lists
    return [embedding.tolist() for embedding in embeddings]
    