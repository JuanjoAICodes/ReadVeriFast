# Services package for VeriFast
# Re-export analysis helpers from the legacy module verifast_app/services.py so
# imports like `from verifast_app import services` and `verifast_app.services.analyze_text_content`
# continue to work even though there is also a `verifast_app/services/` package.

from .analysis_core import (
    analyze_text_content,
    get_valid_wikipedia_tags,
    generate_master_analysis,
    calculate_optimal_question_count,
    find_largest_monetary_tag,
    genai,
    nlp_en,
    nlp_es,
    wiki_en,
    wiki_es,
    textstat,
)

__all__ = [
    "analyze_text_content",
    "get_valid_wikipedia_tags",
    "generate_master_analysis",
    "calculate_optimal_question_count",
    "find_largest_monetary_tag",
    "genai",
    "nlp_en",
    "nlp_es",
    "wiki_en",
    "wiki_es",
    "textstat",
]
