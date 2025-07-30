# Gemini CLI + Kiro Workflow Integration Guide

*Last Updated: July 21, 2025*
*Status: Unified Guide for Multi-Developer Collaboration*

## Overview

This guide enables seamless collaboration between Gemini CLI and Kiro IDE workflows, allowing multiple developers to work on the same project without conflicts while maintaining documentation-driven development standards.

## Core Principles

### 1. Documentation-First Development
- **Always start with specifications** before writing code
- **Three-stage process**: requirements.md → design.md → tasks.md
- **No code without approved specs** - prevents conflicts and ensures alignment

### 2. Multi-Developer Harmony Rules
- **Spec-based coordination** - Each developer works on different specs simultaneously
- **Clear ownership** - One spec = one developer at a time
- **Merge-friendly approach** - Specs prevent code conflicts by design
- **Communication through documentation** - Specs serve as developer communication

## Workflow Integration

### Kiro IDE Users
```bash
# Create new spec
kiro spec create feature-name

# Work on tasks
kiro task start "1. Implement feature X"
kiro task complete "1. Implement feature X"
```

### Gemini CLI Users
```bash
# The ONLY real Gemini CLI command is:
gemini --prompt "your structured prompt here"

# All other examples in this document are conceptual workflows
# You'll use gemini --prompt with carefully structured prompts
```

## Unified Spec Format

### File Structure (Compatible with both tools)
```
.kiro/specs/feature-name/
├── requirements.md    # EARS format requirements
├── design.md         # Technical architecture
└── tasks.md          # Kiro checkbox format tasks
```

### Requirements Format (EARS + Kiro Compatible)
```markdown
# Requirements Document

## Requirement 1: User Authentication

**User Story:** As a user, I want to log in securely, so that I can access personalized features.

#### Acceptance Criteria
1. WHEN a user provides valid credentials THEN the system SHALL authenticate the user
2. WHEN authentication fails THEN the system SHALL display an error message
3. WHEN a user is authenticated THEN the system SHALL redirect to the dashboard
```

### Tasks Format (Kiro + Gemini Compatible)
```markdown
# Implementation Tasks

- [ ] 1. Create authentication models
  - Implement CustomUser model with required fields
  - Add authentication middleware configuration
  - _Requirements: 1.1, 1.2_

- [ ] 2. Implement login views
  - Create login form with validation
  - Add session management
  - _Requirements: 1.3, 1.4_
```

## Multi-Developer Coordination

### Conflict Prevention Strategy

#### 1. Spec-Level Coordination
```bash
# Before starting work, check active specs
ls .kiro/specs/*/tasks.md | xargs grep "in_progress"

# Claim a spec by updating status
echo "Developer: @username" >> .kiro/specs/feature-name/ASSIGNED.md
```

#### 2. File-Level Coordination
- **Models**: One developer per app/model
- **Views**: One developer per feature area
- **Templates**: Coordinate through shared base templates
- **Static files**: Use feature-specific directories

#### 3. Database Coordination
```bash
# Always create migrations in separate branches
git checkout -b feature/your-feature-name
python manage.py makemigrations
# Merge migrations carefully to avoid conflicts
```

**Migration Conflict Resolution Strategies:**

1. **Squash Migrations** (for complex features):
```bash
# After feature completion, squash migrations
python manage.py squashmigrations verifast_app 0001 0005 --squashed-name feature_name
```

2. **Rebase Strategy** (recommended):
```bash
# Before merging, rebase your branch
git checkout main
git pull origin main
git checkout feature/your-feature-name
git rebase main
# Resolve any migration conflicts manually
```

3. **Manual Migration Merge**:
```bash
# If migration conflicts occur, manually edit migration files
# Ensure dependencies are correct in Migration.dependencies
# Test migrations on clean database before pushing
python manage.py migrate --dry-run
```

