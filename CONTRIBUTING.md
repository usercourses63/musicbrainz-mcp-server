# Contributing to MusicBrainz MCP Server

Thank you for your interest in contributing to the MusicBrainz MCP Server! This document provides guidelines and information for contributors.

## 🤝 How to Contribute

### Types of Contributions

We welcome several types of contributions:

- **Bug Reports**: Help us identify and fix issues
- **Feature Requests**: Suggest new functionality
- **Code Contributions**: Implement features or fix bugs
- **Documentation**: Improve or add documentation
- **Testing**: Add or improve test coverage
- **Performance**: Optimize existing code

### Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Create a feature branch** from `main`
4. **Make your changes** with proper tests
5. **Submit a pull request**

## 🛠️ Development Setup

### Prerequisites

- Python 3.8+
- Git
- Virtual environment tool (venv, conda, etc.)

### Local Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/MusicBrainzMcp.git
cd MusicBrainzMcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Set up environment
export MUSICBRAINZ_USER_AGENT="DevApp/1.0.0 (dev@localhost)"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=musicbrainz_mcp --cov-report=html

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m "not api"     # Skip API tests (no network)

# Run tests with verbose output
pytest -v

# Run specific test file
pytest tests/test_client.py
```

### Code Quality

We use several tools to maintain code quality:

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/

# Run all quality checks
pre-commit run --all-files
```

## 📝 Coding Standards

### Code Style

- **Follow PEP 8** for Python code style
- **Use Black** for code formatting (line length: 88)
- **Use isort** for import sorting
- **Use type hints** for all function parameters and return values
- **Write docstrings** for all public functions and classes

### Example Code Style

```python
from typing import List, Optional, Dict, Any
import asyncio
from dataclasses import dataclass

@dataclass
class ExampleClass:
    """Example class demonstrating coding standards.
    
    Args:
        name: The name of the example
        value: Optional numeric value
    """
    name: str
    value: Optional[int] = None
    
    async def process_data(
        self, 
        data: List[Dict[str, Any]], 
        limit: int = 10
    ) -> List[str]:
        """Process data and return results.
        
        Args:
            data: List of data dictionaries to process
            limit: Maximum number of items to process
            
        Returns:
            List of processed result strings
            
        Raises:
            ValueError: If data is empty or invalid
        """
        if not data:
            raise ValueError("Data cannot be empty")
            
        results = []
        for item in data[:limit]:
            if "name" in item:
                results.append(f"{self.name}: {item['name']}")
                
        return results
```

### Documentation Standards

- **Use Google-style docstrings** for functions and classes
- **Include type information** in docstrings
- **Provide examples** for complex functions
- **Document exceptions** that may be raised
- **Keep README.md updated** with new features

### Testing Standards

- **Write tests for all new code**
- **Aim for >90% test coverage**
- **Use descriptive test names**
- **Test both success and failure cases**
- **Mock external dependencies**

Example test:

```python
import pytest
from unittest.mock import AsyncMock, patch
from musicbrainz_mcp.client import MusicBrainzClient

class TestMusicBrainzClient:
    """Test suite for MusicBrainzClient."""
    
    @pytest.mark.asyncio
    async def test_search_artist_success(self):
        """Test successful artist search."""
        client = MusicBrainzClient(user_agent="TestApp/1.0.0")
        
        with patch.object(client._client, 'get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"artists": []}
            mock_get.return_value = mock_response
            
            result = await client.search_artist("test")
            
            assert "artists" in result
            mock_get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_artist_rate_limit_error(self):
        """Test rate limit error handling."""
        client = MusicBrainzClient(user_agent="TestApp/1.0.0")
        
        with patch.object(client._client, 'get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status_code = 429
            mock_get.return_value = mock_response
            
            with pytest.raises(MusicBrainzRateLimitError):
                await client.search_artist("test")
```

## 🐛 Bug Reports

### Before Submitting a Bug Report

1. **Check existing issues** to avoid duplicates
2. **Update to the latest version** to see if the bug persists
3. **Test with minimal configuration** to isolate the issue
4. **Gather relevant information** (logs, environment, steps to reproduce)

### Bug Report Template

