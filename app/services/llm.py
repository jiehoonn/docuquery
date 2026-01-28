from google import genai
from app.core.config import settings

# Create client
client = genai.Client(api_key=settings.gemini_api_key)

def build_prompt(chunks: list[str], question: str) -> str:
    """
    Build the RAG prompt with context and question.

    Format:
        Context:
        [1] chunk 1 text
        [2] chunk 2 text

        Question: user's question

        Instructions: Answer based only on context, use citations [1], [2]
    """
    res = []
    # 1. Build Context Section
    res.append("Context:")
    for i in range(len(chunks)):
        res.append(f"[{i + 1}] {chunks[i]}")

    res.append("\n")

    # 2. Append User Question
    res.append(f"Question: {question}")

    res.append("\n")

    # 3. Build Instructions
    instructions = "Instructions: Answer based only on the context above. Include citation numbers like [1], [2] to reference sources."

    res.append(instructions)
    
    # 4. Build output
    output = "\n".join(res)
    return output


async def generate_answer(chunks: list[str], question: str) -> str:
    """
    Call Gemini API with the prompt, return the answer.

    Currently using mock response for development.
    TODO: Swap back to Gemini when quota resets.
    """
    prompt = build_prompt(chunks, question)
    
    # MOCK RESPONSE FOR DEVELOPMENT
    # This simulates what a real LLM would return
    mock_answer = f"Based on the provided context, {question.lower().replace('?', '')}. "
    mock_answer += "The relevant information can be found in [1]"
    if len(chunks) > 1:
        mock_answer += " and [2]"
    mock_answer += "."
    
    return mock_answer

    # UNCOMMENT WHEN GEMINI QUOTA RESETS
    # prompt = build_prompt(chunks, question)
    # response = client.models.generate_content(
    #     model="gemini-2.0-flash",
    #     contents=prompt
    # )
    # return response.text