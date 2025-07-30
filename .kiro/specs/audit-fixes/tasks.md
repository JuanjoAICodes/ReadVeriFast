
# Implementation Tasks: Project Audit and Code Quality Fixes

- [x] 1. Fix undefined name errors in `verifast_app/xp_system.py`.
  - [x] 1.1. Import `Sum` and `Avg` from `django.db.models`.
  - [x] 1.2. Replace `models.Sum` with `Sum`.
  - [x] 1.3. Replace `models.Avg` with `Avg`.
- [x] 2. Fix undefined name errors in `verifast_app/views.py`.
  - [x] 2.1. Import `Max` from `django.db.models`.
  - [x] 2.2. Replace `models.Max` with `Max`.
- [x] 3. Fix all remaining linting and type errors automatically.
  - [x] 3.1. Run `ruff --fix .`
  - [x] 3.2. Run `mypy .` and fix any remaining errors.
