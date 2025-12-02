# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2025-12-02

### Added
- Initial release
- Real-time voice conversation with Google Gemini Live API
- WebSocket bidirectional communication
- Manual Voice Activity Detection (VAD) integration
- Audio streaming (PCM 16kHz input, 24kHz output)
- Real-time transcription (input and output)
- FastAPI backend with clean architecture
- Comprehensive test suite with pytest (80%+ coverage target)
- Type hints throughout entire codebase (90%+ coverage)
- Pre-commit hooks for code quality enforcement
- Docker and docker-compose support for easy deployment
- Pydantic-based configuration management with validation
- Custom exception hierarchy for better error handling
- UV-based dependency management (10-100x faster than pip)
- Ruff for linting and formatting (replaces black + isort + flake8)
- Mypy for static type checking
- GitHub Actions CI/CD with matrix testing (Python 3.11-3.13)
- Codecov integration for coverage tracking
- Comprehensive documentation (README, ARCHITECTURE, CONTRIBUTING, CHANGELOG, SECURITY)
- MIT License
- GitHub community templates (issue templates, PR template)
- Code of Conduct (Contributor Covenant)

### Technical Details
- FastAPI for web framework
- WebSockets for real-time communication
- Google Gemini 2.0 Flash Exp model
- Spanish language support (es-US)
- Aoede voice model
- Python 3.11-3.13 support
- pyproject.toml (PEP 517/518 standard)

### Security
- Bandit security scanning in CI/CD
- Proper exception handling (no bare exceptions)
- Validation for environment variables
- Security policy documentation (SECURITY.md)

[Unreleased]: https://github.com/icapora/gemini-workshop/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/icapora/gemini-workshop/releases/tag/v1.0.0
