"""
Difficulty Validation Engine

This is RULE-BASED logic (NO LLM).

Validates quiz difficulty against Bloom's taxonomy and concept hierarchy.
If validation fails, provides structured feedback for Agent 2 to retry.

This creates an autonomous feedback loop:
Agent 2 → Validation → Feedback → Agent 2 (retry)
"""
from typing import List, Dict, Any, Tuple
from models.schemas import Question, Concept, ValidationResult


class DifficultyValidator:
    """
    Rule-based validator for quiz difficulty.
    
    Ensures questions match requested difficulty and follow
    cognitive complexity rules (Bloom's taxonomy).
    """
    
    # Bloom's taxonomy hierarchy (lowest to highest cognitive load)
    BLOOMS_HIERARCHY = {
        "Remember": 1,
        "Understand": 2,
        "Apply": 3,
        "Analyze": 4,
        "Evaluate": 5,
        "Create": 6
    }
    
    # Difficulty ranges for each level
    DIFFICULTY_RANGES = {
        "easy": (1, 4),
        "medium": (4, 7),
        "hard": (7, 10)
    }
    
    # Expected Bloom's levels for each difficulty
    EXPECTED_BLOOMS = {
        "easy": {"Remember", "Understand"},
        "medium": {"Understand", "Apply", "Analyze"},
        "hard": {"Analyze", "Evaluate", "Create"}
    }
    
    def __init__(self, concepts: List[Concept]):
        """
        Initialize validator with concept hierarchy.
        
        Args:
            concepts: Full concept hierarchy for context
        """
        self.concepts = concepts
        self.concept_map = {c.id: c for c in concepts}
    
    def validate(
        self,
        questions: List[Question],
        target_concept: Concept,
        requested_difficulty: str
    ) -> ValidationResult:
        """
        Validate quiz difficulty.
        
        Args:
            questions: List of questions to validate
            target_concept: The concept being quizzed
            requested_difficulty: Desired difficulty (easy|medium|hard)
        
        Returns:
            ValidationResult with pass/fail and feedback
        """
        issues = []
        
        # Check 1: Exactly 10 questions
        if len(questions) != 10:
            issues.append(f"Expected 10 questions, got {len(questions)}")
        
        # Check 2: Bloom's level matches difficulty
        blooms_issues = self._validate_blooms_levels(questions, requested_difficulty)
        issues.extend(blooms_issues)
        
        # Check 3: Difficulty scores match difficulty
        score_issues = self._validate_difficulty_scores(questions, requested_difficulty)
        issues.extend(score_issues)
        
        # Check 4: Progressive difficulty
        progression_issues = self._validate_progression(questions)
        issues.extend(progression_issues)
        
        # Check 5: Concept relevance
        relevance_issues = self._validate_concept_relevance(questions, target_concept)
        issues.extend(relevance_issues)
        
        # Check 6: Hierarchy alignment
        hierarchy_issues = self._validate_hierarchy_alignment(questions, target_concept)
        issues.extend(hierarchy_issues)
        
        # Determine if validation passed
        passed = len(issues) == 0
        
        # Generate feedback
        feedback = None
        if not passed:
            feedback = self._generate_feedback(issues, requested_difficulty)
        
        return ValidationResult(
            passed=passed,
            feedback=feedback,
            issues=issues
        )
    
    def _validate_blooms_levels(
        self,
        questions: List[Question],
        requested_difficulty: str
    ) -> List[str]:
        """
        Validate that Bloom's levels match requested difficulty.
        
        Rules:
        - Easy: Mostly Remember/Understand
        - Medium: Mostly Understand/Apply/Analyze
        - Hard: Mostly Analyze/Evaluate/Create
        """
        issues = []
        expected_levels = self.EXPECTED_BLOOMS[requested_difficulty]
        
        # Count Bloom's levels
        blooms_count = {}
        for question in questions:
            level = question.blooms_level
            blooms_count[level] = blooms_count.get(level, 0) + 1
        
        # For requested difficulty, at least 60% should be in expected range
        matching_count = sum(
            blooms_count.get(level, 0) 
            for level in expected_levels
        )
        
        if matching_count < 6:  # 60% of 10 questions
            issues.append(
                f"Only {matching_count}/10 questions match {requested_difficulty} Bloom's levels. "
                f"Expected mostly: {', '.join(expected_levels)}"
            )
        
        # Check for inappropriate levels
        if requested_difficulty == "easy" and blooms_count.get("Create", 0) > 0:
            issues.append("Easy quizzes should not contain 'Create' level questions")
        
        if requested_difficulty == "hard" and blooms_count.get("Remember", 0) > 2:
            issues.append("Hard quizzes should minimize 'Remember' level questions")
        
        return issues
    
    def _validate_difficulty_scores(
        self,
        questions: List[Question],
        requested_difficulty: str
    ) -> List[str]:
        """
        Validate that difficulty scores match requested difficulty.
        
        Rules:
        - Easy: scores 1-4
        - Medium: scores 4-7
        - Hard: scores 7-10
        """
        issues = []
        min_score, max_score = self.DIFFICULTY_RANGES[requested_difficulty]
        
        # Calculate average score
        avg_score = sum(q.difficulty_score for q in questions) / len(questions)
        
        # Average should be in the middle of the range
        expected_avg = (min_score + max_score) / 2
        
        if abs(avg_score - expected_avg) > 2:
            issues.append(
                f"Average difficulty score {avg_score:.1f} doesn't match {requested_difficulty} "
                f"(expected around {expected_avg:.1f})"
            )
        
        # Check individual scores
        out_of_range = [
            q.id for q in questions 
            if q.difficulty_score < min_score - 1 or q.difficulty_score > max_score + 1
        ]
        
        if out_of_range:
            issues.append(
                f"Questions {', '.join(out_of_range)} have scores outside {requested_difficulty} range "
                f"({min_score}-{max_score})"
            )
        
        return issues
    
    def _validate_progression(self, questions: List[Question]) -> List[str]:
        """
        Validate that questions progress from easy to hard.
        
        Rule: Difficulty scores should generally increase.
        """
        issues = []
        
        # Check for monotonic increase (with some tolerance)
        scores = [q.difficulty_score for q in questions]
        
        # Allow some variation, but overall trend should be upward
        violations = 0
        for i in range(len(scores) - 1):
            # If current score is more than 2 points higher than next, it's a violation
            if scores[i] - scores[i + 1] > 2:
                violations += 1
        
        if violations > 2:  # Allow some flexibility
            issues.append(
                "Questions should progress from easy to hard. "
                f"Found {violations} significant drops in difficulty."
            )
        
        return issues
    
    def _validate_concept_relevance(
        self,
        questions: List[Question],
        target_concept: Concept
    ) -> List[str]:
        """
        Validate that questions test the target concept or its prerequisites.
        
        Rule: All questions must reference target concept or prerequisites.
        """
        issues = []
        
        # Ensure prerequisites are strings (defensive programming)
        prerequisite_ids = [
            str(p) if not isinstance(p, str) else p 
            for p in target_concept.prerequisites
        ]
        
        # Build set of valid concept IDs
        valid_concepts = {target_concept.id}
        valid_concepts.update(prerequisite_ids)
        
        # Recursively add prerequisites of prerequisites
        def add_prereqs(concept_id: str):
            if concept_id in self.concept_map:
                concept = self.concept_map[concept_id]
                # Ensure prerequisites are strings here too
                prereq_ids = [
                    str(p) if not isinstance(p, str) else p 
                    for p in concept.prerequisites
                ]
                for prereq in prereq_ids:
                    if prereq not in valid_concepts:
                        valid_concepts.add(prereq)
                        add_prereqs(prereq)
        
        for prereq in prerequisite_ids:
            add_prereqs(prereq)
        
        # Check each question
        irrelevant_questions = []
        for question in questions:
            if not any(cid in valid_concepts for cid in question.concepts):
                irrelevant_questions.append(question.id)
        
        if irrelevant_questions:
            issues.append(
                f"Questions {', '.join(irrelevant_questions)} reference concepts "
                f"unrelated to {target_concept.name} or its prerequisites"
            )
        
        return issues
    
    def _validate_hierarchy_alignment(
        self,
        questions: List[Question],
        target_concept: Concept
    ) -> List[str]:
        """
        Validate that difficulty aligns with concept hierarchy.
        
        Rule: Questions about higher-level concepts should be harder.
        """
        issues = []
        
        # For each question, get the max level of concepts it tests
        for question in questions:
            max_level = max(
                self.concept_map[cid].level 
                for cid in question.concepts 
                if cid in self.concept_map
            )
            
            # Higher level concepts should correlate with harder questions
            # This is a soft rule, so we only flag major mismatches
            expected_min_difficulty = min(max_level * 2, 8)
            
            if max_level >= 2 and question.difficulty_score < expected_min_difficulty:
                issues.append(
                    f"Question {question.id} tests level {max_level} concept "
                    f"but has difficulty {question.difficulty_score} "
                    f"(expected >= {expected_min_difficulty})"
                )
        
        return issues
    
    def _generate_feedback(
        self,
        issues: List[str],
        requested_difficulty: str
    ) -> str:
        """
        Generate structured feedback for Agent 2 to retry.
        
        This feedback guides the agent to fix specific issues.
        """
        feedback_parts = [
            f"Quiz validation failed for {requested_difficulty} difficulty.",
            "\nIssues found:",
        ]
        
        for i, issue in enumerate(issues, 1):
            feedback_parts.append(f"{i}. {issue}")
        
        feedback_parts.append("\nPlease regenerate the quiz addressing these issues.")
        
        return "\n".join(feedback_parts)


# ====================================================
# Public API
# ====================================================

def validate_quiz_difficulty(
    questions: List[Question],
    target_concept: Concept,
    all_concepts: List[Concept],
    requested_difficulty: str
) -> ValidationResult:
    """
    Validate quiz difficulty.
    
    Args:
        questions: Quiz questions to validate
        target_concept: The concept being quizzed
        all_concepts: Full concept hierarchy
        requested_difficulty: Requested difficulty level
    
    Returns:
        ValidationResult with pass/fail status and feedback
    """
    validator = DifficultyValidator(all_concepts)
    return validator.validate(questions, target_concept, requested_difficulty)
