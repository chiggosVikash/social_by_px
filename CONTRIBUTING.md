# Contributing to Social by PX

First off, thank you for considering contributing to Social by PX! It's people like you that make open source such a great community to learn, inspire, and create.

This document provides guidelines and instructions for contributing to this project.

## Code of Conduct

By participating in this project, you are expected to uphold our Code of Conduct. Please treat all contributors with respect, maintain constructive discussions, and foster a welcoming environment for everyone.

## Getting Started

### 1. Fork and Clone

1. Fork the repository on GitHub.
2. Clone your fork locally:
   ```bash
   git clone https://github.com/your-username/social_by_px.git
   cd social_by_px
   ```

### 2. Set Up the Development Environment

Please refer to the [README.md](./README.md) for detailed instructions on setting up both the FastAPI backend (`apps/api`) and the Next.js frontend (`apps/web`).

## Development Workflow

### 1. Create a Branch

Create a new branch for your feature or bug fix:
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 2. Follow Architectural Patterns

This project adheres to SOLID principles and Gang of Four (GoF) design patterns. Please ensure your contributions maintain these standards:

#### Backend (`apps/api`)

- **Repository Pattern**: Never write SQLAlchemy `select` or `commit` statements in FastAPI routers. Use the classes in `src/repositories/`.
- **Strategy & Factory Patterns**: If adding a new social media publisher or a new search integration, extend the `SocialPublisher` or `SearchService` abstract base classes. Register your new strategy in the respective Factory.
- **Single Responsibility Principle**: Keep routers thin. Move business logic to services or LangGraph agents.
- **Dependency Injection**: Use FastAPI `Depends()` for injecting repositories and database sessions.
- **Code Style**: We use standard Python formatting tools. Be sure your code is clean and typed.

#### Frontend (`apps/web`)

- **React Server Components (RSC)**: Keep data fetching in Server Components (`page.tsx`) where appropriate, and interactivity in Client Components (`"use client"`).
- **State Management**: Use Zustand (`src/store/`) for global state management.
- **UI Framework**: Use **shadcn/ui** for building reusable React components.
- **Styling**: Use **Tailwind CSS** for styling. Avoid custom CSS files unless strictly necessary.
- **Code Style**: Run `pnpm lint` before pushing your changes to ensure no ESLint errors exist.

### 3. Commit Your Changes

Write clean, descriptive commit messages. We recommend following [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `refactor:` for code refactoring
- `chore:` for updating build tasks, package manager configs, etc.

Example:
```bash
git commit -m "feat(api): add LinkedIn publisher strategy"
```

### 4. Push to Your Fork

```bash
git push origin feature/your-feature-name
```

## Submitting a Pull Request

1. Go to the original Social by PX repository on GitHub.
2. Click "New Pull Request".
3. Select your fork and branch.
4. Fill out the PR template. Provide clear details about the problem you are solving, the approach you took, and how to test your changes.
5. Request a review from the maintainers.

## Reporting Bugs

If you find a bug, please create an issue on GitHub. Include:
- A clear, descriptive title.
- Steps to reproduce the issue.
- Expected vs actual behavior.
- Relevant logs, screenshots, or environment details.

## Requesting Features

Have an idea for a new feature? We'd love to hear it! Open an issue using the "Feature Request" label and describe your idea in detail, including the use case and potential technical approach.

Thank you for contributing!
