"""
Language Detection and Processing Pipeline
Handles automatic language detection and language-specific processing
"""

import logging
from typing import Dict, Any, Tuple, List

from ..pydantic_models.dto import ContentAcquisitionDTO

logger = logging.getLogger(__name__)


class LanguageProcessor:
    """Service for language detection and processing"""
    
    def __init__(self):
        self.supported_languages = ['en', 'es']
        self.default_language = 'en'
        
        # Language-specific processing rules
        self.language_config = {
            'en': {
                'name': 'English',
                'min_content_length': 200,
                'max_content_length': 50000,
                'stop_words': {
                    'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have',
                    'i', 'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you',
                    'do', 'at', 'this', 'but', 'his', 'by', 'from', 'they',
                    'we', 'say', 'her', 'she', 'or', 'an', 'will', 'my',
                    'one', 'all', 'would', 'there', 'their'
                },
                'common_patterns': [
                    r'\b(the|a|an)\s+\w+',  # Articles
                    r'\b(is|are|was|were)\s+\w+',  # Copula verbs
                    r'\b\w+ing\b',  # Present participles
                    r'\b\w+ed\b',   # Past participles
                ]
            },
            'es': {
                'name': 'Spanish',
                'min_content_length': 200,
                'max_content_length': 50000,
                'stop_words': {
                    'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'es', 'se',
                    'no', 'te', 'lo', 'le', 'da', 'su', 'por', 'son', 'con',
                    'para', 'al', 'del', 'los', 'las', 'una', 'como', 'pero',
                    'sus', 'me', 'ya', 'muy', 'mi', 'si', 'sin', 'sobre',
                    'este', 'ser', 'tiene', 'todo', 'esta', 'era', 'cuando'
                },
                'common_patterns': [
                    r'\b(el|la|los|las)\s+\w+',  # Articles
                    r'\b(es|son|está|están)\s+\w+',  # Copula verbs
                    r'\b\w+ando\b',  # Present participles
                    r'\b\w+ado\b',   # Past participles
                    r'\b\w+ción\b',  # Common suffix
                ]
            }
        }
    
    def detect_language(self, text: str, title: str = "") -> Tuple[str, float]:
        """
        Detect language of text content
        Returns: (language_code, confidence_score)
        """
        if not text or len(text.strip()) < 10:
            return self.default_language, 0.0
        
        # Combine title and content for better detection
        combined_text = f"{title} {text}".strip()
        
        try:
            # Try using langdetect library
            from langdetect import detect_langs
            
            # Get language probabilities
            lang_probs = detect_langs(combined_text)
            
            # Find the best supported language
            for lang_prob in lang_probs:
                if lang_prob.lang in self.supported_languages:
                    return lang_prob.lang, lang_prob.prob
            
            # If no supported language found, use pattern-based detection
            return self._pattern_based_detection(combined_text)
            
        except Exception as e:
            logger.warning(f"Language detection failed: {str(e)}")
            # Fallback to pattern-based detection
            return self._pattern_based_detection(combined_text)
    
    def _pattern_based_detection(self, text: str) -> Tuple[str, float]:
        """Fallback language detection using patterns and keywords"""
        text_lower = text.lower()
        
        # Count language-specific indicators
        language_scores = {}
        
        for lang_code, config in self.language_config.items():
            score = 0
            
            # Count stop words
            stop_words = config['stop_words']
            words = text_lower.split()
            stop_word_count = sum(1 for word in words if word in stop_words)
            
            if len(words) > 0:
                stop_word_ratio = stop_word_count / len(words)
                score += stop_word_ratio * 100
            
            # Count pattern matches
            import re
            for pattern in config['common_patterns']:
                matches = len(re.findall(pattern, text_lower))
                score += matches * 2
            
            language_scores[lang_code] = score
        
        # Return language with highest score
        if language_scores:
            best_lang = max(language_scores, key=language_scores.get)
            max_score = language_scores[best_lang]
            
            # Normalize confidence (rough approximation)
            confidence = min(max_score / 50.0, 1.0)
            
            return best_lang, confidence
        
        return self.default_language, 0.1
    
    def validate_language_content(self, dto: ContentAcquisitionDTO) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validate content meets language-specific requirements
        Returns: (is_valid, reason, details)
        """
        details = {
            'detected_language': dto.language,
            'content_length': len(dto.content),
            'title_length': len(dto.title),
            'checks_performed': []
        }
        
        # Get language configuration
        lang_config = self.language_config.get(dto.language)
        if not lang_config:
            details['checks_performed'].append('unsupported_language')
            return False, f"Unsupported language: {dto.language}", details
        
        # Check content length
        content_length = len(dto.content)
        min_length = max(lang_config['min_content_length'], 1200)  # Global minimum to reduce short items
        max_length = lang_config['max_content_length']
        
        details['checks_performed'].append('content_length')
        details['min_length'] = min_length
        details['max_length'] = max_length
        
        if content_length < min_length:
            return False, f"Content too short: {content_length} < {min_length}", details
        
        if content_length > max_length:
            return False, f"Content too long: {content_length} > {max_length}", details
        
        # Check title length
        title_length = len(dto.title)
        details['checks_performed'].append('title_length')
        
        if title_length < 10:
            return False, f"Title too short: {title_length} characters", details
        
        if title_length > 200:
            return False, f"Title too long: {title_length} characters", details
        
        # Language consistency check
        detected_lang, confidence = self.detect_language(dto.content, dto.title)
        details['checks_performed'].append('language_consistency')
        details['detected_language'] = detected_lang
        details['detection_confidence'] = confidence
        
        if detected_lang != dto.language and confidence > 0.7:
            return False, f"Language mismatch: expected {dto.language}, detected {detected_lang} (confidence: {confidence:.2f})", details
        
        # Content quality checks
        details['checks_performed'].append('content_quality')
        
        # Check for minimum word count
        words = dto.content.split()
        word_count = len(words)
        details['word_count'] = word_count
        
        min_words = 250 if dto.language == 'en' else 300  # Increase to avoid short/summary content
        if word_count < min_words:
            return False, f"Insufficient word count: {word_count} < {min_words}", details
        
        # Check for reasonable sentence structure
        sentences = dto.content.split('.')
        sentence_count = len([s for s in sentences if len(s.strip()) > 10])
        details['sentence_count'] = sentence_count
        
        if sentence_count < 5:
            return False, f"Insufficient sentence structure: {sentence_count} sentences", details
        
        # All checks passed
        details['checks_performed'].append('all_checks_passed')
        return True, "Content validation passed", details
    
    def process_content_for_language(self, dto: ContentAcquisitionDTO) -> ContentAcquisitionDTO:
        """Process content with language-specific enhancements"""
        
        # Detect and validate language if not specified
        if not dto.language or dto.language not in self.supported_languages:
            detected_lang, confidence = self.detect_language(dto.content, dto.title)
            dto.language = detected_lang
            logger.info(f"Detected language: {detected_lang} (confidence: {confidence:.2f})")
        
        # Clean and normalize content based on language
        dto.content = self._clean_content_for_language(dto.content, dto.language)
        dto.title = self._clean_title_for_language(dto.title, dto.language)
        
        # Extract language-specific tags
        if not dto.tags:
            dto.tags = self._extract_language_specific_tags(dto.content, dto.title, dto.language)
        
        return dto
    
    def _clean_content_for_language(self, content: str, language: str) -> str:
        """Clean content with language-specific rules"""
        import re
        
        # Common cleaning for all languages
        content = re.sub(r'\s+', ' ', content).strip()
        
        # Language-specific cleaning
        if language == 'es':
            # Spanish-specific cleaning
            content = re.sub(r'¿([^?]+)\?', r'\1?', content)  # Normalize question marks
            content = re.sub(r'¡([^!]+)!', r'\1!', content)   # Normalize exclamation marks
        
        elif language == 'en':
            # English-specific cleaning
            content = re.sub(r'\b(Mr|Mrs|Dr|Prof)\.\s+', r'\1. ', content)  # Normalize titles
        
        return content
    
    def _clean_title_for_language(self, title: str, language: str) -> str:
        """Clean title with language-specific rules"""
        import re
        
        # Common title cleaning
        title = re.sub(r'\s+', ' ', title).strip()
        
        # Remove common prefixes/suffixes
        prefixes_to_remove = [
            r'^(Breaking|BREAKING):\s*',
            r'^(News|NEWS):\s*',
            r'^(Update|UPDATE):\s*',
        ]
        
        for prefix in prefixes_to_remove:
            title = re.sub(prefix, '', title, flags=re.IGNORECASE)
        
        # Language-specific title cleaning
        if language == 'es':
            # Spanish-specific title cleaning
            spanish_prefixes = [
                r'^(Noticia|NOTICIA):\s*',
                r'^(Último|ÚLTIMO):\s*',
                r'^(Actualización|ACTUALIZACIÓN):\s*',
            ]
            for prefix in spanish_prefixes:
                title = re.sub(prefix, '', title, flags=re.IGNORECASE)
        
        return title.strip()
    
    def _extract_language_specific_tags(self, content: str, title: str, language: str) -> List[str]:
        """Extract tags using language-specific keywords"""
        text = f"{title} {content}".lower()
        
        # Language-specific tag extraction
        if language == 'es':
            tag_keywords = {
                'Tecnología': ['tecnología', 'software', 'inteligencia artificial', 'computadora', 'digital', 'internet', 'aplicación'],
                'Ciencia': ['ciencia', 'investigación', 'estudio', 'descubrimiento', 'experimento', 'científico', 'biología'],
                'Salud': ['salud', 'médico', 'medicina', 'doctor', 'hospital', 'enfermedad', 'tratamiento'],
                'Negocios': ['negocios', 'economía', 'mercado', 'finanzas', 'empresa', 'corporativo', 'inversión'],
                'Política': ['política', 'gobierno', 'elección', 'político', 'congreso', 'senado', 'presidente'],
                'Educación': ['educación', 'escuela', 'universidad', 'estudiante', 'profesor', 'aprendizaje', 'académico'],
                'Deportes': ['deportes', 'fútbol', 'baloncesto', 'béisbol', 'tenis', 'atleta', 'juego', 'partido'],
                'Entretenimiento': ['entretenimiento', 'película', 'música', 'celebridad', 'actor', 'actriz', 'concierto']
            }
        else:  # English
            tag_keywords = {
                'Technology': ['technology', 'software', 'artificial intelligence', 'computer', 'digital', 'internet', 'app'],
                'Science': ['science', 'research', 'study', 'discovery', 'experiment', 'scientific', 'biology'],
                'Health': ['health', 'medical', 'medicine', 'doctor', 'hospital', 'disease', 'treatment'],
                'Business': ['business', 'economy', 'market', 'finance', 'company', 'corporate', 'investment'],
                'Politics': ['politics', 'government', 'election', 'political', 'congress', 'senate', 'president'],
                'Education': ['education', 'school', 'university', 'student', 'teacher', 'learning', 'academic'],
                'Sports': ['sports', 'football', 'basketball', 'baseball', 'tennis', 'athlete', 'game', 'match'],
                'Entertainment': ['entertainment', 'movie', 'music', 'celebrity', 'actor', 'actress', 'concert']
            }
        
        # Find matching tags
        found_tags = []
        for tag, keywords in tag_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score >= 2:  # Require at least 2 keyword matches
                found_tags.append(tag)
        
        # Limit to top 5 tags
        return found_tags[:5]
    
    def get_language_specific_prompts(self, language: str) -> Dict[str, str]:
        """Get language-specific prompts for AI processing"""
        
        if language == 'es':
            return {
                'quiz_generation': """
                Analiza el siguiente artículo en español y genera un cuestionario de comprensión.
                
                Instrucciones:
                - Crea entre 5-10 preguntas de opción múltiple
                - Cada pregunta debe tener exactamente 4 opciones (A, B, C, D)
                - Las preguntas deben cubrir los puntos principales del artículo
                - Incluye una explicación breve para cada respuesta correcta
                - Usa un español claro y apropiado para el nivel educativo
                
                Formato de respuesta JSON:
                {
                    "quiz": [
                        {
                            "question": "Pregunta aquí",
                            "options": ["Opción A", "Opción B", "Opción C", "Opción D"],
                            "answer": "Opción correcta",
                            "explanation": "Explicación de por qué es correcta"
                        }
                    ],
                    "tags": ["etiqueta1", "etiqueta2", "etiqueta3"]
                }
                """,
                
                'tag_extraction': """
                Extrae las etiquetas más relevantes de este artículo en español.
                Proporciona entre 3-7 etiquetas que representen los temas principales.
                Las etiquetas deben estar en español y ser específicas pero no demasiado técnicas.
                """,
                
                'content_summary': """
                Proporciona un resumen conciso de este artículo en español.
                El resumen debe capturar los puntos principales en 2-3 oraciones.
                """
            }
        
        else:  # English
            return {
                'quiz_generation': """
                Analyze the following English article and generate a comprehension quiz.
                
                Instructions:
                - Create 5-10 multiple choice questions
                - Each question must have exactly 4 options (A, B, C, D)
                - Questions should cover the main points of the article
                - Include a brief explanation for each correct answer
                - Use clear, educational-level English
                
                JSON response format:
                {
                    "quiz": [
                        {
                            "question": "Question here",
                            "options": ["Option A", "Option B", "Option C", "Option D"],
                            "answer": "Correct option",
                            "explanation": "Explanation of why it's correct"
                        }
                    ],
                    "tags": ["tag1", "tag2", "tag3"]
                }
                """,
                
                'tag_extraction': """
                Extract the most relevant tags from this English article.
                Provide 3-7 tags that represent the main topics.
                Tags should be in English and specific but not overly technical.
                """,
                
                'content_summary': """
                Provide a concise summary of this English article.
                The summary should capture the main points in 2-3 sentences.
                """
            }
    
    def get_supported_languages(self) -> Dict[str, Dict[str, Any]]:
        """Get information about supported languages"""
        return {
            lang_code: {
                'name': config['name'],
                'min_content_length': config['min_content_length'],
                'max_content_length': config['max_content_length'],
                'stop_word_count': len(config['stop_words']),
                'pattern_count': len(config['common_patterns'])
            }
            for lang_code, config in self.language_config.items()
        }
    
    def test_language_detection(self, test_texts: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
        """Test language detection with sample texts"""
        results = {}
        
        for label, text in test_texts.items():
            detected_lang, confidence = self.detect_language(text)
            results[label] = {
                'text_preview': text[:100] + '...' if len(text) > 100 else text,
                'detected_language': detected_lang,
                'confidence': confidence,
                'supported': detected_lang in self.supported_languages
            }
        
        return results