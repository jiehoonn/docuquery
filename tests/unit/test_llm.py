"""
tests/unit/test_llm.py - LLM Prompt Building Tests

Tests for the prompt construction logic. We only test build_prompt() here
(pure function), NOT generate_answer() which calls the Gemini API.
"""

from app.services.llm import build_prompt


class TestBuildPrompt:
    """Tests for the RAG prompt builder."""

    def test_contains_context_header(self, sample_chunks):
        """Prompt should start with a 'Context:' section."""
        prompt = build_prompt(sample_chunks, "Any question?")
        assert "Context:" in prompt

    def test_chunks_are_numbered(self, sample_chunks):
        """Each chunk should have a [1], [2], [3] citation number."""
        prompt = build_prompt(sample_chunks, "Any question?")
        for i in range(len(sample_chunks)):
            assert f"[{i + 1}]" in prompt

    def test_all_chunk_text_included(self, sample_chunks):
        """Every chunk's text must appear in the prompt."""
        prompt = build_prompt(sample_chunks, "Tell me about Mars")
        for chunk in sample_chunks:
            assert chunk in prompt

    def test_question_included(self, sample_chunks):
        """The user's question should appear after 'Question:'."""
        question = "How tall is Olympus Mons?"
        prompt = build_prompt(sample_chunks, question)
        assert f"Question: {question}" in prompt

    def test_instructions_included(self, sample_chunks):
        """Prompt should contain grounding instructions for the LLM."""
        prompt = build_prompt(sample_chunks, "Any question?")
        assert "Answer based only on the context above" in prompt
        assert "citation" in prompt.lower()

    def test_single_chunk(self):
        """Prompt should work with just one chunk."""
        prompt = build_prompt(["Only one chunk here."], "What?")
        # Check that only one chunk citation line exists in the Context section
        context_section = prompt.split("Question:")[0]
        assert "[1]" in context_section
        assert "[2]" not in context_section

    def test_prompt_section_order(self, sample_chunks):
        """Context should come before Question, which comes before Instructions."""
        prompt = build_prompt(sample_chunks, "Some question?")
        context_pos = prompt.index("Context:")
        question_pos = prompt.index("Question:")
        instructions_pos = prompt.index("Instructions:")
        assert context_pos < question_pos < instructions_pos