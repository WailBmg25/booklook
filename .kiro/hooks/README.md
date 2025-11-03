## Overview

This directory contains Kiro hooks that automate git operations for the BookLook project.

## Hooks

### 1. Auto Commit & Branch Manager (`auto-commit-and-branch.json`)

Automatically manages git commits and branches during development.

**Features:**
- Commits changes after every task completion
- Pushes to remote automatically
- Creates new branches when moving between phases
- Detailed commit messages with task information

**Triggers:**
- `onTaskComplete`: Runs after completing any task
- `onPhaseChange`: Runs when moving from one phase to another

### 2. Manual Phase Commit (`commit-phase-3.sh`)

Manual script to commit phase completion with detailed message.

**Usage:**
```bash
bash .kiro/hooks/commit-phase-3.sh
```

**What it does:**
- Stages all changes
- Shows status
- Creates detailed commit message
- Commits and pushes to remote
- Provides instructions for next phase

## Git Workflow

### Task Completion
When you complete a task, the hook automatically:
1. Stages all changes (`git add -A`)
2. Commits with message: `Task completed: [task name] - [description]`
3. Pushes to current branch

### Phase Transition
When moving to a new phase:
1. Commits current phase completion
2. Pushes to current branch
3. Creates new branch: `phase-[number]-[name]`
4. Pushes new branch to remote

### Manual Commit
For manual control:
```bash
# Commit current phase
bash .kiro/hooks/commit-phase-3.sh

# Create new branch for next phase
git checkout -b phase-4-frontend
git push -u origin phase-4-frontend
```

## Branch Naming Convention

- `phase-1-models` - Models Layer (Data Layer)
- `phase-2-mvc` - MVC Pattern Refactoring
- `phase-3-controllers` - FastAPI Controllers (API Layer)
- `phase-4-frontend` - Next.js Frontend
- `phase-5-testing` - Testing Suite
- `phase-6-deployment` - Docker Deployment
- `phase-7-optimization` - Performance Optimization

## Commit Message Format

### Task Completion
```
Task completed: [Task Number] [Task Name]

[Task description and details]
```

### Phase Completion
```
Phase [N] Complete: [Phase Name]

✅ [Summary of achievements]

Features:
- [Feature 1]
- [Feature 2]

Deliverables:
- [Deliverable 1]
- [Deliverable 2]

Status: [Status]
```

## Configuration

The hooks are configured in `auto-commit-and-branch.json`. You can:
- Enable/disable specific triggers
- Modify commit message templates
- Add custom actions
- Configure push behavior

## Troubleshooting

### Permission Denied Errors
If you get permission errors with docker data:
```bash
# Add to .gitignore
echo "docker/postgres_data/" >> .gitignore
echo "docker/redis_data/" >> .gitignore
```

### Push Failures
If push fails:
```bash
# Check remote configuration
git remote -v

# Set up remote if needed
git remote add origin <repository-url>

# Push manually
git push origin <branch-name>
```

### Hook Not Running
Ensure hooks are executable:
```bash
chmod +x .kiro/hooks/*.sh
```

## Best Practices

1. **Commit Often**: Let the hook commit after each task
2. **Review Changes**: Check `git status` before major commits
3. **Branch Per Phase**: Create new branch for each phase
4. **Descriptive Messages**: Use clear, detailed commit messages
5. **Push Regularly**: Keep remote in sync with local

## Phase 3 Status

✅ **Committed and Pushed**
- Branch: `backeng-phase-001`
- Commit: Phase 3 Complete - All 26 API endpoints working
- Status: Production Ready
- Next: Create `phase-4-frontend` branch

