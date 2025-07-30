"""
Pydantic models for LLM API responses and validation.
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional
import re


class QuizOption(BaseModel):
    """Model for individual quiz answer options with validation."""

    text: str = Field(
        min_length=1, max_length=200, description="The answer option text"
    )

    @field_validator("text")
    @classmethod
    def validate_option_text(cls, v):
        """Validate and clean option text."""
        # Remove excessive whitespace and ensure proper formatting
        cleaned = re.sub(r"\s+", " ", v.strip())
        if not cleaned:
            raise ValueError("Option text cannot be empty")
        return cleaned


class QuizQuestion(BaseModel):
    """Model for individual quiz questions with validation."""

    question: str = Field(
        min_length=10, max_length=500, description="The quiz question text"
    )
    options: List[str] = Field(
        min_length=4,
        max_length=4,
        description="Exactly 4 answer options for the question",
    )
    correct_answer: str = Field(
        alias="answer", description="The text of the correct answer"
    )
    explanation: Optional[str] = Field(
        None, max_length=1000, description="Optional explanation for the correct answer"
    )

    @field_validator("question")
    @classmethod
    def validate_question_text(cls, v):
        """Validate and clean question text."""
        cleaned = re.sub(r"\s+", " ", v.strip())
        if not cleaned.endswith("?"):
            cleaned += "?"
        return cleaned

    @field_validator("options")
    @classmethod
    def validate_unique_options(cls, v):
        """Ensure all quiz options are unique and properly formatted."""
        if len(set(v)) != len(v):
            raise ValueError("Quiz options must be unique")

        # Clean and validate each option
        cleaned_options = []
        for option in v:
            cleaned = re.sub(r"\s+", " ", option.strip())
            if not cleaned:
                raise ValueError("Option text cannot be empty")
            cleaned_options.append(cleaned)

        return cleaned_options

    @model_validator(mode="after")
    def validate_correct_answer_in_options(self):
        """Ensure correct answer matches one of the options."""
        if self.correct_answer not in self.options:
            raise ValueError(
                f'Correct answer "{self.correct_answer}" must be one of the provided options'
            )
        return self


class TagValidation(BaseModel):
    """Model for validating individual tags."""

    name: str = Field(min_length=1, max_length=50, description="Tag name")
    confidence: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Confidence score for tag relevance"
    )

    @field_validator("name")
    @classmethod
    def validate_tag_name(cls, v):
        """Validate and normalize tag name."""
        # Clean whitespace and normalize case
        cleaned = re.sub(r"\s+", " ", v.strip().title())

        # Remove special characters except spaces and hyphens
        cleaned = re.sub(r"[^\w\s\-]", "", cleaned)

        if not cleaned:
            raise ValueError("Tag name cannot be empty after cleaning")

        return cleaned


class MasterAnalysisResponse(BaseModel):
    """Model for complete LLM analysis response including quiz and tags."""

    quiz: List[QuizQuestion] = Field(
        min_length=5,
        max_length=30,
        description="List of 5-30 quiz questions generated based on article length and complexity",
    )
    tags: List[str] = Field(
        min_length=1,
        max_length=7,
        description="List of 1-7 canonical tags extracted from the article",
    )
    reading_level: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Calculated reading difficulty level (0-100)",
    )
    key_concepts: Optional[List[str]] = Field(
        None, max_length=10, description="Key concepts identified in the article"
    )

    @field_validator("quiz")
    @classmethod
    def validate_quiz_questions(cls, v):
        """Validate quiz questions for quality and uniqueness."""
        if len(v) < 5:
            raise ValueError("At least 5 quiz questions are required")

        # Check for duplicate questions
        questions = [q.question for q in v]
        if len(set(questions)) != len(questions):
            raise ValueError("Quiz questions must be unique")

        return v

    @field_validator("tags")
    @classmethod
    def validate_and_clean_tags(cls, v):
        """Clean and validate tags list."""
        if not v:
            raise ValueError("At least one tag is required")

        # Clean and deduplicate tags
        cleaned_tags = []
        seen_tags = set()

        for tag in v:
            # Clean the tag
            cleaned = re.sub(r"\s+", " ", tag.strip().title())
            cleaned = re.sub(r"[^\w\s\-]", "", cleaned)

            if cleaned and cleaned not in seen_tags:
                cleaned_tags.append(cleaned)
                seen_tags.add(cleaned)

        if not cleaned_tags:
            raise ValueError("No valid tags found after cleaning")

        return cleaned_tags[:7]  # Limit to 7 tags

    @field_validator("key_concepts")
    @classmethod
    def validate_key_concepts(cls, v):
        """Validate and clean key concepts."""
        if v is None:
            return v

        cleaned_concepts = []
        for concept in v:
            cleaned = re.sub(r"\s+", " ", concept.strip())
            if cleaned:
                cleaned_concepts.append(cleaned)

        return cleaned_concepts[:10]  # Limit to 10 concepts


class LLMGenerationRequest(BaseModel):
    """Model for LLM generation requests."""

    content: str = Field(min_length=100, description="Article content to analyze")
    language: str = Field(pattern=r"^(en|es)$", description="Language code (en or es)")
    max_questions: int = Field(
        default=10,
        ge=5,
        le=30,
        description="Maximum number of quiz questions to generate",
    )
    difficulty_level: Optional[str] = Field(
        None, pattern=r"^(easy|medium|hard)$", description="Desired difficulty level"
    )
    focus_areas: Optional[List[str]] = Field(
        None,
        max_length=5,
        description="Specific areas to focus on for question generation",
    )

    @field_validator("content")
    @classmethod
    def validate_content_length(cls, v):
        """Ensure content is substantial enough for analysis."""
        word_count = len(v.split())
        if word_count < 50:
            raise ValueError(
                "Content must contain at least 50 words for meaningful analysis"
            )
        return v


class LLMGenerationMetadata(BaseModel):
    """Metadata about LLM generation process."""

    model_name: str = Field(description="Name of the LLM model used")
    generation_time: float = Field(
        ge=0.0, description="Time taken for generation in seconds"
    )
    token_count: Optional[int] = Field(
        None, ge=0, description="Number of tokens processed"
    )
    temperature: Optional[float] = Field(
        None, ge=0.0, le=2.0, description="Temperature setting used"
    )
    success: bool = Field(description="Whether generation was successful")
    error_message: Optional[str] = Field(
        None, description="Error message if generation failed"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "model_name": "gemini-pro",
                "generation_time": 2.5,
                "token_count": 1500,
                "temperature": 0.7,
                "success": True,
                "error_message": None,
            }
        }
    }
