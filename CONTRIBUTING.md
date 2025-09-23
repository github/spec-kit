# Contributing to Spec Kit

We welcome contributions to the Spec Kit Azure DevOps extension! This document provides guidelines for contributing to the project.

## 🚀 Getting Started

### Prerequisites
- Node.js 18+ and npm 8+
- Visual Studio Code (recommended)
- Azure DevOps organization for testing
- Git knowledge and GitHub account

### Development Setup
1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/spec-kit.git`
3. Install dependencies: `npm install`
4. Create a feature branch: `git checkout -b feature/your-feature-name`

## 📋 Development Guidelines

### Code Style
- Use TypeScript for all new code
- Follow existing naming conventions
- Use meaningful variable and function names
- Add comprehensive JSDoc comments for public APIs
- Maintain consistent indentation (2 spaces)

### Testing Requirements
- Write unit tests for all new functionality
- Maintain minimum 80% code coverage
- Add integration tests for Azure DevOps API interactions
- Test both success and error scenarios
- Use Jest testing framework with provided setup

### Commit Messages
Follow conventional commit format:
```
type(scope): description

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Examples:
- `feat(hub): add workflow execution history`
- `fix(tab): handle missing work item fields`
- `docs(readme): update installation instructions`

## 🔧 Architecture Guidelines

### Service Layer Design
- Keep services focused on single responsibilities
- Use dependency injection for testability
- Implement proper error handling and logging
- Follow async/await patterns for API calls

### UI Components
- Use semantic HTML and accessible patterns
- Follow Azure DevOps UI guidelines and styling
- Implement proper loading states and error handling
- Ensure responsive design for different screen sizes

### API Integration
- Use Azure DevOps REST API clients where available
- Implement proper retry logic for network failures
- Add comprehensive error handling and user feedback
- Follow rate limiting and quota guidelines

## 🧪 Testing Strategy

### Unit Tests
```bash
npm test                    # Run all tests
npm run test:watch         # Watch mode
npm run test:coverage      # Coverage report
```

### Integration Tests
- Test Azure DevOps API integrations
- Verify extension loading and initialization
- Test workflow execution end-to-end
- Validate service connection configurations

### Manual Testing
- Test in Azure DevOps environment
- Verify all extension surfaces (hub, tab, widgets)
- Test with different user permissions
- Validate LLM integration functionality

## 📝 Documentation

### Code Documentation
- Add JSDoc comments for all public methods
- Document complex algorithms and business logic
- Include usage examples in comments
- Keep documentation up-to-date with code changes

### User Documentation
- Update README.md for new features
- Add configuration examples
- Include troubleshooting guides
- Provide migration guides for breaking changes

## 🚦 Pull Request Process

### Before Submitting
1. Ensure all tests pass: `npm test`
2. Run linting: `npm run lint`
3. Build successfully: `npm run build`
4. Update documentation if needed
5. Add/update tests for new functionality

### PR Requirements
- Clear description of changes made
- Reference related issues (fixes #123)
- Include screenshots for UI changes
- Ensure CI/CD pipeline passes
- Request review from maintainers

### Review Process
1. Automated checks must pass
2. Code review by maintainers
3. Manual testing verification
4. Documentation review
5. Final approval and merge

## 🐛 Bug Reports

### Bug Report Template
```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. See error

**Expected behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment:**
- Azure DevOps version: [e.g. Azure DevOps Services]
- Extension version: [e.g. 1.0.0]
- Browser: [e.g. Chrome 91]

**Additional context**
Any other context about the problem.
```

## ✨ Feature Requests

### Feature Request Template
```markdown
**Is your feature request related to a problem?**
A clear description of what the problem is.

**Describe the solution you'd like**
A clear description of what you want to happen.

**Describe alternatives you've considered**
Other solutions you've considered.

**Additional context**
Screenshots, mockups, or other context.
```

## 🔒 Security Guidelines

### Security Best Practices
- Never commit API keys or secrets
- Use Azure DevOps service connections for external APIs
- Validate all user inputs
- Implement proper authentication checks
- Follow OWASP security guidelines

### Reporting Security Issues
- Email security issues to: security@example.com
- Do not create public issues for security vulnerabilities
- Provide detailed reproduction steps
- Allow reasonable time for fixes before disclosure

## 📋 Code Review Checklist

### Functionality
- [ ] Feature works as intended
- [ ] Edge cases are handled
- [ ] Error scenarios are covered
- [ ] Performance is acceptable

### Code Quality
- [ ] Code follows project conventions
- [ ] Functions are well-named and focused
- [ ] Comments explain complex logic
- [ ] No code duplication

### Testing
- [ ] Unit tests cover new functionality
- [ ] Tests are meaningful and comprehensive
- [ ] Manual testing completed
- [ ] No regression in existing functionality

### Documentation
- [ ] README updated if needed
- [ ] Code comments are clear
- [ ] API documentation updated
- [ ] Breaking changes documented

## 🎯 Contribution Areas

### High Priority
- Performance optimizations
- Additional LLM provider integrations
- Enhanced error handling and user feedback
- Accessibility improvements
- Mobile/responsive design enhancements

### Medium Priority
- Additional dashboard widgets
- Extended workflow customization
- Enhanced analytics and reporting
- Integration with other Azure services
- Advanced guardrails and compliance features

### Enhancement Ideas
- Multi-language support
- Custom prompt template designer
- Advanced cost optimization
- Real-time collaboration features
- Enhanced audit and compliance reporting

## 🤝 Community

### Communication Channels
- **GitHub Discussions**: General questions and ideas
- **GitHub Issues**: Bug reports and feature requests
- **Pull Requests**: Code contributions and reviews
- **Email**: For sensitive or security-related matters

### Recognition
- Contributors will be acknowledged in release notes
- Significant contributions recognized in README
- Open source contribution badges available
- Annual contributor appreciation events

## 📄 License

By contributing to Spec Kit, you agree that your contributions will be licensed under the MIT License.

Thank you for contributing to Spec Kit! 🚀