"""
AI Agent 2: Adaptive Explanation & Quiz Generator

STRICT QUIZ MODE:
- Quiz MUST contain EXACTLY 10 questions
- If not, generation FAILS
"""

from typing import List
import sys

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from models.schemas import Concept, Question, QuizOutput
from config import settings


class AdaptiveAgent:
    """
    Agent 2: Adaptive tutor that explains and assesses concepts.
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.2,
            openai_api_key=settings.openai_api_key
        )

        self.quiz_parser = PydanticOutputParser(
            pydantic_object=QuizOutput
        )

    # ====================================================
    # MODE A: EXPLANATION GENERATION
    # ====================================================

    def _create_explanation_prompt(self, tone: str) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages([
            (
                "system",
                "You are an expert educator. Explain the concept clearly and accurately."
            ),
            (
                "user",
                """
Concept: {concept_name}
Definition: {concept_definition}
Prerequisites: {prerequisites}

Hierarchy:
{hierarchy}

Tone: {tone}
"""
            )
        ])

    async def generate_explanation(
        self,
        target_concept: Concept,
        all_concepts: List[Concept],
        tone: str
    ) -> str:

        prereqs = [
            c for c in all_concepts
            if c.id in target_concept.prerequisites
        ]

        prereq_text = ", ".join(c.name for c in prereqs) or "None"

        hierarchy_text = "\n".join(
            f"- {c.id}: {c.name}" for c in all_concepts
        )

        prompt = self._create_explanation_prompt(tone)

        response = await self.llm.ainvoke(
            prompt.format_messages(
                concept_name=target_concept.name,
                concept_definition=target_concept.definition,
                prerequisites=prereq_text,
                hierarchy=hierarchy_text,
                tone=tone
            )
        )

        return response.content.strip()

    # ====================================================
    # MODE B: QUIZ GENERATION (STRICT)
    # ====================================================

    def _create_quiz_prompt(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages([
            (
                "system",
                """
You are an expert assessment designer.

CRITICAL RULES:
- Return EXACTLY 10 questions
- Output MUST be valid JSON
- No markdown
- No explanations
- No extra text

{format_instructions}
"""
            ),
            (
                "user",
                """
Target concept: {concept_name}
Definition: {concept_definition}
Level: {concept_level}
Prerequisites: {prerequisites}

Hierarchy:
{hierarchy}

Difficulty rules:
{difficulty_text}

FINAL WARNING:
If you return anything other than EXACTLY 10 questions, the output is INVALID.
"""
            )
        ])

    async def generate_quiz(
        self,
        target_concept: Concept,
        all_concepts: List[Concept],
        difficulty: str
    ) -> List[Question]:

        difficulty_map = {
            "easy": "Bloom: Remember, Understand | Score 1–4",
            "medium": "Bloom: Apply, Analyze | Score 4–7",
            "hard": "Bloom: Evaluate, Create | Score 7–10"
        }

        difficulty_text = difficulty_map.get(
            difficulty,
            difficulty_map["medium"]
        )

        prereqs = [
            c for c in all_concepts
            if c.id in target_concept.prerequisites
        ]

        prereq_text = (
            ", ".join(f"{c.id}: {c.name}" for c in prereqs)
            if prereqs else "None"
        )

        hierarchy_text = "\n".join(
            f"- {c.id}: {c.name} (Level {c.level})"
            for c in sorted(all_concepts, key=lambda x: x.level)
        )

        prompt = self._create_quiz_prompt()

        response = await self.llm.ainvoke(
            prompt.format_messages(
                format_instructions=self.quiz_parser.get_format_instructions(),
                concept_name=target_concept.name,
                concept_definition=target_concept.definition,
                concept_level=target_concept.level,
                prerequisites=prereq_text,
                hierarchy=hierarchy_text,
                difficulty_text=difficulty_text
            )
        )

        # 🔥 FORCE RAW OUTPUT PRINT
        sys.stdout.write("\n===== RAW QUIZ LLM RESPONSE =====\n")
        sys.stdout.write(response.content + "\n")
        sys.stdout.write("================================\n")
        sys.stdout.flush()

        parsed = self.quiz_parser.parse(response.content)
        questions = parsed.questions

        if len(questions) != 10:
            raise ValueError(
                f"LLM returned {len(questions)} questions. EXACTLY 10 required."
            )

        valid_ids = {c.id for c in all_concepts}
        for q in questions:
            for cid in q.concepts:
                if cid not in valid_ids:
                    raise ValueError(
                        f"Question {q.id} references invalid concept {cid}"
                    )

        return questions


# ====================================================
# PUBLIC API (USED BY ROUTES)
# ====================================================

async def generate_explanation(
    target_concept: Concept,
    all_concepts: List[Concept],
    tone: str = "simple"
) -> str:
    agent = AdaptiveAgent()
    return await agent.generate_explanation(
        target_concept,
        all_concepts,
        tone
    )


async def generate_quiz(
    target_concept: Concept,
    all_concepts: List[Concept],
    difficulty: str = "medium"
) -> List[Question]:
    agent = AdaptiveAgent()
    return await agent.generate_quiz(
        target_concept,
        all_concepts,
        difficulty
    )