```markdown
## Bug Description
A clear description of what the bug is.

## Steps to Reproduce
1. Set environment variable X to Y
2. Run command Z
3. Observe error

## Expected Behavior
What you expected to happen.

## Actual Behavior
What actually happened.

## Environment
- OS: [e.g., Ubuntu 20.04]
- Python version: [e.g., 3.11.0]
- Package version: [e.g., 1.0.0]
- MusicBrainz API response time: [if relevant]

## Additional Context
- Configuration files
- Log output
- Screenshots (if applicable)
```

## 🚀 Feature Requests

### Before Submitting a Feature Request

1. **Check existing issues** for similar requests
2. **Consider the scope** - does it fit the project goals?
3. **Think about implementation** - is it technically feasible?
4. **Provide use cases** - why is this feature needed?

### Feature Request Template

```markdown
## Feature Description
A clear description of the feature you'd like to see.

## Use Case
Describe the problem this feature would solve.

## Proposed Solution
How you envision this feature working.

## Alternative Solutions
Other approaches you've considered.

## Additional Context
- Examples from other projects
- Mock-ups or diagrams
- Implementation ideas
```

## 🔧 Pull Request Process

### Before Submitting a Pull Request

1. **Create an issue** to discuss the change (for significant features)
2. **Fork the repository** and create a feature branch
3. **Write tests** for your changes
4. **Update documentation** if needed
5. **Run the test suite** to ensure nothing breaks
6. **Follow the coding standards**

### Pull Request Template

```markdown
## Description
Brief description of changes made.

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] New tests added for new functionality
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings introduced
```

### Review Process

1. **Automated checks** must pass (tests, linting, etc.)
2. **Code review** by maintainers
3. **Address feedback** and make requested changes
4. **Final approval** and merge

## 🏗️ Development Workflow

### Branch Naming

- `feature/description` - New features
- `bugfix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring

### Commit Messages

Use conventional commit format:

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

Examples:
```
feat(client): add retry logic for rate limited requests

fix(server): handle invalid MBID format gracefully

docs(api): update search_artist documentation with examples

test(integration): add real API integration tests
```

## 🧪 Testing Guidelines

### Test Categories

1. **Unit Tests**: Test individual functions/classes in isolation
2. **Integration Tests**: Test component interactions
3. **API Tests**: Test real MusicBrainz API integration (marked with `@pytest.mark.api`)
4. **Performance Tests**: Test performance characteristics

### Writing Good Tests

```python
# Good test example
@pytest.mark.asyncio
async def test_search_artist_with_pagination(self, mock_client):
    """Test artist search with pagination parameters."""
    # Arrange
    expected_query = "The Beatles"
    expected_limit = 50
    expected_offset = 25
    
    # Act
    result = await mock_client.search_artist(
        query=expected_query,
        limit=expected_limit,
        offset=expected_offset
    )
    
    # Assert
    assert result is not None
    mock_client._make_request.assert_called_once_with(
        "artist",
        params={
            "query": expected_query,
            "limit": expected_limit,
            "offset": expected_offset
        }
    )
```

### Test Data

- Use **mock data** for unit tests
- Use **real API responses** (cached) for integration tests
- Keep test data **minimal but realistic**
- Store test data in `tests/mock_data.py`

## 📚 Documentation Guidelines

### Types of Documentation

1. **API Reference**: Complete function/class documentation
2. **User Guides**: How-to guides for common tasks
3. **Examples**: Practical usage examples
4. **Configuration**: Setup and configuration options

### Documentation Standards

- **Use Markdown** for all documentation
- **Include code examples** with expected output
- **Keep examples up-to-date** with current API
- **Use clear, concise language**
- **Provide context** for why something is useful

## 🚀 Release Process

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Run full test suite
4. Create release tag
5. Build and publish package
6. Update documentation

## 🤔 Questions and Support

### Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Documentation**: Check existing docs first

### Community Guidelines

- **Be respectful** and inclusive
- **Help others** when you can
- **Stay on topic** in discussions
- **Provide context** when asking questions

## 📄 License

By contributing to this project, you agree that your contributions will be licensed under the same license as the project (MIT License).

## 🙏 Recognition

Contributors will be recognized in:
- `CONTRIBUTORS.md` file
- Release notes for significant contributions
- GitHub contributor statistics

Thank you for contributing to the MusicBrainz MCP Server! 🎵
