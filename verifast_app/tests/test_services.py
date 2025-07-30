from unittest.mock import patch, MagicMock
from django.test import TestCase

from verifast_app.services import (
    generate_master_analysis,
    analyze_text_content,
    get_valid_wikipedia_tags
)


class TestServices(TestCase):
    """Test restored AI/NLP services"""
    
    @patch('verifast_app.services.genai')
    def test_generate_master_analysis_success(self, mock_genai):
        """Test successful AI analysis"""
        # Setup mock
        mock_response = MagicMock()
        mock_response.text = '''{
            "quiz": [
                {
                    "question": "This is a test question?",
                    "options": [{"text": "A"}, {"text": "B"}, {"text": "C"}, {"text": "D"}],
                    "correct_answer": 0,
                    "explanation": "This is the explanation."
                }
            ],
            "tags": ["test", "pydantic"]
        }'''
        mock_chat = MagicMock()
        mock_chat.send_message.return_value = mock_response
        mock_model = MagicMock()
        mock_model.start_chat.return_value = mock_chat
        mock_genai.GenerativeModel.return_value = mock_model
        
        # Call function
        result = generate_master_analysis("test-model", ["entity"], "test content")
        
        # Verify results
        self.assertIn('quiz', result)
        self.assertIn('tags', result)
        self.assertEqual(len(result['quiz']), 1)
        self.assertEqual(result['quiz'][0]['question'], "This is a test question?")
        self.assertEqual(len(result['quiz'][0]['options']), 4)
        self.assertEqual(result['quiz'][0]['options'][0]['text'], "A")
        self.assertEqual(result['tags'], ["test", "pydantic"])
        mock_genai.GenerativeModel.assert_called_once()
    
    @patch('verifast_app.services.genai')
    def test_generate_master_analysis_json_error(self, mock_genai):
        """Test handling of invalid JSON response"""
        # Setup mock with invalid JSON
        mock_response = MagicMock()
        mock_response.text = 'invalid json'
        mock_chat = MagicMock()
        mock_chat.send_message.return_value = mock_response
        mock_model = MagicMock()
        mock_model.start_chat.return_value = mock_chat
        mock_genai.GenerativeModel.return_value = mock_model
        
        # Call function
        result = generate_master_analysis("test-model", ["entity"], "test content")
        
        # Verify fallback behavior
        self.assertEqual(result, {'quiz': [], 'tags': []})
    
    @patch('verifast_app.services.nlp_en')
    def test_analyze_text_content_success(self, mock_nlp):
        """Test NLP analysis with entities"""
        # Setup mock
        mock_doc = MagicMock()
        mock_ent1 = MagicMock()
        mock_ent1.text = "John Doe"
        mock_ent1.label_ = "PERSON"
        mock_ent2 = MagicMock()
        mock_ent2.text = "Google"
        mock_ent2.label_ = "ORG"
        mock_ent3 = MagicMock()
        mock_ent3.text = "$100"
        mock_ent3.label_ = "MONEY"
        mock_doc.ents = [mock_ent1, mock_ent2, mock_ent3]
        mock_nlp.return_value = mock_doc
        
        # Call function
        result = analyze_text_content("This is a test about John Doe and Google spending $100.")
        
        # Verify results
        self.assertIn('reading_score', result)
        self.assertIn('people', result)
        self.assertIn('organizations', result)
        self.assertIn('money_mentions', result)
        self.assertIn('John Doe', result['people'])
        self.assertIn('Google', result['organizations'])
        self.assertIn('$100', result['money_mentions'])
    
    @patch('verifast_app.services.textstat')
    @patch('verifast_app.services.nlp_en')
    def test_analyze_text_content_textstat_error(self, mock_nlp, mock_textstat):
        """Test handling of textstat errors"""
        # Setup mocks
        mock_doc = MagicMock()
        mock_doc.ents = []
        mock_nlp.return_value = mock_doc
        mock_textstat.flesch_kincaid_grade.side_effect = KeyError("test error")
        
        # Call function
        result = analyze_text_content("Test text")
        
        # Verify fallback behavior
        self.assertEqual(result['reading_score'], 0)
        self.assertEqual(result['people'], [])
        self.assertEqual(result['organizations'], [])
        self.assertEqual(result['money_mentions'], [])
    
    @patch('verifast_app.services.wiki_en')
    def test_get_valid_wikipedia_tags_success(self, mock_wiki):
        """Test Wikipedia tag validation"""
        # Setup mocks
        mock_page = MagicMock()
        mock_page.exists.return_value = True
        mock_page.title = "Python (programming language)"
        mock_wiki.page.return_value = mock_page
        
        # Call function
        result = get_valid_wikipedia_tags(["Python"])
        
        # Verify results
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "Python (programming language)")
        mock_wiki.page.assert_called_once_with("Python")
    
    @patch('verifast_app.services.wiki_en')
    def test_get_valid_wikipedia_tags_nonexistent(self, mock_wiki):
        """Test handling of non-existent Wikipedia pages"""
        # Setup mock
        mock_page = MagicMock()
        mock_page.exists.return_value = False
        mock_wiki.page.return_value = mock_page
        
        # Call function
        result = get_valid_wikipedia_tags(["NonexistentPage"])
        
        # Verify results
        self.assertEqual(len(result), 0)
    
    def test_get_valid_wikipedia_tags_empty_input(self):
        """Test handling of empty input"""
        result = get_valid_wikipedia_tags([])
        self.assertEqual(len(result), 0)
    
    def test_get_valid_wikipedia_tags_invalid_input(self):
        """Test handling of invalid input"""
        result = get_valid_wikipedia_tags([None, "", "  "])
        self.assertEqual(len(result), 0)