> **Further Reading**: See Django's [Migration Documentation](https://docs.djangoproject.com/en/stable/topics/migrations/) for advanced conflict resolution techniques.

## How Gemini CLI Works with This Project

**IMPORTANT CLARIFICATION**: Gemini CLI's core command is `gemini --prompt "your prompt here"`. The functions shown below are examples of how to structure prompts for consistency with Kiro workflow - they are NOT built-in commands.

### Real Gemini CLI Usage Pattern
When working with this project, you'll use `gemini --prompt` with structured prompts that reference the actual spec files that Kiro creates.

### Spec Generation
```bash
# Generate complete spec from description
gemini-spec() {
    local feature_name=$1
    local description=$2
    
    if [ -z "$feature_name" ] || [ -z "$description" ]; then
        echo "Usage: gemini-spec <feature_name> <description>"
        return 1
    fi
    
    mkdir -p .kiro/specs/$feature_name
    
    # Generate requirements
    gemini --prompt "Generate requirements.md in EARS format for: $description
    Use Kiro-compatible format with user stories and acceptance criteria.
    Include requirement references for traceability." > .kiro/specs/$feature_name/requirements.md
    
    # Generate design
    gemini --prompt "Generate design.md based on requirements:
    $(cat .kiro/specs/$feature_name/requirements.md)
    Focus on Django architecture and VeriFast project patterns." > .kiro/specs/$feature_name/design.md
    
    # Generate tasks
    gemini --prompt "Generate tasks.md in Kiro checkbox format:
    Requirements: $(cat .kiro/specs/$feature_name/requirements.md)
    Design: $(cat .kiro/specs/$feature_name/design.md)
    Use - [ ] format with requirement references." > .kiro/specs/$feature_name/tasks.md
    
    echo "✅ Spec generated at .kiro/specs/$feature_name/"
}
```

### Task Implementation
```bash
# Implement specific task
gemini-task() {
    local spec_dir=$1
    local task_number=$2
    
    if [ -z "$spec_dir" ] || [ -z "$task_number" ]; then
        echo "Usage: gemini-task <spec_directory> <task_number>"
        return 1
    fi
    
    # Get task details
    local task_details=$(grep -A 5 "^- \[ \] $task_number\." $spec_dir/tasks.md)
    
    # Generate implementation
    gemini --prompt "Implement this task for VeriFast Django project:
    Task: $task_details
    
    Context:
    - Requirements: $(cat $spec_dir/requirements.md)
    - Design: $(cat $spec_dir/design.md)
    - Project structure: Django app with verifast_app/
    
    Generate complete, working code following Django best practices.
    
    IMPORTANT: This code serves as a strong starting point that requires:
    - Human review for business logic accuracy
    - Testing and validation
    - Integration with existing codebase
    - Security and performance considerations"
    
    echo "⚠️  Generated code requires review, testing, and integration before use."
}
```

### Task Status Management
```bash
# Mark task as completed
mark-task-complete() {
    local spec_dir=$1
    local task_number=$2
    
    if [ -z "$spec_dir" ] || [ -z "$task_number" ]; then
        echo "Usage: mark-task-complete <spec_directory> <task_number>"
        echo "Example: mark-task-complete .kiro/specs/user-auth 1"
        return 1
    fi
    
    # Replace [ ] with [x] for the specific task
    sed -i "s/^- \[ \] $task_number\./- [x] $task_number./" $spec_dir/tasks.md
    echo "✅ Task $task_number marked as complete in $spec_dir/tasks.md"
}

# Mark task as in progress
mark-task-progress() {
    local spec_dir=$1
    local task_number=$2
    
    if [ -z "$spec_dir" ] || [ -z "$task_number" ]; then
        echo "Usage: mark-task-progress <spec_directory> <task_number>"
        echo "Example: mark-task-progress .kiro/specs/user-auth 1"
        return 1
    fi
    
    # Replace [ ] with [~] for in-progress tasks
    sed -i "s/^- \[ \] $task_number\./- [~] $task_number./" $spec_dir/tasks.md
    echo "🔄 Task $task_number marked as in progress in $spec_dir/tasks.md"
}
```

