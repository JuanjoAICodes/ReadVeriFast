# Gemini CLI Specification Generation for Documentation-Driven Development (DDD)
*Compatible with Kiro Workflow Standards*

## Overview

This document provides instructions for using Gemini CLI tools to replicate Kiro's spec-driven development workflow. You can achieve the same Documentation-Driven Development (DDD) approach using Gemini's native capabilities combined with file system tools and careful prompt engineering.

## Core Principle

All changes, features, and implementations MUST be preceded by clear, structured documentation. No code should be written or modified without a corresponding, approved specification.

## Core Principles:

**Documentation First:** Always start by defining the requirements.md, then design.md, and finally tasks.md. Do not proceed to the next stage without a complete previous stage.

**Clarity & Precision:** All generated content must be unambiguous, concise, and technically accurate.

**Testability:** Requirements should be directly translatable into test cases.

**Traceability:** Each requirement should ideally map to design elements and tasks.

**Iterative Refinement:** Understand that specifications may be refined. When changes are requested, update the relevant section and cascade necessary updates to dependent sections.

## Output Structure (three distinct Markdown files):

You will generate the content for three separate Markdown files: requirements.md, design.md, and tasks.md. Present the content for each file clearly delimited, stating which file it belongs to.

File 1: requirements.md
Purpose: Captures user stories and acceptance criteria. This is the "What" the system should do.

Format: Adhere strictly to EARS (Easy Approach to Requirements Syntax).

Each requirement must follow the pattern:

WHEN [condition/event]
THE SYSTEM SHALL [expected behavior]
Use clear, concise language.

Break down complex requirements into multiple, atomic EARS statements.

Content Focus: User-centric, functional, and non-functional requirements. Avoid implementation details.

File 2: design.md
Purpose: Documents the technical architecture, high-level design, and implementation considerations. This is the "How" the system will achieve the requirements.

Content Focus:

Architecture Overview: High-level system components and their relationships.

Key Decisions: Rationale for chosen technologies, patterns, or approaches.

Data Models: Relevant data structures or database schema outlines.

API Endpoints: Proposed API contract details (e.g., method, path, request/response body examples).

Sequence Diagrams (Textual/Mermaid): Describe key interactions between components for critical flows (e.g., user signup, order processing). Use clear, textual descriptions if Mermaid is not feasible in the output format.

Non-Functional Considerations: Scalability, security, performance (briefly, linking back to requirements if applicable).

Relationship to requirements.md: Ensure the design directly addresses and fulfills all stated requirements.

File 3: tasks.md
Purpose: Provides a detailed, actionable implementation plan with discrete, trackable tasks. This is the "Steps" to build the design and meet requirements.

Format: A clear, numbered or bulleted list of tasks and sub-tasks.

Content Focus:

Each task should be granular enough to be assigned and completed within a reasonable timeframe (e.g., a few hours to a day).

Task ID: Assign a unique identifier to each top-level task (e.g., TASK-001, TASK-002).

Description: A concise explanation of what needs to be done.

Expected Outcome: What constitutes successful completion of the task (e.g., "API endpoint implemented," "Database table created").

Dependencies (Optional): List other tasks that must be completed first.

Status (Placeholder): Assume an initial status of [PENDING]. The user will manage this.

Relationship to design.md: Tasks should directly flow from the technical design, implementing its components and interactions.

Initial User Request:

[User will insert their project/feature description here. Examples: "Develop a new user login system," "Implement a product search feature," "Add a shopping cart functionality."]

Example Output (Illustrative - Gemini would fill this in):

requirements.md

WHEN a user provides valid login credentials
THE SYSTEM SHALL authenticate the user and redirect them to their dashboard.

WHEN a user provides invalid login credentials
THE SYSTEM SHALL display an error message indicating invalid credentials.

WHEN a user attempts to access a protected resource without authentication
THE SYSTEM SHALL redirect the user to the login page.

design.md

Architecture Overview
Frontend: React SPA for user interface.

Backend: Node.js (Express.js) API for authentication and business logic.

Database: PostgreSQL for user data storage.

Authentication Mechanism: JWT (JSON Web Tokens) for stateless authentication.

API Endpoints
POST /api/auth/login

Request Body: { "email": "string", "password": "string" }

Success Response (200 OK): { "token": "string", "user": { "id": "uuid", "email": "string" } }

Error Response (401 Unauthorized): { "message": "Invalid credentials" }

Sequence Diagram: User Login
User->Frontend: Submits login form
Frontend->Backend: POST /api/auth/login {email, password}
Backend->Database: Query user by email
Database-->Backend: User data (or null)
Backend: Verify password hash
Backend->Backend: Generate JWT
Backend-->Frontend: 200 OK {token, user_data}
Frontend->Frontend: Store JWT, redirect to dashboard
tasks.md

