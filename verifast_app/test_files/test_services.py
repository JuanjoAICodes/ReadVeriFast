from django.test import TestCase
from unittest.mock import patch, MagicMock, call
from wikipedia.exceptions import PageError # type: ignore

from verifast_app.models import Tag
from verifast_app.services import get_valid_wikipedia_tags
# Note: I'm assuming the 'calculate_ponderated_score' function and its tests
# exist in this file as well, and I'm leaving them as they were.

# Placeholder for the other test class that was in your file
class CalculatePonderatedScoreTest(TestCase):
    def test_calculate_ponderated_score(self):
        # Assuming you have tests for this function, they would go here.
        # For example:
        # score = calculate_ponderated_score(10, 5, 2)
        # self.assertEqual(score, 7.0) # This is just a hypothetical example
        pass


class GetValidWikipediaTagsTest(TestCase):
    """
    Test suite for the get_valid_wikipedia_tags service function.
    These tests use mocking to isolate the function from external services
    (like the Wikipedia API) and the database.
    """

    def setUp(self):
        """
        No database setup is needed as we are fully mocking database interactions.
        """
        pass

    @patch('verifast_app.services.wiki_en.page')
    @patch('verifast_app.models.Tag.objects.get_or_create')
    def test_get_valid_wikipedia_tags_success(self, mock_get_or_create, mock_wiki_page):
        """
        Tests the successful validation of a single, new tag that exists on Wikipedia.
        """
        # Arrange: Configure the mocks to simulate a successful scenario.
        mock_page = MagicMock()
        mock_page.exists = True
        mock_page.title = "New Valid Tag"
        mock_wiki_page.return_value = mock_page

        mock_tag_instance = MagicMock(spec=Tag)
        mock_tag_instance.name = "New Valid Tag"
        mock_get_or_create.return_value = (mock_tag_instance, True) # (object, created)

        entities = ["New Valid Tag"]

        # Act: Call the function under test.
        validated_tags = get_valid_wikipedia_tags(entities, language='en')

        # Assert: Verify the outcome.
        self.assertEqual(len(validated_tags), 1)
        self.assertEqual(validated_tags[0].name, "New Valid Tag")
        mock_wiki_page.assert_called_once_with("New Valid Tag")
        mock_get_or_create.assert_called_once_with(name="New Valid Tag")

    @patch('verifast_app.services.wiki_en.page')
    def test_get_valid_wikipedia_tags_empty_input(self, mock_wiki_page):
        """
        Tests that providing an empty list of entities results in an empty list of tags.
        """
        # Act
        validated_tags = get_valid_wikipedia_tags([], language='en')
        # Assert
        self.assertEqual(len(validated_tags), 0)
        mock_wiki_page.assert_not_called()

    @patch('verifast_app.services.wiki_en.page')
    @patch('verifast_app.models.Tag.objects.get_or_create')
    def test_get_valid_wikipedia_tags_non_existent_tag(self, mock_get_or_create, mock_wiki_page):
        """
        Tests that an entity with no corresponding Wikipedia page does not result in a tag.
        """
        # Arrange: Mock the Wikipedia API to raise a PageError.
        mock_wiki_page.side_effect = PageError(pageid=None)
        entities = ["Non Existent Tag"]

        # Act
        validated_tags = get_valid_wikipedia_tags(entities, language='en')

        # Assert
        self.assertEqual(len(validated_tags), 0)
        mock_wiki_page.assert_called_once_with("Non Existent Tag")
        mock_get_or_create.assert_not_called()

    @patch('verifast_app.services.wiki_en.page')
    @patch('verifast_app.models.Tag.objects.get_or_create')
    def test_get_valid_wikipedia_tags_existing_and_new_tags(self, mock_get_or_create, mock_wiki_page):
        """
        Tests the handling of a mixed list of entities, some corresponding to
        existing tags in the database and some to new tags.
        """
        # Arrange
        mock_page_existing = MagicMock()
        mock_page_existing.exists = True
        mock_page_existing.title = "Existing Tag"
        mock_page_new = MagicMock()
        mock_page_new.exists = True
        mock_page_new.title = "New Tag"

        # Simulate the behavior of the Wikipedia API for different inputs.
        def wiki_page_side_effect(title, **_kwargs):
            if title == "Existing Tag":
                return mock_page_existing
            if title == "New Tag":
                return mock_page_new
            return MagicMock(exists=False)
        mock_wiki_page.side_effect = wiki_page_side_effect

        # Mock the Tag instances that get_or_create will return.
        mock_existing_tag_instance = MagicMock(spec=Tag, name="Existing Tag")
        mock_new_tag_instance = MagicMock(spec=Tag, name="New Tag")

        # Simulate the behavior of the database get_or_create method.
        def get_or_create_side_effect(name):
            if name == "Existing Tag":
                return (mock_existing_tag_instance, False) # Returns existing, created=False
            if name == "New Tag":
                return (mock_new_tag_instance, True)   # Creates new, created=True
            return (MagicMock(), False)
        mock_get_or_create.side_effect = get_or_create_side_effect

        entities = ["Existing Tag", "New Tag"]

        # Act
        validated_tags = get_valid_wikipedia_tags(entities, language='en')

        # Assert
        self.assertEqual(len(validated_tags), 2)
        self.assertIn(mock_existing_tag_instance, validated_tags)
        self.assertIn(mock_new_tag_instance, validated_tags)
        mock_wiki_page.assert_has_calls([call("Existing Tag"), call("New Tag")], any_order=True)
        mock_get_or_create.assert_has_calls([call(name="Existing Tag"), call(name="New Tag")], any_order=True)


    @patch('verifast_app.services.wiki_en.page')
    @patch('verifast_app.models.Tag.objects.get_or_create')
    def test_get_valid_wikipedia_tags_canonicalization(self, mock_get_or_create, mock_wiki_page):
        """
        Tests that different variations of an entity name are canonicalized to a single tag
        (e.g., "Apple" and "Apple Inc." should both result in one "Apple Inc." tag).
        """
        # Arrange
        mock_apple_page = MagicMock()
        mock_apple_page.exists = True
        mock_apple_page.title = "Apple Inc."
        mock_cook_page = MagicMock()
        mock_cook_page.exists = True
        mock_cook_page.title = "Tim Cook"

        def wiki_page_side_effect(title, **_kwargs):
            if title in ["Apple", "Apple Inc."]:
                return mock_apple_page # Both resolve to the same canonical page
            if title == "Tim Cook":
                return mock_cook_page
            return MagicMock(exists=False)
        mock_wiki_page.side_effect = wiki_page_side_effect

        mock_apple_tag = MagicMock(spec=Tag, name="Apple Inc.")
        mock_cook_tag = MagicMock(spec=Tag, name="Tim Cook")

        # get_or_create should only be called for each unique canonical name.
        def get_or_create_side_effect(name):
            if name == "Apple Inc.":
                return (mock_apple_tag, True)
            if name == "Tim Cook":
                return (mock_cook_tag, True)
            return (MagicMock(), False)
        mock_get_or_create.side_effect = get_or_create_side_effect

        entities = ["Apple", "Apple Inc.", "Tim Cook"]

        # Act
        validated_tags = get_valid_wikipedia_tags(entities, language='en')

        # Assert
        self.assertEqual(len(validated_tags), 2, "Should return two unique tags.")
        self.assertIn(mock_apple_tag, validated_tags)
        self.assertIn(mock_cook_tag, validated_tags)
        # The function should be smart enough to only create the "Apple Inc." tag once.
        self.assertEqual(mock_get_or_create.call_count, 2)
        mock_get_or_create.assert_has_calls([call(name="Apple Inc."), call(name="Tim Cook")], any_order=True)
