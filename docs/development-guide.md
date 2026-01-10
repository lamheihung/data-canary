# Development Guide

This guide contains detailed development practices, workflows, and standards for Data Canary AI project.

## Table of Contents
- [Pre-Commit Checklist](#pre-commit-checklist)
- [Git Workflow](#git-workflow)
- [Code Quality Standards](#code-quality-standards)
- [Python Development Guidelines](#python-development-guidelines)
- [Testing Standards](#testing-standards)
- [Common Issues & Solutions](#common-issues--solutions)

---

## Pre-Commit Checklist

Before ANY git commit, verify ALL of these checks pass:

### 1. Environment Setup
- [ ] **Virtual environment activated**: Run `source .venv/bin/activate` (macOS/Linux) or `.venv\Scripts\activate` (Windows)
- [ ] **Python 3.13 confirmed**: `python --version` should show 3.13.x
- [ ] **Dependencies installed**: `uv pip install -e .[dev]` (if requirements changed)

### 2. Code Quality Verification
Run these commands in order:

```bash
# All tests pass (100% required)
uv run pytest

# Linting passes - no errors
uv run ruff check .

# Formatting is clean - would not change anything
uv run ruff format --check .

# Type checking passes
uv run mypy data_canary/ --config-file pyproject.toml

# Security scan shows no HIGH issues
uv run bandit -r data_canary
```

### 3. Code Review Checklist
- [ ] **No duplicate code**: Review `git diff --staged` for redundancy
- [ ] **No unused imports**: Ruff should catch this automatically
- [ ] **Google-style docstrings**: All public functions/classes documented
- [ ] **No `Any` types**: Type hints required, `Any` needs justification
- [ ] **No secrets committed**: Check for API keys, passwords, tokens

### 4. Git Hygiene
- [ ] **Correct branch naming**: `feature/description`, `fix/description`, or `docs/description`
- [ ] **Conventional commit format**: `feat:`, `fix:`, `docs:`, `refactor:`, etc.
- [ ] **Atomic commits**: Each commit focuses on one logical change

---

## Git Workflow

### Branch Lifecycle: Create → Develop → Test → Push → Wait → Merge → Cleanup

**Step 1: Create Feature Branch**
```bash
git checkout main
git pull origin main
git checkout -b feature/your-feature-name
```

**Step 2: Develop**
- Make changes with frequent, atomic commits
- Follow conventional commit format

**Step 3: Test Locally**
- Run full pre-commit checklist (see above)
- Fix any failures before proceeding

**Step 4: Push to Remote**
```bash
git push -u origin feature/your-feature-name
```

**Step 5: Wait for CI (CRITICAL)**
- Do NOT merge until all GitHub checks pass ✅
- Monitor checks: `gh pr checks --watch`
- If any check fails, fix and push again

**Step 6: Create Pull Request**
```bash
gh pr create --title "feat: description" --body "Detailed description"
```

**Step 7: Merge ONLY When All Checks Pass**
- All 4 checks must show ✅
- No exceptions for "just documentation" (can trigger issues)

**Step 8: Cleanup After Merge**
```bash
git checkout main
git pull origin main
git branch -d feature/your-feature-name              # Delete local
git push origin --delete feature/your-feature-name  # Delete remote
```

### Protected Branches Policy

**NEVER push directly to:**
- `main` - Production branch
- `develop` - Development branch (if exists)

**All changes MUST go through:**
1. Feature branch
2. Pull request
3. CI validation
4. Merge via GitHub UI or `gh pr merge`

### CI Check Timeline

Typical durations:
- **Lint and Format**: ~15 seconds
- **Security Scan**: ~15 seconds
- **Type Check**: ~35 seconds
- **Build and Verify**: ~20 seconds

**Total wait time**: ~85 seconds

**DO NOT merge** until you see all green checkmarks.

---

## Code Quality Standards

### Python Code Standards

**Follow:**
- PEP 8 - Style Guide for Python Code
- Google Style Docstrings for all public APIs
- Type hints for all functions and methods

**Docstring Example:**
```python
def build_physical_schema(
    columns: List[Dict[str, Any]],
    naming_report: Optional[NamingCheckReport] = None,
) -> List[PhysicalColumn]:
    """Builds physical schema from profiling data with AI suggestions.

    Creates PhysicalColumn definitions with support for user overrides,
    AI suggestions, and role annotations while preserving source→target
    mapping and column ordering.

    Args:
        columns: List of column data from Polars profiling.
        naming_report: Optional AI naming suggestions for columns.

    Returns:
        List of PhysicalColumn objects with override information.

    Raises:
        ValueError: If columns list is empty or missing required fields.

    Example:
        schema = build_physical_schema(
            columns=[{"name": "user_id", "dtype": "Int64"}],
            naming_report=naming_check_report
        )
    """
```

### Polars Best Practices

**Current State:**
- Using Eager API in prototype (acceptable temporarily)

**MVP0 Requirement:**
- **MUST migrate to Lazy API** for memory efficiency
- Use `pl.scan_csv()` instead of `pl.read_csv()`
- Use `pl.scan_parquet()` instead of `pl.read_parquet()`
- All transformations should use LazyFrame operations

**Example Migration:**
```python
# Before (Eager)
df = pl.read_csv("data.csv")
result = df.filter(pl.col("age") > 18).groupby("city").agg(pl.count())

# After (Lazy)
lf = pl.scan_csv("data.csv")
result = lf.filter(pl.col("age") > 18).groupby("city").agg(pl.count()).collect()
```

### Type Safety

- **No `Any` types** without explicit justification in comments
- **Use Union types** for multiple possible types
- **Leverage Pydantic** for data validation
- **MyPy strict mode** enabled - no issues allowed

### Error Handling

- **Be specific**: Catch specific exceptions, not generic `Exception`
- **Provide context**: Include column names, values in error messages
- **Fail fast**: Validate inputs at function boundaries
- **Document raises**: All `@raises` in docstrings should be accurate

---

## Testing Standards

### Test File Organization

- Place tests in `tests/` directory
- Name: `test_<module>.py`
- Structure: Mirror source code organization

### Coverage Goals

- **Minimum**: 80% coverage for new code
- **Ideal**: 90%+ for critical paths (contract building, data transformation)
- **Current**: 64 tests, all passing

### Test Categories

**1. Unit Tests**
- Test individual functions in isolation
- Mock external dependencies (LLM APIs, file I/O)
- Fast execution (< 1 second per test)

**2. Integration Tests**
- Test component interaction
- Use real Polars DataFrames (small, synthetic data)
- Verify full workflows end-to-end

**3. Validation Tests**
- Test error conditions and edge cases
- Verify error messages are helpful
- Check type validation

### Example Test Patterns

```python
def test_build_physical_schema_with_overrides():
    """Test user override precedence: User > AI > Original."""
    columns = [{
        "name": "usr_id",
        "dtype": "Int64"
    }]

    naming_report = NamingCheckReport(
        violations=[],
        suggestions=[{"column": "usr_id", "suggested_name": "user_id"}]
    )

    user_overrides = {"usr_id": {"target_name": "user_identifier"}}

    result = build_physical_schema(
        columns=columns,
        naming_report=naming_report,
        user_overrides=user_overrides
    )

    assert result[0].target_name == "user_identifier"  # User override wins
    assert result[0].ai_suggested_name == "user_id"    # AI suggestion stored
    assert result[0].source_name == "usr_id"           # Original preserved
```

### Running Tests

**All tests:**
```bash
uv run pytest
```

**Specific file:**
```bash
uv run pytest tests/test_contract_builder.py
```

**With coverage:**
```bash
uv run pytest --cov=data_canary --cov-report=html
```

**Verbose output:**
```bash
uv run pytest -v
```

---

## Common Issues & Solutions

### Issue 1: MyPy Type Errors with Polars

**Problem:**
```
error: "Sequence[str]" has no attribute "append"
```

**Cause:**
Polars schema inference creates immutable sequences.

**Solution:**
Add explicit type annotation:
```python
transformation_log: List[Dict[str, Any]] = []
transform_record: Dict[str, Any] = {
    "column": col_name,
    "actions": [],  # type: ignore
}
```

### Issue 2: Ruff Formatting Fails

**Problem:**
```
Would reformat: data_canary/core/contract_builder.py
```

**Solution:**
```bash
# Apply formatting
uv run ruff format .

# Verify it worked
uv run ruff format --check .
```

### Issue 3: Tests Pass Locally but CI Fails

**Cause:**
- Different Python version in CI (we use 3.13)
- Missing dependencies
- Code duplication that wasn't caught

**Solution:**
1. Always activate virtual environment
2. Run full pre-commit checklist
3. Review all staged changes: `git diff --staged`
4. Look for duplicate function definitions

### Issue 4: Python 3.13 Deprecation Warnings

**Current warnings (acceptable for MVP0):**
```
DeprecationWarning: datetime.datetime.utcnow() is deprecated
```

**Guidance:**
- Acceptable temporarily with MVP0 scope
- DO NOT use `datetime.utcfromtimestamp()` (also deprecated)
- Future fix: Use `datetime.now(timezone.utc)`

### Issue 5: CI Pipeline Fails After Merge to Main

**Cause:**
- Merged PR with failing CI checks
- Main branch now has failing status

**Prevention:**
- ALWAYS wait for all checks to pass before merging
- Use: `gh pr checks --watch` to monitor
- If documentation-only change, still wait (CI validates structure)

---

## Agent & Tool Selection Guide

See `docs/agent-usage-guide.md` for detailed agent and skill selection logic.

**Quick Reference:**

| Task Type | Direct Tools | Specialized Agent |
|-----------|--------------|-------------------|
| Simple implementation | ✅ Read/Edit/Write | ❌ Skip |
| Complex UI design | ⚠️ Initial attempt | ✅ `design-iterator` |
| Frontend JavaScript | ✅ Implementation | ✅ `julik-frontend-races-reviewer` |
| Architectural choices | ⚠️ Exploration | ✅ `architecture-strategist` |
| Performance issues | ✅ Profiling | ✅ `performance-oracle` |
| Security audit | ✅ Code review | ✅ `security-sentinel` |

**For this project (Data Canary AI):**
- Current phases (MVP0-MVP2): Use direct tools for implementation
- JavaScript/Stimulus work (MVP3+): Add frontend review agents
- Performance optimization: Use agents only if bottlenecks identified

---

## Deployment Options

This section covers deployment strategies for Data Canary AI. **Note**: MVP0 focuses on local development. Advanced deployment options will be discussed in future milestones.

### Local Development Setup

**Process:**
```bash
# 1. Install in development mode with all dependencies
uv pip install -e .[dev]

# 2. Configure environment variables
cp .env.example .env
# Edit .env with your API keys and configuration

# 3. Run the Streamlit application
streamlit run data_canary/app.py
```

**Configuration via .env:**
```bash
OPENAI_API_KEY="your-api-key-here"
OPENAI_MODEL_NAME="kimi-k2-thinking"  # Optional
OPENAI_BASE_URL="https://api.moonshot.ai/v1"  # For non-OpenAI providers
```

**Best Practices:**
- **Never commit .env file**: It's already in .gitignore
- **Use separate API keys**: Create development-specific keys
- **Monitor token usage**: Check costs in LLM provider dashboard
- **Sensitive data**: Process locally, no cloud uploads needed

**Use Cases:**
- Individual data engineers doing one-off data exploration
- Prototyping and testing new features
- Working with sensitive data that cannot leave local environment
- Learning and experimentation with the tool

**Future Considerations:**
Docker deployment, cloud deployment (AWS, GCP), and Kubernetes orchestration will be evaluated based on user needs and usage patterns after MVP1.

---

## Troubleshooting Guide

This section covers common issues encountered during development, with clear solutions and workarounds.

### Common Development Issues

#### "OPENAI_API_KEY not found"

**Symptoms:**
```
Error: OPENAI_API_KEY environment variable not set
```

**Root Cause:** LLM integration requires API credentials to function.

**Solutions:**
```bash
# Option 1: Export environment variable (temporary)
export OPENAI_API_KEY="sk-..."

# Option 2: Create .env file (persistent, not committed)
echo "OPENAI_API_KEY=sk-..." > .env

# Option 3: Set in IDE run configuration
# PyCharm/VSCode: Add to environment variables in run config
```

**Best Practice:** Use .env file for local development, environment variables for production.

#### "File too large" error

**Symptoms:** Streamlit shows upload limit errors or processing is very slow.

**Root Cause:** Application not optimized for large files.

**Solutions:**
```python
# Option 1: Use Polars Lazy API (recommended)
lf = pl.scan_csv("huge_file.csv")  # Lazy evaluation
df = lf.collect(streaming=True)    # Process in chunks

# Option 2: Process only needed columns
lf = pl.scan_csv("large.csv").select(["col1", "col2"])

# Option 3: Use approximations for speed
df.select([
    pl.col("*").null_count(),
    pl.col("*").approx_unique(),  # Faster than exact count
    pl.col("*").mean()
]).collect()
```

**Performance Targets:**
- Files < 100MB: < 5 seconds
- Files < 1GB: < 30 seconds
- Files < 10GB: < 5 minutes (with Lazy API)

#### "LLM returned invalid JSON"

**Symptoms:**
```
pydantic.error_wrappers.ValidationError: 1 validation error
```

**Root Cause:** AI model didn't follow the schema instructions.

**Solutions:**
```python
# 1. Verify schema in system prompt (check llm/prompts.py)
system_prompt = f"""You are a data quality analyst. Respond in JSON that matches this schema: {schema_definition}"""

# 2. Try a more capable model
# In .env
OPENAI_MODEL_NAME="kimi-k2-thinking"

# 3. Add retry logic with exponential backoff
import time
for attempt in range(3):
    try:
        return call_llm_with_schema()
    except ValidationError as e:
        if attempt == 2:  # Last attempt
            raise
        time.sleep(2 ** attempt)  # Wait 2s, 4s, 8s

# 4. Log failed responses for analysis
logger.error(f"LLM returned invalid JSON: {response}")
```

**Best Practice:** Always wrap LLM calls in try/except and log failures for analysis.

### CI/CD Issues

#### CI pipeline failing on GitHub but passing locally

**Symptoms:** GitHub Actions shows ❌ while local tests show ✅.

**Root Causes:**
- Different Python versions
- Missing dependencies in CI environment
- Code duplication not caught locally
- Virtual environment not activated locally

**Solutions & Prevention:**
```bash
# 1. Verify Python version matches CI (3.13.9)
python --version

# 2. Clean install test (catches dependency issues)
rm -rf .venv
uv venv
source .venv/bin/activate
uv pip install -e .[dev]
uv run pytest  # Should match CI results

# 3. Check for code duplication
git diff --staged | grep -E "^\+.*def "  # Look for duplicate functions

# 4. Run exact CI commands locally
cat .github/workflows/ci.yml | grep -A 5 "run:"
# Execute those commands in your terminal
```

**Pre-commit Checklist (MANDATORY):**
```bash
# Before every push:
source .venv/bin/activate
uv run pytest && uv run ruff check . && uv run ruff format --check . && uv run mypy data_canary/
```

#### Merge conflicts in schema files

**Symptoms:**
```
Conflicts in schemas/data_models.py
```

**Root Cause:** Multiple PRs modifying Pydantic models simultaneously.

**Solution:**
```bash
# 1. Merge main into feature branch
git checkout feature/DATA-123
git merge main

# 2. Resolve conflicts manually
# Look for <<<<<<<, =======, >>>>>>> markers
# Keep both changes when appropriate

# 3. Test schema validation
uv run pytest tests/test_data_models.py
uv run mypy data_canary/schemas/

# 4. Verify runtime behavior
uv run pytest tests/test_contract_builder.py  # Integration tests

# 5. Complete merge
git add schemas/data_models.py
git commit -m "fix: resolve schema merge conflicts"
```

**Prevention:**
- Keep PRs small and focused
- Avoid parallel changes to the same schema files
- Communicate schema changes in team channels

### Data Quality Issues

#### "null_count_pct > 100%" in results

**Symptoms:** Statistical impossibilities in profiling results.

**Root Causes:**
- Race condition in data processing
- Schema mismatch between operations
- Column name duplication

**Solutions:**
```python
# 1. Verify DataFrame schema expectations
assert df.schema == expected_schema, f"Schema mismatch: {df.schema}"

# 2. Check for column name duplicates
duplicates = [col for col in df.columns if df.columns.count(col) > 1]
assert len(duplicates) == 0, f"Duplicate columns found: {duplicates}"

# 3. Validate before and after transformations
original_cols = df.columns
df_processed = apply_transformations(df)
assert len(original_cols) == len(df_processed.columns)
```

**Best Practices:**
- Validate schema at function boundaries
- Use Polars Lazy API for consistency
- Add assertions in development to catch issues early

---

## Contributing Guidelines

This section outlines the development workflow and standards for contributing to Data Canary AI.

### Git Workflow

#### Branch Naming Convention

**Format:** `<type>/<JIRA-ID>-<description>` (if using JIRA) or `<type>/<description>`

**Types:**
- **feature**: New features and enhancements
- **fix**: Bug fixes
- **docs**: Documentation updates
- **refactor**: Code restructuring (no behavior change)
- **hotfix**: Critical fixes for production

**Examples:**
```bash
# Feature branch
git checkout -b feature/human-override-workflow

# Bug fix branch
git checkout -b fix/null-pointer-check

# Documentation branch
git checkout -b docs/api-endpoints
```

#### Development Process

**Step 1: Create Feature Branch**
```bash
git checkout main
git pull origin main
git checkout -b feature/description
```

**Step 2: Develop with Atomic Commits**
Each commit should be a logical unit of work.

```bash
# Good: Single purpose commits
git commit -m "feat: add contract builder with user override support"
git commit -m "fix: handle null values in AI suggestions"
git commit -m "docs: update API documentation"

# Bad: Multiple changes in one commit
git commit -m "feat: add contract builder and fix bugs and update readme"
```

**Step 3: Code Quality Checks (MANDATORY)**
```bash
# Format code
uv run ruff format .

# Check types
uv run mypy data_canary/

# Security scan
uv run bandit -r data_canary/
```

**Step 4: Test Thoroughly**
```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_contract_builder.py -v

# Check coverage
uv run pytest --cov=data_canary --cov-report=html
```

**Step 5: Push and Create PR**
```bash
# Push feature branch
git push -u origin feature/description

# Create pull request with detailed description
gh pr create --title "feat: description" --body "Detailed explanation of changes"
```

**Step 6: Wait for CI (CRITICAL)**
```bash
# Monitor CI checks
gh pr checks --watch

# Only merge when all checks pass ✅
# DO NOT merge if any check fails ❌
```

**Step 7: Merge and Cleanup**
```bash
# After PR is merged
git checkout main
git pull origin main
git branch -d feature/description                  # Delete local
git push origin --delete feature/description       # Delete remote
```

### Code Quality Standards

#### Python Code Requirements

**Style:**
- Follow PEP 8 guidelines
- Use ruff for formatting and linting
- Maximum line length: 88 characters

**Type Hints:**
- All functions must have type hints
- No `Any` type without explicit justification in comments

**Docstrings:**
- Google-style docstrings for all public functions/classes
- Include Args, Returns, Raises sections
- Add examples for complex functions

**Example:**
```python
def build_physical_schema(
    columns: List[Dict[str, Any]],
    naming_report: Optional[NamingCheckReport] = None,
) -> List[PhysicalColumn]:
    """Builds physical schema from profiling data.

    Creates PhysicalColumn definitions with support for user overrides,
    AI suggestions, and role annotations.

    Args:
        columns: List of column data from Polars profiling
        naming_report: Optional AI naming suggestions

    Returns:
        List of PhysicalColumn objects

    Raises:
        ValueError: If columns list is empty or missing required fields

    Example:
        >>> schema = build_physical_schema([{"name": "col", "dtype": "Int64"}])
        >>> assert len(schema) == 1
    """
    # Implementation here
```

### Code Review Checklist

**Mandatory verification before submitting PR:**

- [ ] **Functionality:** Code works as intended, all tests pass
- [ ] **Tests:** New code has adequate test coverage (aim for 80%+)
- [ ] **Documentation:** Docstrings updated for all public functions
- [ ] **Type hints:** All functions have proper type annotations
- [ ] **Security:** No secrets committed, input validation implemented
- [ ] **Performance:** Efficient data structures and algorithms used
- [ ] **Error handling:** Graceful error handling with descriptive messages
- [ ] **CI:** All GitHub Actions checks pass

### Testing Standards

**Coverage Goals:**
- Minimum: 80% coverage for new code
- Critical paths: 90%+ (contract building, data transformation)
- Current baseline: 64 tests, 100% passing

**Test Organization:**
- Place tests in `tests/` directory
- Name files: `test_<module>.py`
- Mirror source code structure
- One test class per feature, one test method per scenario

**Example Test:**
```python
def test_build_physical_schema_with_user_override():
    """Test that user override takes precedence over AI suggestions."""
    columns = [{"name": "usr_id", "dtype": "Int64"}]
    naming_suggestion = [{"column": "usr_id", "suggested_name": "user_id"}]
    user_override = {"usr_id": {"target_name": "user_identifier"}}

    result = build_physical_schema(
        columns=columns,
        naming_report=naming_suggestion,
        user_overrides=user_override
    )

    assert result[0].target_name == "user_identifier"  # User wins
    assert result[0].ai_suggested_name == "user_id"    # Stored for reference
    assert result[0].source_name == "usr_id"           # Original preserved
```

### Documentation Updates

**When to update docs:**
- After completing major features (Phase 1, Phase 2, etc.)
- When adding new configuration options
- When changing architecture decisions
- When updating dependencies or requirements

**Files to update:**
- `docs/changelog.md` - version history (user-facing)
- `docs/project-status.md` - current progress metrics
- `docs/development-guide.md` - new practices learned
- `docs/architecture.md` - system design changes
- `docs/agent-usage-guide.md` - agent selection patterns
- `README.md` - high-level project summary

### Pull Request Best Practices

**PR Title Format:**
```
<type>: <description>

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation change
- refactor: Code restructuring
- test: Test additions/changes
```

**Examples:**
- `feat: add contract builder with user override support`
- `fix: handle null values in AI suggestions`
- `docs: update API documentation`

**PR Size Guidelines:**
- Small: < 200 lines (preferred)
- Medium: 200-500 lines (acceptable)
- Large: > 500 lines (consider splitting)

**PR Description Template:**
```markdown
## Summary
Brief description of what changes and why.

## Changes
- List of specific changes made
- Bullet points for clarity

## Testing
- How was this tested?
- What test coverage was added?

## Documentation
- What docs were updated?

## Notes
Any additional context or considerations
```

**Review Process:**
1. Author creates PR with detailed description
2. CI checks run automatically (must all pass)
3. Reviewer provides feedback
4. Author addresses feedback
5. CI checks run again (must all pass)
6. Reviewer approves
7. Maintainer merges to main

**Code Review Response Time:**
- Authors: Address feedback within 24-48 hours
- Reviewers: Provide initial review within 48-72 hours
- Critical bugs: Review and fix within 24 hours
