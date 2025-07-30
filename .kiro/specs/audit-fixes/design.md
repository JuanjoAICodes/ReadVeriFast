
# Design Document: Project Audit and Code Quality Fixes

## 1. Fix Undefined Name Errors in `xp_system.py`

*   **Problem:** The file `verifast_app/xp_system.py` contains several `F821` "Undefined name" errors related to the `models` module.
*   **Solution:**
    1.  Import `Sum` and `Avg` from `django.db.models`.
    2.  Replace all instances of `models.Sum` with `Sum`.
    3.  Replace all instances of `models.Avg` with `Avg`.

## 2. Fix Undefined Name Errors in `views.py`

*   **Problem:** The file `verifast_app/views.py` contains an `F821` "Undefined name" error related to the `models` module.
*   **Solution:**
    1.  Import `Max` from `django.db.models`.
    2.  Replace `models.Max` with `Max`.

## 3. Fix Unused Imports

*   **Problem:** The project has a large number of unused imports (`F401` errors).
*   **Solution:** Run `ruff --fix` to automatically remove all unused imports.

## 4. Fix Other Linting Errors

*   **Problem:** The project has a number of other linting errors, such as multiple statements on one line and module-level imports not at the top of the file.
*   **Solution:** Run `ruff --fix` to automatically fix these errors where possible. Manually fix any remaining errors.
