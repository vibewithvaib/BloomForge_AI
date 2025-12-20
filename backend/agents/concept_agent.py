"""
AI Agent 1: Concept Extraction & Hierarchy Builder

ROLE: Curriculum Designer + Subject Matter Expert

This agent runs EXACTLY ONCE per document upload.
It analyzes the full educational text and produces a structured concept hierarchy.

Uses LangGraph for orchestration with the following workflow:
1. Read full text from vector store
2. Extract key concepts (LLM call)
3. Build hierarchy (LLM call with validation)
4. Return structured JSON

CRITICAL: This agent sees the RAW TEXT.
"""
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langgraph.graph import StateGraph, END
import json

from models.schemas import Concept, ConceptHierarchy
from config import settings


class ConceptExtractionAgent:
    """
    Agent 1: Extract concepts and build dependency hierarchy.
    
    Workflow:
    1. analyze_text → Extract concepts
    2. build_hierarchy → Assign levels and prerequisites
    3. validate_output → Ensure JSON correctness
    """
    
    def __init__(self):
        """Initialize LLM and prompts."""
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.3,  # Lower temperature for more consistent extraction
            openai_api_key=settings.openai_api_key
        )
        
        self.parser = PydanticOutputParser(pydantic_object=ConceptHierarchy)
    
    def _create_extraction_prompt(self) -> ChatPromptTemplate:
        """
        Prompt for extracting concepts from educational text.
        
        This is the critical instruction that shapes the entire hierarchy.
        """
        return ChatPromptTemplate.from_messages([
            ("system", """You are an expert curriculum designer and subject matter expert.

Your task is to analyze educational text and extract a structured hierarchy of key concepts.

RULES:
1. Extract ONLY teachable concepts, not examples or anecdotes
2. Each concept must be independently explainable and testable
3. Assign each concept a unique ID (C1, C2, C3, ...)
4. Provide a concise definition (1-2 sentences)
5. Score importance from 0.0 to 1.0
6. Identify prerequisite concepts (concepts that must be understood first)
7. Assign hierarchy levels:
   - Level 0: Foundational concepts (no prerequisites)
   - Level 1+: Concepts that depend on others

IMPORTANT:
- Be adaptive: extract as many or as few concepts as needed
- Prioritize quality over quantity
- Ensure prerequisites form a valid DAG (no circular dependencies)

{format_instructions}

Return ONLY valid JSON matching the schema."""),
            ("user", "Educational text:\n\n{text}")
        ])
    
    async def extract_concepts(self, text: str) -> ConceptHierarchy:
        """
        Main entry point: Extract concepts from text.
        
        This is a single LLM call with structured output parsing.
        """
        # Create prompt
        prompt = self._create_extraction_prompt()
        
        # Format with instructions
        formatted_prompt = prompt.format_messages(
            text=text,
            format_instructions=self.parser.get_format_instructions()
        )
        
        # Call LLM
        response = await self.llm.ainvoke(formatted_prompt)
        
        # Parse response
        try:
            # Try to parse as structured output
            hierarchy = self.parser.parse(response.content)
            
            # Validate hierarchy
            self._validate_hierarchy(hierarchy)
            
            return hierarchy
        
        except Exception as e:
            # If parsing fails, try to extract JSON from response
            print(f"Parsing failed: {e}")
            print(f"Response: {response.content}")
            
            # Attempt to extract JSON manually
            hierarchy = self._extract_json_fallback(response.content)
            
            if hierarchy:
                self._validate_hierarchy(hierarchy)
                return hierarchy
            
            raise ValueError(f"Failed to extract valid concept hierarchy: {e}")
    
    def _extract_json_fallback(self, content: str) -> ConceptHierarchy:
        """
        Fallback parser if structured output fails.
        Looks for JSON in the response.
        """
        try:
            # Try to find JSON in the response
            start = content.find('{')
            end = content.rfind('}') + 1
            
            if start != -1 and end > start:
                json_str = content[start:end]
                data = json.loads(json_str)
                
                # Convert to ConceptHierarchy
                concepts = [Concept(**c) for c in data.get('concepts', [])]
                return ConceptHierarchy(concepts=concepts)
        
        except Exception as e:
            print(f"Fallback parsing failed: {e}")
        
        return None
    
    def _validate_hierarchy(self, hierarchy: ConceptHierarchy):
        """
        Validate the concept hierarchy for correctness.
        
        Checks:
        1. All prerequisite IDs exist
        2. No circular dependencies
        3. Level assignments are consistent with prerequisites
        """
        concept_ids = {c.id for c in hierarchy.concepts}
        
        # Check all prerequisites exist
        for concept in hierarchy.concepts:
            for prereq in concept.prerequisites:
                if prereq not in concept_ids:
                    raise ValueError(
                        f"Concept {concept.id} references non-existent prerequisite {prereq}"
                    )
        
        # Check for circular dependencies (simple DFS)
        def has_cycle(concept_id: str, visited: set, stack: set) -> bool:
            visited.add(concept_id)
            stack.add(concept_id)
            
            # Find concept
            concept = next((c for c in hierarchy.concepts if c.id == concept_id), None)
            if not concept:
                return False
            
            # Check prerequisites
            for prereq in concept.prerequisites:
                if prereq not in visited:
                    if has_cycle(prereq, visited, stack):
                        return True
                elif prereq in stack:
                    return True
            
            stack.remove(concept_id)
            return False
        
        visited = set()
        for concept in hierarchy.concepts:
            if concept.id not in visited:
                if has_cycle(concept.id, visited, set()):
                    raise ValueError(f"Circular dependency detected involving {concept.id}")
        
        # Validate level assignments
        concept_map = {c.id: c for c in hierarchy.concepts}
        for concept in hierarchy.concepts:
            if concept.prerequisites:
                # Level should be at least max(prereq levels) + 1
                max_prereq_level = max(
                    concept_map[prereq].level 
                    for prereq in concept.prerequisites
                )
                if concept.level <= max_prereq_level:
                    print(f"Warning: Concept {concept.id} level may be incorrect")