TASK-001: Implement POST /api/auth/login endpoint in Express.js. [PENDING]

Description: Create the API route for user login.

Expected Outcome: Endpoint callable, handles request body.

TASK-002: Add user authentication logic to the backend. [PENDING]

Description: Verify password, generate and sign JWT.

Expected Outcome: JWT returned on successful login.

Dependencies: TASK-003 (Password Hashing)

TASK-003: Integrate bcrypt for password hashing and comparison. [PENDING]

Description: Set up bcrypt for secure password management.

Expected Outcome: Passwords securely stored and compared.

TASK-004: Implement frontend login form and API integration. [PENDING]

Description: Create React component for login, handle state, send API requests.

Expected Outcome: User can input credentials, submit form.

TASK-005: Store JWT securely in the frontend. [PENDING]

Description: Determine best practice for storing JWT (e.g., HTTP-only cookies, local storage).

Expected Outcome: Token persisted across sessions.

TASK-006: Implement client-side redirection after successful login. [PENDING]

Description: Navigate user to dashboard upon successful authentication.

Expected Outcome: User sees dashboard after login.

gemini-spec-workflow.md (Template for Project Repositories)
This gemini-spec-workflow.md file would live in your project's root or a dedicated docs/ folder. It serves as an internal guide for your team on how to use Gemini for specification management.

gemini-spec-workflow.md

Gemini Documentation-Driven Development (DDD) Workflow
This document outlines our process for Documentation-Driven Development (DDD) using Gemini as our specification engine. All new features, bug fixes, or significant changes MUST be documented according to this workflow before any code is written or modified. This ensures clarity, reduces regressions, and maintains a high-quality codebase for our growing project.

Core Principles
Documentation First: Every change starts with a specification. No code without a doc!

Structured Specs: We use requirements.md, design.md, and tasks.md for every spec.

EARS for Requirements: Ensures clarity and testability.

Traceability: Specifications link directly to implementation tasks.

Version Controlled: All specifications are stored in our Git repository alongside the code.

Workflow Overview
Our workflow follows a logical progression, ensuring each step is properly completed before moving to the next.

Fragmento de código

graph TD
    A[Idea/Feature Request] --> B{Start Spec Session with Gemini};
    B --> C[Generate requirements.md (EARS)];
    C --Approved--> D[Generate design.md (Technical Architecture)];
    D --Approved--> E[Generate tasks.md (Implementation Plan)];
    E --Approved--> F[Code Implementation];
    F --> G[Testing & Review];
    G --> H[Deployment & Monitoring];
    H --Feedback/New Idea--> B;
    C --Needs Refinement--> B;
    D --Needs Refinement--> C;
    E --Needs Refinement--> D;
## Gemini CLI Tools Mapping to Kiro Functionality

| Kiro Feature | Gemini CLI Equivalent | Implementation |
|--------------|----------------------|----------------|
| **Spec Generation** | `writeFile` + Comprehensive Prompts | Use structured prompts to generate requirements.md, design.md, tasks.md |
| **Task Status Updates** | Manual editing + Custom scripts | Update checkbox format `- [ ]` to `- [x]` in tasks.md |
| **Requirements (EARS)** | EARS-focused prompting | Explicitly instruct Gemini to use WHEN/SHALL format |
| **Design Documentation** | Design-focused prompts | Generate architecture, APIs, diagrams with specific prompts |
| **Task Execution** | `readFile` + Code generation | Read tasks.md, generate code for each task |
| **Code Analysis** | `readFile` + Analysis prompts | Feed codebase to Gemini to identify completed tasks |
| **MCP Integration** | Native MCP support | Direct equivalent - connect external tools and data |
| **Version Control** | Standard Git | Store specs in `.kiro/specs/` directory structure |

## Specification File Structure (Kiro Compatible)
For each feature or significant change, a dedicated directory will be created under `.kiro/specs/`.

```
.
└── .kiro/specs/
    ├── feature-name-1/
    │   ├── requirements.md
    │   ├── design.md
    │   └── tasks.md
    └── feature-name-2/
        ├── requirements.md
        ├── design.md
        └── tasks.md
```
The Spec Files
1. requirements.md
Purpose: Defines the "WHAT" – user stories and acceptance criteria.

Format:

WHEN [condition/event]
THE SYSTEM SHALL [expected behavior]
How to Generate/Update:

New Spec: Provide Gemini with a high-level feature description.

Refinement: Manually edit the file or provide new instructions to Gemini for specific additions/modifications.

2. design.md
Purpose: Documents the "HOW" – technical architecture, component interactions, and implementation considerations.

Content:

System components and their responsibilities.

Key architectural decisions.

Data structures, API contracts.

Sequence diagrams (textual/Mermaid) for critical flows.

How to Generate/Update:

