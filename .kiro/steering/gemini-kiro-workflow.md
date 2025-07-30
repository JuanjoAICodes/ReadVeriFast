# Gemini-Kiro Workflow Integration

This project uses a unified workflow that supports both Kiro IDE and Gemini CLI users working together seamlessly.

## Multi-Developer Coordination Rules

### Spec-Based Development
- Always start with specifications before writing code
- Use three-stage process: requirements.md → design.md → tasks.md
- Each developer works on different specs simultaneously to prevent conflicts
- Communicate through documentation rather than external channels

### File Structure Standards
All specs must follow this structure:
```
.kiro/specs/feature-name/
├── requirements.md    # EARS format requirements
├── design.md         # Technical architecture
└── tasks.md          # Kiro checkbox format tasks
```

### Task Format Requirements
Use Kiro-compatible checkbox format:
```markdown
- [ ] 1. Create authentication models
  - Implement CustomUser model with required fields
  - Add authentication middleware configuration
  - _Requirements: 1.1, 1.2_
```

## Code Generation Guidelines

### For All AI Assistants
- Generated code serves as a starting point requiring human review
- Always include proper error handling and validation
- Follow Django best practices and VeriFast patterns
- Include comprehensive docstrings and comments
- Ensure code integrates with existing XP system and tag analytics

### Database Operations
- Create migrations in separate feature branches
- Test migrations with `python manage.py migrate --dry-run`
- Coordinate migration dependencies carefully
- Use squash migrations for complex features

### Integration Requirements
- All new features must integrate with existing XP system
- Follow established patterns in `verifast_app/models.py`
- Use existing services in `xp_system.py` and `tag_analytics.py`
- Maintain compatibility with PicoCSS frontend framework

## Quality Standards

### Code Review Checklist
- [ ] Follows Django naming conventions
- [ ] Includes proper model field help_text
- [ ] Uses appropriate database indexes
- [ ] Integrates with XP transaction system
- [ ] Maintains backward compatibility
- [ ] Includes relevant tests

### Documentation Requirements
- Update relevant specs when implementation differs from design
- Keep task status current ([ ], [~], [x])
- Document any architectural decisions or trade-offs
- Update API documentation for new endpoints

## Collaboration Patterns

### Conflict Prevention
- Check active specs before starting work: `ls .kiro/specs/*/tasks.md | xargs grep "in_progress"`
- Claim specs by updating ASSIGNED.md files
- Use feature branches for all development
- Coordinate through shared steering rules and hooks

### Integration Points
- XP System: Use `XPTransactionManager` for all XP operations
- Tag System: Validate tags through Wikipedia API integration
- Quiz System: Follow existing Gemini API patterns
- User System: Extend `CustomUser` model appropriately

This steering ensures consistent development practices whether using Kiro IDE or Gemini CLI.