## VeriFast Project Context

### Current Architecture
- **Django 4.2+** with Python 3.10+
- **Main app**: `verifast_app/` (models, views, templates)
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Frontend**: HTML5 + CSS3 + Vanilla JS
- **AI Integration**: Google Gemini API
- **External APIs**: Wikipedia API

### Key Systems
- **XP System** (`xp_system.py`) - Gamification and rewards
- **Tag System** (`tag_analytics.py`) - Wikipedia-validated tagging
- **Speed Reader** - Immersive reading interface
- **Quiz System** - AI-generated comprehension tests

### Development Standards
```python
# Model pattern
class ExampleModel(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at.isoformat()
        }

# View pattern
class ExampleView(ListView):
    model = ExampleModel
    template_name = 'app/example_list.html'
    context_object_name = 'examples'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['extra_data'] = 'value'
        return context
```

## Collaboration Workflows

### Scenario 1: Kiro + Gemini on Same Feature
1. **Kiro user** creates spec structure
2. **Gemini user** generates detailed requirements
3. **Kiro user** reviews and approves
4. **Both users** implement different tasks simultaneously
5. **Integration** through shared spec documentation

### Scenario 2: Parallel Feature Development
1. **Developer A** (Kiro): Works on XP system enhancements
2. **Developer B** (Gemini): Works on tag system improvements
3. **Coordination**: Through separate specs in `.kiro/specs/`
4. **Integration**: Merge specs and coordinate database changes

### Scenario 3: Bug Fixes and Maintenance
1. **Quick fixes**: Direct implementation with documentation update
2. **Complex fixes**: Create mini-spec for coordination
3. **Testing**: Both developers can run same test suite

## Best Practices

### For Gemini CLI Users
- **Always read existing specs** before generating new ones
- **Follow Kiro task format** for compatibility
- **Update task status** manually or with scripts
- **Coordinate database migrations** with other developers

### For Kiro IDE Users
- **Generate Gemini-compatible prompts** in spec descriptions
- **Use clear requirement references** for traceability
- **Keep specs updated** as implementation progresses
- **Share context** through comprehensive spec documentation

### For Both
- **Communicate through specs** rather than external channels
- **Test integration points** frequently
- **Keep documentation current** with implementation
- **Use feature branches** for complex changes

## Agent Hooks Integration

Agent Hooks provide automated workflows that trigger AI assistance based on specific events or manual triggers. Both Kiro and Gemini users should understand how to work with these shared automation tools.

### Understanding Agent Hooks

**Agent Hooks** are automated triggers that execute AI-powered tasks when specific events occur in the IDE or when manually activated. They help maintain code quality and consistency across all developers.

### Common Hook Types for VeriFast

#### 1. **Code Quality Hooks**
```yaml
# Example: Auto-format and lint on save
name: "Django Code Quality Check"
trigger: "file_save"
file_pattern: "*.py"
description: "Automatically format Python code and run linting"
```

#### 2. **Test Automation Hooks**
```yaml
# Example: Run tests when models change
name: "Model Change Test Runner"
trigger: "file_save"
file_pattern: "*/models.py"
description: "Run related tests when model files are modified"
```

#### 3. **Documentation Hooks**
```yaml
# Example: Update documentation on spec changes
name: "Spec Documentation Sync"
trigger: "file_save"
file_pattern: ".kiro/specs/*/requirements.md"
description: "Update project documentation when specs change"
```

### Hook Management for Multi-Developer Teams

#### For Kiro IDE Users
```bash
# View current hooks
# Use Explorer View → Agent Hooks section

# Create new hook
# Command Palette → "Open Kiro Hook UI"

# Enable/disable hooks
# Right-click hook in Explorer → Toggle
```