New Spec: Gemini generates this based on requirements.md.

Refinement: Manually edit or instruct Gemini to refine based on updated requirements or new technical insights.

3. tasks.md
Purpose: Provides the "STEPS" – a detailed, trackable implementation plan.

**Kiro-Compatible Format:**
```markdown
- [ ] 1. Task description
  - Sub-task details and implementation notes
  - Expected outcome description
  - _Requirements: 1.1, 1.2, 2.3_

- [ ] 2. Next task description
  - Implementation details
  - _Requirements: 2.1_
```

Content:
- Discrete, trackable tasks in checkbox format
- Clear descriptions and expected outcomes for each task
- Requirement references linking back to requirements.md
- Sub-task details with implementation guidance

How to Generate/Update:
- **New Spec**: Gemini generates this based on requirements.md and design.md using Kiro checkbox format
- **Status Updates**: Use manual editing or custom scripts to update `- [ ]` to `- [x]`
- **Refinement**: Regenerate by providing Gemini with updated requirements.md and design.md

## Workflow Steps (Practical Guide)

### Initiate a New Spec:

When starting a new feature or significant change, create a new directory: `.kiro/specs/[feature-name]`.

Create empty requirements.md, design.md, and tasks.md files within it.

**Gemini CLI Commands:**
```bash
# Create spec directory structure
mkdir -p .kiro/specs/feature-name
touch .kiro/specs/feature-name/{requirements,design,tasks}.md
```

Define Requirements (Iterative):

Engage Gemini: Provide Gemini with your initial high-level feature idea. Prompt it using the "Gemini Specification Generation for Documentation-Driven Development (DDD)" prompt.

Review & Refine: Carefully review the generated requirements.md. Ensure all user stories and acceptance criteria are clear, complete, and in EARS format. Iterate with Gemini or manually edit until satisfied.

Approval: Get team/PM approval on requirements.md before proceeding.

Design the Solution (Iterative):

Engage Gemini: With an approved requirements.md, instruct Gemini to generate design.md. Provide context on existing architecture or preferred technologies.

Review & Refine: Review the generated design.md. Ensure it addresses all requirements, is technically sound, and aligns with architectural principles. Iterate as needed.

Approval: Get engineering team approval on design.md.

Plan Implementation Tasks:

Engage Gemini: With approved requirements.md and design.md, instruct Gemini to generate tasks.md.

Review & Refine: Review the generated tasks.md. Ensure tasks are granular, clear, and cover the entire scope. Add any manual tasks or re-order if necessary.

Commit: Commit the complete requirements.md, design.md, and tasks.md to your repository. This is the critical "documentation first" step.

Implement & Track:

Work on tasks as defined in tasks.md.

Update Task Status: As tasks are completed, update their status in tasks.md. (Manually edit, or use a future CLI if available).

Code Review: Ensure code implementations directly map back to the tasks and specified design.

Iterate & Refine Existing Specs:

Change in Requirements: If requirements change, update requirements.md first. Then, instruct Gemini to re-evaluate and update design.md and tasks.md based on the new requirements.

Change in Design: If the design needs adjustment, update design.md directly. Then, instruct Gemini to regenerate tasks.md to reflect the design changes.

Task Updates: For new tasks or re-evaluating existing ones, update tasks.md directly or ask Gemini to check codebase for completed tasks.

Sharing Specs
Version Control: Specs are stored directly in the project repository alongside the code. This is the primary method of sharing.

Cross-Team: For specs shared across multiple teams, consider Git submodules or a central specs repository for common components.

## Advanced Gemini CLI Features for Kiro Workflow

### **Task Status Management**
```bash
# Update task status manually
sed -i 's/- \[ \] 1\. Task description/- [x] 1. Task description/' .kiro/specs/feature-name/tasks.md

# Or create a simple script
echo '#!/bin/bash
TASK_FILE="$1"
TASK_NUM="$2"
sed -i "s/- \[ \] ${TASK_NUM}\./- [x] ${TASK_NUM}./" "$TASK_FILE"' > mark-task-complete.sh
chmod +x mark-task-complete.sh
```

### **Code Analysis for Task Completion**
```bash
# Use Gemini CLI to analyze codebase and identify completed tasks
gemini --prompt "Analyze the following codebase and tasks.md file. 
Identify which tasks appear to be completed based on the code:

$(cat .kiro/specs/feature-name/tasks.md)

Codebase:
$(find . -name '*.py' -o -name '*.js' | head -10 | xargs cat)"
```

### **MCP Integration Examples**
```bash
# Connect to external tools via MCP
gemini --mcp-server database --prompt "Generate SQL schema based on requirements.md"
gemini --mcp-server github --prompt "Create issues for incomplete tasks"
```

