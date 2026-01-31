"""
app/services/llm.py - Large Language Model Service

Handles interaction with the LLM (Google Gemini) for generating answers
from retrieved document chunks. This is the final step in the RAG query flow.

Query flow: Cache Check → Embed Query → Vector Search → LLM Generate Answer
                                                        ^^^^^^^^^^^^^^^^^^^^
                                                           (this file)

How RAG prompting works:
    We don't just send the user's question to the LLM. Instead, we build a
    structured prompt that includes:
    1. Context - The relevant document chunks found by vector search
    2. Question - The user's original question
    3. Instructions - Tell the LLM to answer ONLY from context and cite sources

    This "grounding" prevents hallucination - the LLM can only use information
    we explicitly provide, not its general training knowledge.

TODO(cloud): Consider abstracting the LLM provider behind an interface
    so we can swap between Gemini, OpenAI, Claude, or local models without
    changing the rest of the codebase. This would also enable A/B testing
    different models for answer quality.
"""

from google import genai

from app.core.config import settings

# Create Gemini client at module level (reused across all requests)
# The API key is loaded from environment variables via settings
client = genai.Client(api_key=settings.gemini_api_key)


def build_prompt(chunks: list[str], question: str) -> str:
    """
    Build the RAG prompt with context chunks and user question.

    This constructs a structured prompt that grounds the LLM's response
    in the provided document chunks. The numbered citations [1], [2], etc.
    allow the user to trace which chunks informed each part of the answer.

    Args:
        chunks: List of relevant text chunks from vector search
        question: The user's original question

    Returns:
        A formatted prompt string ready to send to the LLM

    Example output:
        Context:
        [1] First chunk of relevant text...
        [2] Second chunk of relevant text...

        Question: What is the return policy?

        Instructions: Answer based only on the context above. Include
        citation numbers like [1], [2] to reference sources.
    """
    res = []

    # 1. Build Context Section - numbered chunks for citation
    res.append("Context:")
    for i in range(len(chunks)):
        res.append(f"[{i + 1}] {chunks[i]}")

    res.append("\n")

    # 2. Append User Question
    res.append(f"Question: {question}")

    res.append("\n")

    # 3. Build Instructions - constrain LLM to only use provided context
    # This is critical for RAG: without these instructions, the LLM might
    # answer from its general knowledge instead of the user's documents
    instructions = "Instructions: Answer based only on the context above. Include citation numbers like [1], [2] to reference sources."

    res.append(instructions)

    # 4. Join all parts with newlines into a single prompt string
    output = "\n".join(res)
    return output


async def generate_answer(chunks: list[str], question: str) -> str:
    """
    Generate an answer using the Gemini LLM with RAG context.

    Builds a grounded prompt from the chunks and question, sends it to
    Gemini, and returns the generated answer text.

    Args:
        chunks: List of relevant text chunks (from Qdrant vector search)
        question: The user's original question

    Returns:
        The LLM-generated answer text with citation references

    Note:
        Using gemini-2.0-flash for cost efficiency. It's fast and cheap
        while still producing quality answers for RAG use cases.

    TODO(cloud): Add error handling for API rate limits and timeouts.
        Implement retry logic with exponential backoff (max 3 attempts).
        Track token usage per tenant for cost monitoring via the
        docuquery_llm_tokens_used_total Prometheus metric.
    """
    prompt = build_prompt(chunks, question)

    response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)

    return response.text
