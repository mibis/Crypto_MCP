# Contributing to Crypto_MCP

Thank you for your interest in contributing to Crypto_MCP! This document provides guidelines and information for contributors.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Development Guidelines](#development-guidelines)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Community](#community)

## 🤝 Code of Conduct

This project follows a code of conduct to ensure a welcoming environment for all contributors. By participating, you agree to:

- Be respectful and inclusive
- Focus on constructive feedback
- Accept responsibility for mistakes
- Show empathy towards other contributors
- Help create a positive community

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- Node.js and npm (for MCP Inspector testing)
- Claude Desktop or LM Studio

### Quick Setup

```bash
# Fork and clone the repository
git clone https://github.com/mibis/Crypto_MCP.git
cd Crypto_MCP

# Set up development environment
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Test the setup
python crypto_mcp.py  # Should start without errors
```

## 🛠️ Development Setup

### Environment Setup

1. **Create virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   .venv\Scripts\activate     # Windows
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install development dependencies:**
   ```bash
   pip install pytest black flake8 mypy  # Add to requirements-dev.txt
   ```

### Testing Tools

- **MCP Inspector:** For testing MCP server functionality
- **pytest:** For unit tests
- **black:** Code formatting
- **flake8:** Linting
- **mypy:** Type checking

## 💡 How to Contribute

### Types of Contributions

- 🐛 **Bug fixes**
- ✨ **New features**
- 📚 **Documentation improvements**
- 🧪 **Tests**
- 🔧 **Tool improvements**
- 🌐 **API integrations**

### Finding Issues

- Check [GitHub Issues](https://github.com/mibis/Crypto_MCP/issues) for open tasks
- Look for issues labeled `good first issue` or `help wanted`
- Comment on issues you'd like to work on

### Feature Requests

- Open a [GitHub Issue](https://github.com/mibis/Crypto_MCP/issues) with the `enhancement` label
- Describe the feature and its use case
- Discuss implementation approach if possible

## 📝 Development Guidelines

### Code Style

- Follow [PEP 8](https://pep8.org/) style guide
- Use meaningful variable and function names
- Write comprehensive docstrings
- Keep functions focused and single-purpose

### Tool Development

When adding new tools to `crypto_mcp.py`:

1. **Use clear naming:** `get_price_[source]` pattern
2. **Comprehensive docstrings:** Include parameter types and examples
3. **Error handling:** Graceful API failure handling
4. **Parameter validation:** Check inputs before API calls
5. **Consistent returns:** Standardized response format

Example:
```python
@mcp.tool()
def get_price_new_exchange(symbol: str = "BTCUSDT"):
    """Gets cryptocurrency price from New Exchange API.

    Args:
        symbol: Trading pair symbol (e.g., 'BTCUSDT')

    Returns:
        Formatted price string with source
    """
    # Implementation here
```

### Documentation

- Update `USAGE_EXAMPLES.md` for new features
- Add inline comments for complex logic
- Update README.md if needed
- Test documentation examples

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_crypto_tools.py

# Run with coverage
pytest --cov=crypto_mcp --cov-report=html
```

### Writing Tests

- Test each tool function
- Mock external API calls
- Test error conditions
- Include edge cases

Example test structure:
```python
def test_get_crypto_price():
    # Test successful API call
    # Test error handling
    # Test parameter validation
```

### Manual Testing

Use MCP Inspector for manual testing:
```bash
npx @modelcontextprotocol/inspector --config test_config.json --server crypto-mcp
```

## 📤 Submitting Changes

### Commit Guidelines

- Use clear, descriptive commit messages
- Reference issue numbers when applicable
- Keep commits focused and atomic

Example:
```
feat: Add CoinPaprika API integration

- Add get_price_coinpaprika tool
- Update documentation
- Add usage examples

Closes #123
```

### Pull Request Process

1. **Fork the repository**
2. **Create a feature branch:**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
4. **Run tests and linting:**
   ```bash
   pytest
   black crypto_mcp.py
   flake8 crypto_mcp.py
   ```
5. **Commit your changes:**
   ```bash
   git commit -m "Add amazing feature"
   ```
6. **Push to your branch:**
   ```bash
   git push origin feature/amazing-feature
   ```
7. **Open a Pull Request**

### PR Checklist

- [ ] Tests pass
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] New features have usage examples
- [ ] Commit messages are clear
- [ ] PR description explains changes

## 🌍 Community

### Getting Help

- 📖 **Documentation:** Check [README.md](README.md) and [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md)
- 💬 **Discussions:** Use [GitHub Discussions](https://github.com/mibis/Crypto_MCP/discussions) for questions
- 🐛 **Issues:** Report bugs via [GitHub Issues](https://github.com/mibis/Crypto_MCP/issues)

### Recognition

Contributors will be recognized in:
- Repository contributors list
- Release notes
- Special mentions in documentation

## 📄 License

By contributing to this project, you agree that your contributions will be licensed under the same MIT License that covers the project.

Thank you for contributing to Crypto_MCP! 🎉