### **Iterative Spec Refinement**
```bash
# Update requirements based on feedback
gemini --prompt "Update the following requirements.md based on this feedback: [feedback]
Current requirements:
$(cat .kiro/specs/feature-name/requirements.md)"

# Regenerate design based on updated requirements
gemini --prompt "Update design.md based on these revised requirements:
$(cat .kiro/specs/feature-name/requirements.md)"
```

## Workflow Automation Scripts

### **Spec Generation Script**
```bash
#!/bin/bash
# generate-spec.sh
FEATURE_NAME="$1"
DESCRIPTION="$2"

# Create directory structure
mkdir -p .kiro/specs/$FEATURE_NAME

# Generate requirements
gemini --prompt "Generate requirements.md in EARS format for: $DESCRIPTION" > .kiro/specs/$FEATURE_NAME/requirements.md

# Generate design (after requirements approval)
gemini --prompt "Generate design.md based on requirements:
$(cat .kiro/specs/$FEATURE_NAME/requirements.md)" > .kiro/specs/$FEATURE_NAME/design.md

# Generate tasks (after design approval)
gemini --prompt "Generate tasks.md in Kiro checkbox format based on:
Requirements: $(cat .kiro/specs/$FEATURE_NAME/requirements.md)
Design: $(cat .kiro/specs/$FEATURE_NAME/design.md)" > .kiro/specs/$FEATURE_NAME/tasks.md
```

### **Task Execution Script**
```bash
#!/bin/bash
# execute-task.sh
SPEC_DIR="$1"
TASK_NUM="$2"

# Get specific task
TASK=$(grep "^- \[ \] $TASK_NUM\." $SPEC_DIR/tasks.md)

# Generate code for task
gemini --prompt "Generate code for this task:
$TASK

Context:
Requirements: $(cat $SPEC_DIR/requirements.md)
Design: $(cat $SPEC_DIR/design.md)"
```

## Integration with Development Workflow

### **Git Hooks Integration**
```bash
# .git/hooks/pre-commit
#!/bin/bash
# Ensure all specs are up to date before commit
for spec_dir in .kiro/specs/*/; do
    if [ -f "$spec_dir/tasks.md" ]; then
        # Check if tasks match current code
        gemini --prompt "Verify tasks in $spec_dir/tasks.md match current codebase"
    fi
done
```

### **CI/CD Integration**
```yaml
# .github/workflows/spec-validation.yml
name: Spec Validation
on: [push, pull_request]
jobs:
  validate-specs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Validate Specs
        run: |
          for spec in .kiro/specs/*/; do
            gemini --prompt "Validate spec completeness: $spec"
          done
```

## Best Practices for Gemini CLI + Kiro Workflow

### **Prompt Engineering Tips**
1. **Be Specific**: Always specify the exact format you want (EARS, Kiro checkboxes, etc.)
2. **Provide Context**: Include existing requirements/design when updating specs
3. **Use Templates**: Create prompt templates for consistent output
4. **Iterate Gradually**: Make small, focused changes rather than large rewrites

### **File Management**
1. **Version Control**: Always commit specs before implementation
2. **Naming Conventions**: Use kebab-case for feature names
3. **Documentation**: Keep a changelog of spec updates
4. **Backup**: Regularly backup your .kiro/specs directory

### **Quality Assurance**
1. **Review Process**: Always review generated specs before approval
2. **Validation**: Use Gemini to cross-check requirements vs design vs tasks
3. **Testing**: Generate test cases from requirements
4. **Traceability**: Maintain clear links between requirements and tasks

## Troubleshooting Common Issues

### **Large Context Windows**
```bash
# For large codebases, focus on specific files
gemini --prompt "Analyze only these files for task completion:
$(find . -name "*.py" -path "./src/*" | head -5 | xargs cat)"
```

### **Spec Synchronization**
```bash
# Check if specs are out of sync
gemini --prompt "Compare these three files for consistency:
Requirements: $(cat requirements.md)
Design: $(cat design.md)  
Tasks: $(cat tasks.md)"
```

### **Task Granularity**
```bash
# Break down large tasks
gemini --prompt "Break this task into smaller, more granular subtasks:
- [ ] 1. Implement user authentication system"
```

---

## Summary

This Gemini CLI approach provides **full compatibility** with Kiro's spec-driven development workflow while leveraging Gemini's powerful generative capabilities. The key advantages are:

- ✅ **Same three-file structure** (requirements.md, design.md, tasks.md)
- ✅ **EARS format compliance** for requirements
- ✅ **Kiro checkbox format** for tasks
- ✅ **Version control integration** with Git
- ✅ **MCP support** for external tool integration
- ✅ **Automation capabilities** through scripting
- ✅ **Professional workflow** with proper documentation-first approach

The main difference is that you manage the workflow through CLI commands and scripts rather than an integrated IDE, but the core methodology and outputs are identical to Kiro's approach.