# ====================================================
# LangGraph Workflow (Alternative Orchestration)
# ====================================================

class ConceptExtractionWorkflow:
    """
    LangGraph-based workflow for concept extraction.
    
    This provides more explicit state management and error handling.
    """
    
    def __init__(self):
        self.agent = ConceptExtractionAgent()
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        
        # Define state
        class State(dict):
            text: str
            hierarchy: ConceptHierarchy = None
            error: str = None
        
        # Create graph
        graph = StateGraph(dict)
        
        # Add nodes
        graph.add_node("extract", self._extract_node)
        graph.add_node("validate", self._validate_node)
        
        # Define flow
        graph.set_entry_point("extract")
        graph.add_edge("extract", "validate")
        graph.add_edge("validate", END)
        
        return graph.compile()
    
    async def _extract_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract concepts from text."""
        try:
            hierarchy = await self.agent.extract_concepts(state["text"])
            return {"hierarchy": hierarchy}
        except Exception as e:
            return {"error": str(e)}
    
    async def _validate_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Validate extracted hierarchy."""
        if state.get("error"):
            return state
        
        try:
            self.agent._validate_hierarchy(state["hierarchy"])
            return state
        except Exception as e:
            return {"error": f"Validation failed: {e}"}
    
    async def run(self, text: str) -> ConceptHierarchy:
        """Execute the workflow."""
        result = await self.graph.ainvoke({"text": text})
        
        if result.get("error"):
            raise ValueError(result["error"])
        
        return result["hierarchy"]


# ====================================================
# Public API
# ====================================================

async def extract_concept_hierarchy(text: str) -> ConceptHierarchy:
    """
    Main entry point for concept extraction.
    
    Args:
        text: Raw educational text
    
    Returns:
        ConceptHierarchy with extracted concepts
    
    Raises:
        ValueError if extraction fails
    """
    # Use the simple agent by default
    # Can switch to workflow for more complex orchestration
    agent = ConceptExtractionAgent()
    return await agent.extract_concepts(text)
