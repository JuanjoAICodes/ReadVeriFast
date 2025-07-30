# Documentation Maintenance Guidelines

*Last Updated: July 21, 2025*
*Status: Current*

## Overview

This guide establishes processes and standards for maintaining accurate, current, and useful documentation throughout the VeriFast project lifecycle. Following these guidelines ensures documentation remains a valuable development resource.

## Core Principles

### 1. Documentation-First Development
- **Update docs before code** when possible
- **Document decisions** as they're made
- **Keep specs current** with implementation
- **Review docs** during code reviews

### 2. Single Source of Truth
- **One authoritative document** per topic
- **Clear ownership** of each document
- **Consistent cross-references** between documents
- **Archive outdated content** rather than deleting

### 3. User-Focused Content
- **Write for the reader** not the writer
- **Include practical examples** and code snippets
- **Test instructions** before publishing
- **Gather feedback** from documentation users

## Maintenance Workflows

### When Code Changes

#### Feature Development
```bash
# 1. Update or create spec first
.kiro/specs/feature-name/
├── requirements.md    # Update requirements
├── design.md         # Update design
└── tasks.md          # Update implementation tasks

# 2. Update feature documentation
documentation/features/feature-name.md

# 3. Update API documentation if needed
documentation/api/specification.md

# 4. Update architecture docs if needed
documentation/architecture/overview.md
```

#### Bug Fixes
```bash
# 1. Document the issue and solution
# 2. Update relevant feature documentation
# 3. Update troubleshooting sections
# 4. Consider if architecture docs need updates
```

#### Refactoring
```bash
# 1. Update technical specifications
# 2. Update code examples in documentation
# 3. Update setup/development guides if needed
# 4. Update API documentation for interface changes
```

### Regular Maintenance Schedule

#### Weekly Tasks
- [ ] Review recent commits for documentation impacts
- [ ] Check for broken internal links
- [ ] Update project status if significant progress made
- [ ] Review and respond to documentation feedback

#### Monthly Tasks
- [ ] Comprehensive link validation across all docs
- [ ] Review documentation metrics and usage
- [ ] Update screenshots and UI examples
- [ ] Archive outdated session notes and temporary docs

#### Quarterly Tasks
- [ ] Full documentation audit and accuracy review
- [ ] Update development roadmap and project status
- [ ] Review and update maintenance guidelines
- [ ] Consolidate and organize accumulated documentation

## Documentation Standards

### File Organization
```
documentation/
├── README.md                    # Documentation hub
├── setup/                      # Installation and setup
├── architecture/               # System design
├── features/                   # Feature documentation
├── api/                        # API reference
├── development/                # Development guides
├── sessions/                   # Session notes (dated)
└── archived/                   # Historical content
    └── YYYY-MM-DD-reason/      # Dated archive folders
```

### Naming Conventions
- **Files:** `kebab-case.md` (e.g., `user-management.md`)
- **Directories:** `lowercase` (e.g., `features/`, `api/`)
- **Archives:** `YYYY-MM-DD-reason/` (e.g., `2025-07-21-consolidation/`)
- **Session Notes:** `YYYY-MM-DD-session-name.md`

### Document Structure
```markdown
# Document Title
*Last Updated: YYYY-MM-DD*
*Status: Current | Draft | Deprecated*

## Overview
Brief description of the document's purpose

## Main Content Sections
Organized content with consistent formatting

## Related Documentation
Links to related documents

## Changelog (for major documents)
- YYYY-MM-DD: Description of changes
```

### Content Standards
- **Headings:** Use consistent hierarchy (H1 for title, H2 for main sections)
- **Code Blocks:** Always specify language for syntax highlighting
- **Links:** Use relative paths for internal documentation
- **Status Indicators:** Include last updated date and current status
- **Examples:** Provide working, tested examples

## Quality Assurance

### Documentation Review Checklist

#### Content Review
- [ ] **Accuracy:** Information matches current implementation
- [ ] **Completeness:** All necessary information included
- [ ] **Clarity:** Content is clear and understandable
- [ ] **Examples:** Code examples work and are current
- [ ] **Links:** All internal links work correctly

#### Format Review
- [ ] **Structure:** Consistent heading hierarchy
- [ ] **Formatting:** Proper markdown formatting
- [ ] **Code Blocks:** Language specified for syntax highlighting
- [ ] **Status:** Last updated date and status included
- [ ] **Cross-references:** Related documentation linked

#### Technical Review
- [ ] **Setup Instructions:** Actually work on clean environment
- [ ] **Code Examples:** Run without errors
- [ ] **API Documentation:** Matches actual endpoints
- [ ] **Configuration:** Settings and options are current

