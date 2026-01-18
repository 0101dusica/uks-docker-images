# Contributing

This document defines the development rules and workflow for this project.
Its purpose is to ensure clear change tracking, consistent versioning, and alignment with software configuration management principles.

All contributions must follow the rules described below.

---

## 1. Branching Model

The project follows a GitFlow-inspired branching strategy.

### Main Branches

- **main**  
  Contains stable, production-ready code.

- **develop**  
  Contains the latest development changes and serves as the integration branch.

Direct commits to these branches are not allowed.

---

### Milestone Branches

For each major milestone, a dedicated branch can be created:

```
milestone/M{milestone}
```

Examples:
```
milestone/M1
milestone/M2
```

Milestone branch workflow:

- The milestone branch is created from `develop` at the start of the milestone
- All feature/bugfix branches for that milestone are created from the corresponding milestone branch
- When a task is completed, the feature/bugfix branch is merged into the milestone branch (not directly into develop)
- When all tasks for the milestone are finished and tested, the milestone branch is merged into `develop`
- If needed, the milestone branch should be periodically updated from develop to resolve conflicts

This approach enables parallel work on multiple tasks within a milestone and makes integration and testing easier before merging into develop.

## 2. Issues and Milestones

- Every functionality or fix must be created as a **GitHub Issue**
- Each issue must be assigned to a **GitHub Milestone**
- One issue represents one logical unit of work
- Development must always start from an existing issue

This ensures full traceability between the project specification, implementation, and version history.

---

## 3. Branch Naming Convention

Each issue is implemented in a separate branch created from the `develop` branch.

### Feature Branches

```
feature/M{milestone}-I{issue}-{short-description}
```

Examples:
```
feature/M1-I1-initialize-gitflow
feature/M2-I3-user-authentication
feature/M5-I4-delete-repository
```

### Bugfix Branches

```
bugfix/M{milestone}-I{issue}-{short-description}
```

Example:
```
bugfix/M4-I2-search-filter-fix
```

### Other Branches

- `hotfix/*` – critical fixes for production
- `release/*` – preparation for a release version

---

## 4. Commit Message Rules


Commit messages must be clear, written in English, and directly linked to an issue.

### Commit Format

```
[M{milestone}-I{issue}] Short description
```

Examples:
```
[M1-I1] Initialize GitFlow structure
[M2-I3] Implement user login endpoint
[M5-I4] Add repository deletion logic
```

Commits should be small and focused on a single change.

---

## 5. Pull Request Workflow


- Pull Requests must be opened against the `develop` branch
- Each Pull Request must reference the related GitHub Issue (add a link in the PR description)
- The PR description should contain a brief summary of the solution
- One Pull Request should resolve one issue
- Code review is required before merging
- After merging, the feature or bugfix branch should be deleted

---

## 6. General Development Rules

- Do not commit directly to `main` or `develop`
- Follow the defined branch naming rules
- Keep commits clean and meaningful
- Ensure the application builds and runs before opening a Pull Request

---

## 7. Code Style and Naming Conventions

For all Python/Django code, follow the [PEP8](https://peps.python.org/pep-0008/) style guide:

- Use `snake_case` for variable and function names (e.g., `user_name`, `get_user_profile`)
- Use `PascalCase` (CapWords) for class names (e.g., `UserProfile`)
- Constants should be in `UPPER_CASE`
- Write all code and comments in English
- Use 4 spaces for indentation

This ensures consistency and readability across the codebase.


## 7. Goal of This Workflow

This workflow is designed to:
- Enable controlled and transparent change management
- Provide clear traceability of features and fixes
- Support collaborative development
- Demonstrate proper software configuration management practices