#### For Gemini CLI Users
Hooks are managed through Kiro IDE, but Gemini users should be aware of active hooks:

```bash
# Check active hooks (if available)
ls .kiro/hooks/

# Understand hook triggers
cat .kiro/hooks/*/config.yaml
```

### Recommended Hooks for VeriFast Development

#### 1. **Django Migration Hook**
- **Trigger**: When `models.py` files are saved
- **Action**: Check for migration needs and suggest creation
- **Benefit**: Prevents forgotten migrations

#### 2. **XP System Validation Hook**
- **Trigger**: When `xp_system.py` is modified
- **Action**: Run XP calculation tests automatically
- **Benefit**: Ensures gamification logic integrity

#### 3. **Template Validation Hook**
- **Trigger**: When HTML templates are saved
- **Action**: Validate Django template syntax and PicoCSS compliance
- **Benefit**: Catches template errors early

#### 4. **API Documentation Hook**
- **Trigger**: When `api_views.py` or `serializers.py` change
- **Action**: Update API documentation automatically
- **Benefit**: Keeps API docs synchronized

### Hook Coordination Between Developers

#### Shared Hook Configuration
```bash
# Hooks should be committed to version control
git add .kiro/hooks/
git commit -m "Add shared development hooks"

# All developers get the same automation
git pull origin main
```

#### Hook Conflict Resolution
- **Kiro users**: Can modify hooks through UI
- **Gemini users**: Should communicate hook needs through specs
- **Both**: Test hooks on feature branches before merging

## Agent Steering System

Agent Steering provides contextual guidance to AI assistants working on the project. This ensures consistent code quality and architectural decisions across all developers and AI tools.

### Understanding Steering Rules

**Steering Rules** are markdown files in `.kiro/steering/` that provide context and guidelines to AI assistants. They ensure all AI-generated code follows project standards.

### Current VeriFast Steering Rules

#### 1. **Product Context** (`.kiro/steering/product.md`)
- Core features and user journey
- Target audience and business model
- Feature priorities and constraints

#### 2. **Technical Standards** (`.kiro/steering/tech.md`)
- Technology stack and versions
- Development commands and workflows
- Environment setup requirements

#### 3. **Project Structure** (`.kiro/steering/structure.md`)
- Directory organization patterns
- Naming conventions
- Code organization standards

### Steering Rule Types

#### Always Included (Default)
```markdown
---
# No front-matter = always included
---
# This steering rule applies to all AI interactions
```

#### Conditional Inclusion
```markdown
---
inclusion: fileMatch
fileMatchPattern: 'verifast_app/models.py'
---
# This rule only applies when working with models.py
```

#### Manual Inclusion
```markdown
---
inclusion: manual
---
# This rule is only included when explicitly referenced with #steering-name
```

### Managing Steering Rules

#### For Kiro IDE Users
```bash
# Steering rules are automatically applied
# View active rules in Kiro's context panel

# Create new steering rule
# File → New → Steering Rule

# Reference specific rule in chat
# Use #steering-rule-name in chat
```

#### For Gemini CLI Users
Steering rules should be referenced in prompts:

```bash
# Include steering context in prompts
gemini-with-steering() {
    local prompt=$1
    local steering_context=$(cat .kiro/steering/*.md)
    
    gemini --prompt "Context from project steering rules:
    $steering_context
    
    User request: $prompt
    
    Follow the project standards and patterns described above."
}
```

### Recommended Steering Rules for VeriFast

#### 1. **Django Patterns** (`.kiro/steering/django-patterns.md`)
```markdown
---
inclusion: fileMatch
fileMatchPattern: 'verifast_app/*.py'
---
# Django-specific coding patterns for VeriFast
- Use class-based views for complex logic
- Follow Django model field naming conventions
- Include help_text for all model fields
- Use proper related_name for relationships
```

