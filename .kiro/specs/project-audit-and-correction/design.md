# Audit and Correction Design

This document outlines the execution plan for the project-wide standards audit.

## Guiding Principles
- **Safety:** The process is iterative and applies minimal viable changes to prevent unintended side effects.
- **Audibility:** Every action is tracked in `tasks.md`.
- **Efficiency:** Hooks are applied in a logical order to prevent redundant work or conflicts.

## Optimized Hook Execution Order
The audit will be performed hook-by-hook in the following sequence:

1.  **Foundational Correctness (Syntax & Style):**
    - `python-code-quality.kiro.hook`
    - `template-validation-hook.kiro.hook`
    - *Reasoning: Ensures code is syntactically valid before logical analysis.*

2.  **Schema & Structure:**
    - `django-migration-hook.kiro.hook`
    - *Reasoning: Ensures database models are sound before modifying dependent logic.*

3.  **Business Logic & Internationalization:**
    - `i18n-localization-hook.kiro.hook`
    - `xp-validation-hook.kiro.hook`
    - *Reasoning: Modifies application logic on a syntactically correct and structurally sound base.*

4.  **Documentation (Final Step):**
    - `api-docs-sync.kiro.hook`
    - *Reasoning: Documents the final, corrected state of the code.*

## Execution Workflow
For each hook, the system will identify all matching files and process them one by one. For each file, it will:
1. Read the file's content.
2. Analyze it against the hook's rules.
3. If non-compliant, write the full, corrected content back to the file.
4. Mark the corresponding task in `tasks.md` as complete.
