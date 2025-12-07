# Contributing to Home Assistant Vibecode Agent

Thank you for your interest in contributing to the HomeAssistant Vibecode Agent! Contributions are welcome and greatly appreciated.

## 🤝 How to Contribute

We welcome contributions of all kinds:
- 🐛 Bug fixes
- ✨ New features
- 📝 Documentation improvements
- 🧪 Tests
- 💡 Ideas and suggestions

## 🚀 Getting Started

### 1. Fork and Clone

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:

```bash
git clone https://github.com/YOUR_USERNAME/home-assistant-vibecode-agent.git
cd home-assistant-vibecode-agent
```

3. **Add the upstream repository** (to sync with main project):

```bash
git remote add upstream https://github.com/Coolver/home-assistant-vibecode-agent.git
```

### 2. Create a Branch

Create a new branch for your changes:

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

Use descriptive branch names:
- `feature/add-new-endpoint` - for new features
- `fix/authentication-issue` - for bug fixes
- `docs/update-api-docs` - for documentation
- `refactor/improve-error-handling` - for refactoring

### 3. Make Your Changes

- Write clean, readable code
- Follow existing code style (PEP 8 for Python)
- Add comments for complex logic
- Update documentation if needed
- Add tests for new features

### 4. Test Your Changes

Before submitting, make sure:

- ✅ Code runs without errors
- ✅ Existing tests still pass
- ✅ New functionality is tested
- ✅ Documentation is updated

### 5. Commit Your Changes

Write clear, descriptive commit messages:

```bash
git commit -m "Add feature: description of what you did"
```

Good commit messages:
- Start with a verb (Add, Fix, Update, Remove)
- Be specific about what changed
- Keep the first line under 72 characters
- Add more details in the body if needed

Example:
```
Add support for custom commit messages in automation creation

- Extract commit_message from request body
- Pass to git_manager for meaningful Git history
- Update API documentation
```

### 6. Push and Create Pull Request

1. **Push your branch** to your fork:

```bash
git push origin feature/your-feature-name
```

2. **Create a Pull Request** on GitHub:
   - Go to the original repository
   - Click "New Pull Request"
   - Select your fork and branch
   - Fill out the PR template (if available)
   - Describe your changes clearly

## 📋 Pull Request Guidelines

### PR Description

Your PR description should include:

- **What** - What changes did you make?
- **Why** - Why are these changes needed?
- **How** - How did you implement the changes?
- **Testing** - How was it tested?

### Code Review Process

1. Maintainers will review your PR
2. Address any feedback or requested changes
3. Once approved, your PR will be merged

### PR Checklist

Before submitting, ensure:

- [ ] Code follows the project's style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated (if needed)
- [ ] Tests added/updated (if applicable)
- [ ] No new warnings or errors
- [ ] Commit messages are clear

## 💻 Development Setup

See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed setup instructions.

## 🐛 Reporting Bugs

### Before Reporting

1. Check if the bug has already been reported
2. Test with the latest version
3. Gather relevant information (logs, error messages, steps to reproduce)

### Bug Report Template

When reporting a bug, include:

- **Description**: Clear description of the bug
- **Steps to Reproduce**: Detailed steps to reproduce the issue
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens
- **Environment**: Home Assistant version, add-on version, OS
- **Logs**: Relevant error logs or stack traces
- **Screenshots**: If applicable

## 💡 Feature Requests

### Suggesting Features

We welcome feature suggestions! When proposing a feature:

1. **Check** if it's already been suggested
2. **Describe** the feature clearly
3. **Explain** the use case and benefits
4. **Consider** implementation complexity

### Feature Request Template

- **Feature Description**: What should the feature do?
- **Use Case**: Why is this feature needed?
- **Proposed Solution**: How should it work?
- **Alternatives**: Other solutions you've considered

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🙏 Thank You!

Your contributions make this project better for everyone. Thank you for taking the time to contribute!

**Happy coding!** 🚀

