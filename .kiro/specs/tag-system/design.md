
# Tag System Design - Wikipedia Article Processing Pipeline

## 1. Overview

This document outlines the necessary changes to integrate the existing `process_wikipedia_article` task into the main article processing pipeline. The goal is to ensure that when a new article with `article_type='wikipedia'` is created, it is correctly processed using the specialized pipeline.

## 2. Current Implementation

The `verifast_app/tasks.py` file contains two relevant tasks:

- `process_article`: The main task for processing user-submitted articles. It handles NLP analysis, reading level calculation, dynamic model selection, and quiz/tag generation.
- `process_wikipedia_article`: A specialized task for processing articles sourced from Wikipedia. It has slightly different logic for reading level, model selection, and tag handling.

Currently, the `process_article` task does not differentiate between article types and therefore does not delegate to `process_wikipedia_article`.

## 3. Proposed Changes

The `process_article` task will be modified to act as a dispatcher based on the `article_type` field of the `Article` model.

### 3.1. `process_article` Task Modification

The `process_article` task in `verifast_app/tasks.py` will be updated as follows:

1.  **Fetch Article:** The task will fetch the `Article` object as it currently does.
2.  **Check `article_type`:** It will then inspect the `article.article_type` field.
3.  **Delegate or Process:**
    - If `article.article_type == 'wikipedia'`, the task will immediately call `process_wikipedia_article.delay(article.id)` and terminate its own execution for that article.
    - Otherwise (if the `article_type` is `'regular'` or another default value), it will proceed with its existing processing logic.

This change ensures that Wikipedia articles are routed to the correct, specialized processing pipeline while regular articles are handled as before.

## 4. Rationale

This approach offers several advantages:

- **Simplicity:** It requires a minimal change to the existing codebase.
- **Maintainability:** It keeps the logic for different article types separate and clean. The `process_article` task becomes a simple dispatcher, and the specialized logic remains encapsulated in `process_wikipedia_article`.
- **Robustness:** It leverages the existing, specialized `process_wikipedia_article` task, which is already designed to handle the nuances of Wikipedia content.

## 5. Task Breakdown

The implementation will be broken down into the following tasks, which will be added to `tasks.md`:

- **TASK-013.1:** Modify `process_article` to delegate based on `article_type`.
- **TASK-013.2:** Add unit tests to verify the new dispatching logic.

## 6. Error Handling for Wikipedia API Interactions

### 6.1. Overview

This section details enhancements to error handling within the `get_valid_wikipedia_tags` function in `verifast_app/services.py`. The goal is to improve the robustness of Wikipedia API calls, particularly for transient network issues and unexpected responses.

### 6.2. Proposed Changes

1.  **Retry Mechanism:** A simple retry mechanism will be implemented for Wikipedia API calls. This will involve:
    -   A maximum number of retries (e.g., 3).
    -   A short delay between retries (e.g., 1 second), potentially with exponential backoff.
    -   Targeting specific exceptions for retries (e.g., network-related errors, HTTP 5xx errors if the `wikipediaapi` library exposes them).
2.  **Specific Exception Handling:** While `wikipediaapi.exceptions.PageError` and `wikipediaapi.exceptions.DisambiguationError` are already handled, the general `Exception` block will be refined to provide more specific logging and potentially differentiate between various types of unexpected errors.
3.  **Input Validation:** Basic validation for the `entities` list will be added to ensure it contains valid string inputs, preventing potential errors before API calls are made.

### 6.3. Rationale

-   **Increased Reliability:** Retries will make the tag validation process more resilient to temporary network glitches or API rate limits.
-   **Improved Diagnostics:** More specific error handling will provide clearer logs, aiding in debugging and troubleshooting.
-   **Enhanced Robustness:** Input validation will prevent common errors and ensure the function operates on expected data types.

## 7. Comprehensive Testing Suite for Tag System

### 7.1. Overview

This section outlines the plan for creating a comprehensive testing suite for the tag system, with a primary focus on the `get_valid_wikipedia_tags` function in `verifast_app/services.py`. The tests will cover various scenarios, including successful API calls, edge cases, and error handling.

### 7.2. Proposed Tests

1.  **`test_get_valid_wikipedia_tags_success`:**
    -   **Scenario:** Valid entity names are provided, and the Wikipedia API returns existing pages.
    -   **Expected Behavior:** The function should return a list of `Tag` objects, and new tags should be created in the database if they don't already exist. The Wikipedia API should be called for each unique entity.
2.  **`test_get_valid_wikipedia_tags_empty_input`:**
    -   **Scenario:** An empty list or a list containing empty strings is provided as input.
    -   **Expected Behavior:** The function should return an empty list, and no API calls or database operations should occur.
3.  **`test_get_valid_wikipedia_tags_invalid_input`:**
    -   **Scenario:** Input contains non-string types (e.g., numbers, None).
    -   **Expected Behavior:** The function should gracefully handle these inputs (e.g., skip them with a warning), and only process valid strings.
4.  **`test_get_valid_wikipedia_tags_page_not_found`:**
    -   **Scenario:** Entity names are provided, but the Wikipedia API indicates that the pages do not exist.
    -   **Expected Behavior:** The function should not create `Tag` objects for non-existent pages, and appropriate warnings should be logged.
5.  **`test_get_valid_wikipedia_tags_disambiguation_error`:**
    -   **Scenario:** Entity names lead to a Wikipedia disambiguation page.
    -   **Expected Behavior:** The function should handle the `DisambiguationError` gracefully (e.g., skip the entity or log a warning), and not create a `Tag` object for the ambiguous term.
6.  **`test_get_valid_wikipedia_tags_api_error_retry`:**
    -   **Scenario:** The Wikipedia API encounters a transient error (e.g., network issue) that triggers the retry mechanism.
    -   **Expected Behavior:** The function should retry the API call a specified number of times before failing, and appropriate errors should be logged.
7.  **`test_get_valid_wikipedia_tags_api_error_no_retry`:**
    -   **Scenario:** The Wikipedia API encounters a non-transient error (e.g., invalid API key, HTTP 4xx) that should not trigger retries.
    -   **Expected Behavior:** The function should log the error and not retry the API call.
8.  **`test_get_valid_wikipedia_tags_existing_tags`:**
    -   **Scenario:** Some entity names already exist as `Tag` objects in the database.
    -   **Expected Behavior:** The function should retrieve existing `Tag` objects from the database instead of creating duplicates, and the Wikipedia API should not be called for these existing tags.

### 7.3. Implementation Details

-   Tests will be placed in `verifast_app/test_files/test_services.py`.
-   The `wikipediaapi.Wikipedia` and `wikipediaapi.WikipediaPage` objects will be mocked to control API responses and avoid actual network calls during testing.
-   `patch` will be used to mock `Tag.objects.get_or_create` to verify database interactions.
-   Assertions will verify return values, database state, and logger output.