### Link Validation Process
```bash
# Manual link checking
grep -r "\[.*\](.*\.md" documentation/ | grep -v "http"

# Automated link validation (if tool available)
markdown-link-check documentation/**/*.md

# Test setup instructions
# Follow setup guide on clean system to verify accuracy
```

## Change Management

### Documentation Updates

#### Minor Updates
- **Typo fixes** - Direct edit with commit message
- **Link updates** - Fix broken links immediately
- **Small clarifications** - Update with brief explanation

#### Major Updates
- **New features** - Create/update feature documentation
- **Architecture changes** - Update architecture docs and related content
- **API changes** - Update API documentation and examples
- **Process changes** - Update development and setup guides

### Version Control
```bash
# Commit messages for documentation
git commit -m "docs: update XP system documentation for new features"
git commit -m "docs: fix broken links in setup guide"
git commit -m "docs: archive outdated session notes"

# Branch strategy for major doc updates
git checkout -b docs/major-update-description
# Make changes
git commit -m "docs: comprehensive update to feature documentation"
# Create PR for review
```

### Archive Management

#### When to Archive
- **Outdated Information** - Content no longer accurate
- **Superseded Documents** - Replaced by newer documentation
- **Temporary Content** - Session notes older than 6 months
- **Conflicting Information** - Documents that contradict current docs

#### Archive Process
```bash
# 1. Create archive directory
mkdir -p documentation/archived/YYYY-MM-DD-reason/

# 2. Move files with context
mv outdated-file.md documentation/archived/YYYY-MM-DD-reason/

# 3. Update archive README
# Add entry to documentation/archived/YYYY-MM-DD-reason/README.md

# 4. Create redirect note if needed
echo "This content has been moved to [new location](path/to/new/doc.md)" > old-location.md

# 5. Update cross-references
# Find and update any links to archived content
```

## Templates and Tools

### New Document Template
```markdown
# Document Title

*Last Updated: YYYY-MM-DD*
*Status: Draft*

## Overview

Brief description of what this document covers and who should read it.

## Prerequisites

What the reader should know or have set up before reading this document.

## Main Content

Organized sections with clear headings and practical examples.

## Examples

Working code examples with explanations.

## Troubleshooting

Common issues and their solutions.

## Related Documentation

- [Related Doc 1](path/to/doc1.md)
- [Related Doc 2](path/to/doc2.md)

## Changelog

- YYYY-MM-DD: Initial version
```

### Useful Commands
```bash
# Find all markdown files
find . -name "*.md" -type f

# Search for broken internal links
grep -r "\[.*\](.*\.md" . | grep -v "http" | grep -v "node_modules"

# Count documentation files
find documentation/ -name "*.md" | wc -l

# Find files without last updated date
grep -L "Last Updated:" documentation/**/*.md

# Find large files that might need splitting
find documentation/ -name "*.md" -exec wc -l {} + | sort -n
```

## Metrics and Monitoring

### Documentation Health Metrics
- **Link Health** - Percentage of working internal links
- **Freshness** - Percentage of docs updated in last 3 months
- **Coverage** - Features with complete documentation
- **Usage** - Most accessed documentation pages

### Regular Health Checks
```bash
# Weekly health check script
#!/bin/bash

echo "Documentation Health Check - $(date)"
echo "=================================="

# Count total docs
total_docs=$(find documentation/ -name "*.md" | wc -l)
echo "Total documentation files: $total_docs"

# Check for docs without recent updates
old_docs=$(find documentation/ -name "*.md" -mtime +90 | wc -l)
echo "Files not updated in 90 days: $old_docs"

# Check for broken internal links (basic check)
broken_links=$(grep -r "\[.*\](.*\.md" documentation/ | grep -v "http" | wc -l)
echo "Internal markdown links found: $broken_links"

echo "=================================="
```

## Team Collaboration

### Documentation Ownership
- **Feature Docs** - Feature developer maintains
- **API Docs** - Backend team maintains
- **Setup Docs** - DevOps/Infrastructure team maintains
- **Architecture Docs** - Tech lead maintains

### Review Process
1. **Author** creates or updates documentation
2. **Peer Review** by team member familiar with topic
3. **Technical Review** by subject matter expert
4. **Final Review** by documentation maintainer
5. **Merge** after all reviews pass

### Communication
- **Document changes** in team updates
- **Request feedback** on new documentation
- **Share documentation wins** and improvements
- **Escalate issues** with outdated or confusing docs

## Related Documentation
- [Development Setup](../setup/development.md) - Development environment
- [Testing Guide](testing.md) - Testing documentation
- [GEMINI_KIRO_WORKFLOW.md](../../GEMINI_KIRO_WORKFLOW.md) - Multi-developer collaboration