#### 2. **XP System Rules** (`.kiro/steering/xp-system.md`)
```markdown
---
inclusion: fileMatch
fileMatchPattern: '*xp_system*'
---
# XP System development guidelines
- All XP transactions must be logged
- Use XPTransactionManager for XP operations
- Validate XP amounts before processing
- Include source tracking for all XP changes
```

#### 3. **Frontend Standards** (`.kiro/steering/frontend.md`)
```markdown
---
inclusion: fileMatch
fileMatchPattern: '*.html,*.css,*.js'
---
# Frontend development standards
- Use PicoCSS classes, avoid custom CSS when possible
- Vanilla JavaScript only, no frameworks
- Follow semantic HTML5 structure
- Ensure mobile responsiveness
```

### Steering Rule Collaboration

#### Creating New Rules
1. **Identify need**: Common patterns or repeated guidance
2. **Draft rule**: Create markdown file with clear guidelines
3. **Test with AI**: Verify rule improves AI output quality
4. **Share with team**: Commit to version control
5. **Monitor effectiveness**: Update based on usage

#### Updating Existing Rules
```bash
# Rules are version controlled
git add .kiro/steering/
git commit -m "Update Django patterns steering rule"

# All developers get updated context
git pull origin main
```

#### Rule Conflicts
- **Kiro users**: Can edit rules directly through file system
- **Gemini users**: Should suggest changes through specs or issues
- **Both**: Test rule changes on feature branches

### Integration with Development Workflow

#### Spec Creation with Steering
```bash
# Kiro automatically includes relevant steering
kiro spec create user-authentication

# Gemini should reference steering manually
gemini-spec-with-steering() {
    local feature_name=$1
    local description=$2
    local steering=$(cat .kiro/steering/*.md)
    
    gemini --prompt "Create spec for: $description
    
    Project context: $steering
    
    Generate requirements.md, design.md, and tasks.md following project standards."
}
```

#### Code Generation with Steering
```bash
# Kiro applies steering automatically to all AI interactions

# Gemini should include steering in task implementation
gemini-task-with-steering() {
    local spec_dir=$1
    local task_number=$2
    local steering=$(cat .kiro/steering/*.md)
    
    gemini --prompt "Implement task with project context:
    
    Steering Rules: $steering
    
    Task: $(grep -A 5 "^- \[ \] $task_number\." $spec_dir/tasks.md)
    
    Follow all project standards and patterns."
}
```

## Quick Reference

### File Locations
- **Specs**: `.kiro/specs/feature-name/` (where `feature-name` is a specific feature directory containing `requirements.md`, `design.md`, and `tasks.md`)
- **Hooks**: `.kiro/hooks/`
- **Steering**: `.kiro/steering/`
- **Main app**: `verifast_app/`
- **Templates**: `verifast_app/templates/`
- **Static files**: `verifast_app/static/`
- **Documentation**: `documentation/`

### Common Commands
```bash
# Check project status
python manage.py check

# Run tests
python manage.py test

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Run development server
python manage.py runserver

# View steering rules
cat .kiro/steering/*.md

# Check active hooks
ls .kiro/hooks/
```

### Kiro-Specific Commands
```bash
# Open Hook UI
# Command Palette → "Open Kiro Hook UI"

# Reference steering in chat
# Use #steering-rule-name

# View active context
# Check Kiro's context panel
```

### Gemini Integration Commands
```bash
# Use steering in prompts
source ~/.gemini_kiro_functions.sh
gemini-with-steering "your prompt here"

# Create spec with steering
gemini-spec-with-steering "feature-name" "description"

# Implement task with steering
gemini-task-with-steering ".kiro/specs/feature-name" "1"
```

This unified approach ensures that whether you're using Gemini CLI or Kiro IDE, you're working within the same documentation-driven framework with consistent AI assistance, automated workflows, and shared project context that prevents conflicts and maintains code quality.