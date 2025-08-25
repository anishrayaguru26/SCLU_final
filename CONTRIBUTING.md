# Contributing to SCLU

Thank you for your interest in contributing to SCLU! This document provides guidelines and information for contributors.

## How to Contribute

We welcome contributions in many forms:

- **Bug Reports**: Found a bug? Please let us know!
- **Feature Requests**: Have an idea for a new feature?
- **Code Contributions**: Fix bugs, add features, improve documentation
- **Documentation**: Help improve our docs
- **Testing**: Add test cases, improve test coverage
- **Performance**: Optimize algorithms, improve efficiency

## Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/yourusername/SCLU.git
cd SCLU

# Add upstream remote
git remote add upstream https://github.com/originalowner/SCLU.git
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Install the package in development mode
pip install -e .
```

### 3. Create a Branch

```bash
# Create a feature branch
git checkout -b feature/your-feature-name

# Or a bugfix branch
git checkout -b fix/issue-number-description
```

## Development Guidelines

### Code Style

We use several tools to maintain code quality:

- **Black**: Code formatting
- **Flake8**: Linting
- **MyPy**: Type checking
- **isort**: Import sorting

```bash
# Format code
black src/ tests/

# Check linting
flake8 src/ tests/

# Type checking
mypy src/

# Sort imports
isort src/ tests/
```

### Code Standards

1. **Type Hints**: Use type hints for all function parameters and return values
2. **Docstrings**: All public functions and classes must have docstrings
3. **Error Handling**: Proper exception handling with informative messages
4. **Logging**: Use the logging framework instead of print statements
5. **Testing**: Add tests for new functionality

### Example Code Structure

```python
from typing import Optional, Dict, Any
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ExampleClass:
    """
    Brief description of the class.
    
    Longer description if needed, explaining the purpose,
    usage, and any important details.
    
    Attributes:
        attribute_name: Description of the attribute
    """
    
    def __init__(self, param: str, optional_param: Optional[int] = None) -> None:
        """
        Initialize the class.
        
        Args:
            param: Description of the parameter
            optional_param: Optional parameter description
        """
        self.param = param
        self.optional_param = optional_param
    
    def public_method(self, input_data: Dict[str, Any]) -> bool:
        """
        Brief description of what the method does.
        
        Args:
            input_data: Description of the input
            
        Returns:
            bool: Description of what the return value means
            
        Raises:
            ValueError: When input_data is invalid
            RuntimeError: When operation fails
        """
        try:
            # Implementation here
            logger.info("Operation completed successfully")
            return True
        except Exception as e:
            logger.error(f"Operation failed: {e}")
            raise RuntimeError(f"Failed to process data: {e}") from e
```

## Testing

### Running Tests

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_strategies.py

# Run with coverage
python -m pytest --cov=src/sclu --cov-report=html

# Run only fast tests (skip slow integration tests)
python -m pytest -m "not slow"
```

### Writing Tests

1. **Unit Tests**: Test individual functions and classes in isolation
2. **Integration Tests**: Test component interactions
3. **End-to-End Tests**: Test complete workflows

Example test structure:

```python
import pytest
from unittest.mock import Mock, patch
from sclu.strategies import SCLUStrategy


class TestSCLUStrategy:
    """Test cases for SCLU trading strategy."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.strategy = SCLUStrategy()
    
    def test_initialization(self):
        """Test strategy initialization."""
        assert self.strategy is not None
        assert hasattr(self.strategy, 'params')
    
    @patch('sclu.api.KiteClient')
    def test_signal_generation(self, mock_kite):
        """Test trading signal generation."""
        # Mock setup
        mock_kite.return_value.fetch_data.return_value = self._get_sample_data()
        
        # Test execution
        signal = self.strategy.generate_signal()
        
        # Assertions
        assert signal in ['BUY', 'SELL', 'HOLD']
    
    def _get_sample_data(self):
        """Helper method to get sample data for testing."""
        return {
            'close': 100.0,
            'oi': 1000000,
            'doi': -50.0,
            'd2oi': -10.0
        }
```

## Documentation

### Docstring Format

We use Google-style docstrings:

