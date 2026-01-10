# Agent & Skill Usage Guide

This guide explains how to select and use specialized agents, skills, and tools in the Data Canary AI project.

## Table of Contents
- [Decision Framework](#decision-framework)
- [Agent Categories](#agent-categories)
- [Project-Specific Recommendations](#project-specific-recommendations)
- [When to NOT Use Agents](#when-to-not-use-agents)
- [Creating Custom Skills](#creating-custom-skills)

---

## Decision Framework

### Key Principle

**Claude Code is the primary implementer. Agents are specialists for validation, review, and complex problem-solving.**

Use this decision tree:

```
Is the task straightforward and well-defined?
├── YES → Use direct tools (Read/Edit/Write/Bash)
│         Examples: Creating Pydantic models, writing tests, git operations
│
└── NO → Is it a specialized domain problem?
    ├── YES → Use specialized agent with relevant expertise
    │         Examples: Frontend race conditions, security audits, performance optimization
    │
    └── NO → Use plan/explore agent for research and architecture
              Examples: Unfamiliar codebase, complex design decisions
```

### Direct Tools vs Agents

**Direct Tools (Default Choice):**
- ✅ Read/Edit/Write/Bash
- ✅ For: Clear requirements, standard implementation, known patterns
- ✅ Examples: Phase 1 & 2 implementation (models, contract builder, tests)

**Specialized Agents (When Needed):**
- ✅ Task-specific expertise
- ✅ For: Complex validation, multi-step review, specialized domains
- ✅ Examples: Frontend race conditions, performance bottlenecks

---

## Agent Categories

### 1. Implementation/Planning Agents

#### `Plan` Agent
- **Purpose**: Design implementation strategies for complex features
- **When to use**: Multi-file changes, architectural decisions, unclear requirements
- **For this project**: Useful for Phase 3-4 if UI design is complex

#### `Explore` Agent
- **Purpose**: Explore unfamiliar codebases
- **When to use**: New repository, finding patterns, understanding architecture
- **For this project**: Not needed (we know the codebase)

### 2. Review Agents

#### `code-simplicity-reviewer`
- **Purpose**: Review code for simplicity and minimalism after implementation
- **When to use**: After completing feature implementation
- **For this project**: **Recommended for Phase 2 review** (we could have caught duplication)

#### `kieran-rails-reviewer` / `dhh-rails-reviewer`
- **Purpose**: High-quality bar review for Rails code
- **When to use**: After Rails features, controllers, services
- **For this project**: Skip (Python project, not Rails)

#### `kieran-python-reviewer`
- **Purpose**: High-quality bar review for Python code
- **When to use**: After Python implementations
- **For this project**: **Consider for Phase 3** before merge

#### `julik-frontend-races-reviewer`
- **Purpose**: Review JavaScript/Stimulus for race conditions
- **When to use**: After JavaScript/Stimulus changes
- **For this project**: **Use in MVP3** if adding JavaScript interactivity

#### `security-sentinel`
- **Purpose**: Security audit and vulnerability scanning
- **When to use**: For authentication, API endpoints, user input handling
- **For this project**: Consider before production deployment

#### `performance-oracle`
- **Purpose**: Performance analysis and optimization
- **When to use**: When experiencing slow operations, scaling concerns
- **For this project**: **Use if Polars operations are slow** or data is large

#### `data-integrity-guardian`
- **Purpose**: Review database migrations and data transformations
- **When to use**: DB schema changes, data backfills
- **For this project**: Useful for MVP1 delta ingestion mode

### 3. Design Agents

#### `design-iterator`
- **Purpose**: Iterate UI designs 5-10 times for refinement
- **When to use**: When initial design doesn't look right
- **For this project**: **Consider for Phase 3 Streamlit UI** if styling is off

#### `figma-design-sync`
- **Purpose**: Sync implementation with Figma designs
- **When to use**: When Figma designs are provided
- **For this project**: Optional (depends on design process)

### 4. Research Agents

#### `framework-docs-researcher`
- **Purpose**: Research framework documentation and patterns
- **When to use**: When implementing new libraries
- **For this project**: **Useful for Polars Lazy API migration**

#### `best-practices-researcher`
- **Purpose**: Research best practices and external examples
- **When to use**: Uncertain about best approach
- **For this project**: Optional (we have clear requirements)

### 5. Workflow Agents

#### `pr-comment-resolver`
- **Purpose**: Address PR comments and make requested changes
- **When to use**: When reviewer leaves comments
- **For this project**: Use as needed during code review

#### `bug-reproduction-validator`
- **Purpose**: Verify bug reports by reproducing issues
- **When to use**: When investigating bug reports
- **For this project**: Use when users report issues

#### `every-style-editor`
- **Purpose**: Format text to Every's style guide
- **When to use**: For blog posts, newsletters, documentation
- **For this project**: Skip (not part of this project)

---

## Project-Specific Recommendations

### MVP0 Implementation (Current Phase)

**Direct tools only** - No agents needed:
- Creating Pydantic models ✅
- Building contract builder ✅
- Writing export functions ✅
- Creating tests ✅
- Git workflow ✅

**Why?**
- Requirements are well-defined in CLAUDE.md
- Implementation patterns are clear
- Straightforward code generation

### MVP0 → MVP1 Transition

**Consider these agents:**
- `performance-oracle` - If Polars Lazy API migration has issues
- `framework-docs-researcher` - For Polars LazyFrame patterns
- `data-integrity-guardian` - For delta ingestion data validation

### MVP1 (Delta Ingestion)

**Recommended agents:**
- `data-migration-expert` - If complex data transformations
- `security-sentinel` - If adding authentication
- `code-simplicity-reviewer` - After major features

**Skip:**
- Frontend agents (no JavaScript yet)

### MVP2 (Governance)

**May need:**
- `architecture-strategist` - For governance features
- `performance-oracle` - If handling large metadata directories

### MVP3+ (UI/UX Enhancements)

**Will need:**
- `julik-frontend-races-reviewer` - For any JavaScript/Stimulus
- `design-iterator` - If Streamlit UI needs refinement
- `kieran-python-reviewer` - For backend API changes

---

## When to NOT Use Agents

### ❌ Skip Agents When:

1. **Task is straightforward**
   - Creating models with clear structure
   - Writing standard CRUD operations
   - Following established patterns

2. **Requirements are well-defined**
   - Spec is clear with examples
   - No design decisions needed
   - Single implementation path

3. **Time is critical**
   - Agents add overhead (token cost, latency)
   - Direct implementation is faster
   - No validation needed

4. **No specialized expertise needed**
   - No frontend JavaScript
   - No complex algorithms
   - No security concerns

### Real Example from Phase 2:

**What we did:**
- Used direct tools to write contract_builder.py
- Ran tests manually
- Used direct bash for git operations

**What we should have done:**
- Added `code-simplicity-reviewer` before merge to catch duplication
- Still use direct tools for implementation
- Add review agent as final validation step

**Result**: Phase 2 had duplicate code that required Phase 2.5 fix

---

## Creating Custom Skills

### When Needed

Create a custom skill (`/.claude/`) when:
- Repeating the same complex workflow
- Need specialized knowledge for this project
- Want to encapsulate best practices

### Example Custom Skills for This Project

**Potential skills:**
- `/run-ci` - Run full CI pipeline locally
- `/create-feature` - Create branch with proper naming
- `/test-and-commit` - Run tests, check quality, commit
- `/prep-phase3` - Setup for Phase 3 implementation

### Skill Creation Process

1. Identify repeated workflow
2. Document steps in SKILL.md format
3. Place in `/.claude/` directory
4. Test the skill
5. Document usage

See `compound-engineering:skill-creator` for guidance on creating skills.

---

## MCP Configuration

### Current MCPs in Use

**compound-engineering plugin:**
- Browser automation (used for watching CI checks)

### Future MCPs to Consider

- **Polars MCP** - Direct Polars integration if available
- **GitHub MCP** - Enhanced GitHub operations
- **Testing MCP** - Test visualization and management

---

## Command Reference

### Essential Commands (Direct Tools)

```bash
# Development
source .venv/bin/activate
uv run pytest
uv run ruff check .
uv run ruff format .  # For formatting
uv run ruff format --check .  # For checking
uv run mypy data_canary/ --config-file pyproject.toml

# Git
git checkout -b feature/description
git commit -m "feat: description"
git push -u origin feature/description
gh pr create --title "feat: description" --body "Details"
gh pr checks --watch
gh pr merge

# Branch cleanup
git branch -d feature/description
git push origin --delete feature/description
```

### Agent Invocation Examples

```bash
# Review code for simplicity (after implementation)
/claude: use code-simplicity-reviewer on contract_builder.py

# Iterate on UI design (if needed)
/claude: use design-iterator agent with 5 iterations on Streamlit UI

# Check for performance issues
/claude: use performance-oracle to analyze Polars operations

# Review Python code quality
/claude: use kieran-python-reviewer on llm/ directory
```

---

## Decision Summary for Data Canary AI

### Current Phase (MVP0: Phase 3 Implementation)

**Use direct tools for:**
- ✅ Streamlit UI implementation
- ✅ Integration of contract builder with UI
- ✅ Testing and validation
- ✅ Git workflow

**Add review agent:**
- ✅ `code-simplicity-reviewer` before final Phase 3 merge

### Upcoming Phases

**MVP1 (Delta Ingestion):**
- Consider: `data-integrity-guardian` for data validation logic
- Consider: `performance-oracle` for large dataset handling

**MVP2 (Governance):**
- Consider: `architecture-strategist` for governance features

**MVP3 (UI/UX):**
- Will need: `design-iterator` for UI refinement
- Will need: `julik-frontend-races-reviewer` for any JavaScript

### Never Needed for This Project

- ❌ Ruby/Rails agents (kieran-rails, dhh-rails)
- ❌ TypeScript reviewer (no TypeScript in codebase)
- ❌ Every-style-editor (not publishing to Every)
- ❌ Julik frontend reviewer until JavaScript added
