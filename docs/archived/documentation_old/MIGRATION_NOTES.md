# Migration Notes (2025-08-19)

This document summarizes recent behavioral and implementation changes affecting Speed Reader, Quiz, Comments, and Guest interactions, along with configuration notes.

## Summary of Changes

1) Comments unlock threshold aligned to ≥ 60%
- All checks for commenting now use `score >= 60`.
- Quiz results partial triggers an HTMX event `quiz-passed` to refresh the comments section without a full page reload.

2) Anonymous (Guest) Comments After Pass
- Anonymous users who pass the quiz (≥ 60%) can comment.
- Guest form requires a display name; comments are attributed internally to a dedicated `guest` account and appear prefixed with `[Guest: Name]`.
- A signed cookie `vf_guest_name` stores the guest display name for 30 days (renewed on post).
- Throttling: simple per-session limiter (max 5 comments per 10 minutes for guests).

3) Speed Reader Power-Ups Ownership Check
- Power-up checks now use `PremiumFeatureStore.user_owns_feature` rather than user boolean flags.
- This aligns staff/admin ownership and purchased features without manual booleans.

4) Quiz Options Normalization
- QuizStartView normalizes quiz options to string format, supporting both `"string"` and `{ "text": "..." }` formats.

5) Comments Section HTMX Refresh

6) Content Motor: Always Scrape Full Articles with Newspaper3k
- RSS/API providers are treated as discovery only. We do not persist summaries/snippets.
- Orchestrator scrapes the full article from `dto.url` before saving; rejects items with content shorter than a configurable minimum (default 300 words).
- Rationale: ensures consistent full-text articles; avoids short content leaking into DB.

- New endpoint `comments/section/<article_id>/` re-renders the comments block (form + list) on `quiz-passed`.
- New partial `partials/comments_section.html` consolidates form and list rendering.

## Configuration Notes

- Pydantic Settings: list-type env vars must be JSON arrays or use indexed env vars (e.g., `ALLOWED_HOSTS__0=...`).
- API Base Path: `/api/v1/` is the canonical base for DRF routes.

## Action Items for DevOps/Team

- Ensure a non-privileged `guest` user exists in production (the system will auto-create if missing, but consider setting a non-sensitive random password and monitoring usage).
- Consider adding IP-based throttling or WAF rules if anonymous comments become high volume.
- If legacy JavaScript assets are deployed, validate they are not referenced; HTMX server rendering is the current path.
- Align documentation: update mentions of 70% thresholds to 60%; ensure anonymous comment flow is documented.

## Testing Checklist

- Auth user: read → pass quiz (≥60) → comment form appears without full reload → a comment posts (XP cost or free at 100%).
- Guest user: read → pass quiz (≥60) → guest form appears → enter name + comment → comment appears with `[Guest: Name]` prefix → subsequent comments prefill name.
- Speed Reader: verify owned features (admin/purchased) trigger chunking/smart features.
- Quiz: mixed option schemas render and grade correctly.

## Rollback

- Revert to prior commit/branch and remove:
  - New view `CommentsSectionView` and route.
  - Guest cookie read/write and throttling.
  - `process_content_with_powerups` ownership check change.
  - Quiz options normalization.