```python
def example_function(param1: str, param2: int) -> bool:
    """
    Brief description of the function.
    
    Longer description explaining the function's purpose,
    behavior, and any important details.
    
    Args:
        param1: Description of the first parameter
        param2: Description of the second parameter
        
    Returns:
        bool: Description of what the return value represents
        
    Raises:
        ValueError: When param1 is empty
        TypeError: When param2 is negative
        
    Example:
        >>> result = example_function("test", 42)
        >>> print(result)
        True
    """
```

### Documentation Updates

- Update docstrings when changing function signatures
- Add examples for complex functions
- Update README.md for user-facing changes
- Add entries to CHANGELOG.md for notable changes

## Reporting Issues

### Before Reporting

1. **Search existing issues** to avoid duplicates
2. **Check the latest version** to see if the issue is already fixed
3. **Test with minimal example** to isolate the problem

### Issue Template

```markdown
## Bug Description
Brief description of what went wrong.

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Expected Behavior
What should have happened.

## Actual Behavior
What actually happened.

## Environment
- Python version:
- SCLU version:
- Operating System:
- Relevant dependencies:

## Additional Context
Any other context, logs, or screenshots.
```

## Pull Request Process

### Before Submitting

1. **Run tests**: Ensure all tests pass
2. **Check code style**: Run linting and formatting tools
3. **Update documentation**: Add/update docstrings and docs
4. **Add tests**: Include tests for new functionality
5. **Update changelog**: Add entry to CHANGELOG.md

### Pull Request Template

```markdown
## Description
Brief description of changes made.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Performance improvement

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All tests pass locally
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings introduced
- [ ] Backwards compatibility maintained
```

### Review Process

1. **Automated checks** must pass (CI/CD pipeline)
2. **Code review** by at least one maintainer
3. **Discussion** of design decisions if needed
4. **Approval** and merge by maintainer

## Security

### Reporting Security Issues

Please **DO NOT** report security vulnerabilities in public issues.

Instead:
- Email security concerns to: security@example.com
- Use responsible disclosure practices
- Allow time for fixes before public disclosure

### Security Guidelines

- Never commit API keys or secrets
- Use environment variables for sensitive data
- Validate all user inputs
- Follow secure coding practices

## Development Workflow

### Typical Workflow

1. **Issue Discussion**: Discuss features/bugs in issues
2. **Design Review**: For large changes, create design document
3. **Implementation**: Write code following guidelines
4. **Testing**: Add comprehensive tests
5. **Review**: Submit PR for code review
6. **Merge**: Maintainer merges after approval

### Release Process

1. **Version Bump**: Update version numbers
2. **Changelog**: Update CHANGELOG.md
3. **Testing**: Run full test suite
4. **Tag Release**: Create git tag
5. **Deploy**: Publish to PyPI (maintainers only)

## Labels and Milestones

### Issue Labels

- `bug`: Something isn't working
- `enhancement`: New feature or request
- `documentation`: Improvements to documentation
- `good first issue`: Good for newcomers
- `help wanted`: Extra attention is needed
- `priority-high`: High priority issue
- `priority-low`: Low priority issue

### Pull Request Labels

- `work-in-progress`: PR is not ready for review
- `ready-for-review`: PR is ready for review
- `needs-changes`: PR needs changes before merge
- `approved`: PR is approved and ready to merge

## Community Guidelines

### Code of Conduct

- **Be respectful**: Treat everyone with respect
- **Be constructive**: Provide helpful feedback
- **Be patient**: Remember that people have different skill levels
- **Be collaborative**: Work together towards common goals

### Communication

- **Issues**: For bug reports and feature requests
- **Discussions**: For questions and general discussion
- **Pull Requests**: For code review and collaboration
- **Discord/Slack**: For real-time community chat (if available)

## Getting Help

Need help contributing? Here's where to get support:

1. **Documentation**: Check the [docs/](docs/) directory
2. **Issues**: Search existing issues for similar problems
3. **Discussions**: Ask questions in GitHub Discussions
4. **Community**: Join our community chat (if available)

## Recognition

Contributors will be recognized in:

- **README.md**: Contributors section
- **CHANGELOG.md**: Release notes
- **GitHub**: Contributor statistics
- **Special recognition**: For significant contributions

Thank you for contributing to SCLU!
