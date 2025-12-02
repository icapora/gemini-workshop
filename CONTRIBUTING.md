# Contributing to Gemini Workshop

Thank you for your interest in contributing to Gemini Workshop! We welcome contributions from the community.

## Code of Conduct

This project adheres to a Code of Conduct. By participating, you are expected to uphold this code. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with the following information:
- A clear and descriptive title
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Your environment (OS, Python version, etc.)
- Any relevant logs or error messages

### Suggesting Enhancements

We welcome suggestions for enhancements! Please create an issue with:
- A clear and descriptive title
- A detailed description of the proposed enhancement
- Any relevant examples or mockups
- Why this enhancement would be useful

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Set up your development environment**:
   ```bash
   # Clone your fork
   git clone https://github.com/YOUR_USERNAME/gemini-workshop.git
   cd gemini-workshop

   # Install dependencies
   uv sync
   ```

3. **Make your changes**:
   - Write clear, commented code
   - Follow the existing code style
   - Add tests if applicable
   - Update documentation as needed

4. **Test your changes**:
   - Ensure the application runs correctly
   - Test all affected functionality
   - Verify no new errors or warnings

5. **Commit your changes**:
   - Use clear and meaningful commit messages
   - Follow conventional commit format (e.g., `feat:`, `fix:`, `docs:`, `refactor:`)

6. **Push to your fork** and submit a pull request

### Pull Request Guidelines

- Fill out the PR template completely
- Link any related issues
- Ensure CI checks pass
- Request review from maintainers
- Be responsive to feedback

## Development Setup

### Prerequisites

- Python 3.8 or higher
- A Google Cloud project with Gemini API access
- API credentials

### Environment Setup

1. Copy `.env.example` to `.env`
2. Add your API credentials
3. Install dependencies: `uv sync`
4. Run the application: `uv run uvicorn main:app --reload`

## Code Style

- Follow PEP 8 guidelines for Python code
- Use meaningful variable and function names
- Write docstrings for functions and classes
- Keep functions focused and modular
- Comment complex logic

## Testing

Before submitting a PR, please test:
- Application startup
- WebSocket connections
- Audio streaming functionality
- Error handling
- Edge cases

## Documentation

- Update README.md if you change functionality
- Add inline comments for complex code
- Update ARCHITECTURE.md if you modify the system design

## Questions?

Feel free to open an issue with the "question" label if you have any questions about contributing.

Thank you for contributing! 🎉
