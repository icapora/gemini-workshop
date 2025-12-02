# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive test suite with pytest (80%+ coverage target)
- Type hints throughout entire codebase (90%+ coverage)
- Pre-commit hooks for code quality enforcement
- Docker and docker-compose support for easy deployment
- Pydantic-based configuration management with validation
- Custom exception hierarchy for better error handling
- CHANGELOG.md for tracking project changes
- SECURITY.md with security policy and reporting guidelines
- UV-based dependency management (10-100x faster than pip)
- Ruff for linting and formatting (replaces black + isort + flake8)
- Mypy for static type checking
- GitHub Actions CI/CD with matrix testing (Python 3.11-3.13)
- Codecov integration for coverage tracking

### Changed
- Migrated from Pipfile to pyproject.toml (PEP 517/518 standard)
- Replaced black + isort + flake8 with Ruff (single tool, 60-80% faster CI)
- Added mypy for static type checking throughout codebase
- Improved CI/CD pipeline with UV and faster builds
- Enhanced error handling with custom exceptions
- Configurable settings via Pydantic (no more magic numbers)
- Python version support broadened to 3.11-3.13 (was 3.13-only)

### Fixed
- **CRITICAL**: Bare exception handler in websocket.py (line 138)
  - Changed from `except: pass` to `except Exception:` with proper logging
  - No longer silently swallows errors
- Missing type hints across codebase (added 90%+ coverage)
- Loose version pinning (`=="*"` → proper semantic versioning)
- Magic number 160000 → configurable `settings.flush_interval_bytes`
- Function attribute mutation → proper closure variable with `nonlocal`
- Late imports → moved `import time` to module level

### Security
- Added Bandit security scanning in CI/CD
- Implemented proper exception handling (no more bare exceptions)
- Added validation for environment variables
- Security policy documentation (SECURITY.md)

## [1.0.0] - 2024-12-02

### Added
- Initial release
- Real-time voice conversation with Google Gemini Live API
- WebSocket bidirectional communication
- Manual Voice Activity Detection (VAD) integration
- Audio streaming (PCM 16kHz input, 24kHz output)
- Real-time transcription (input and output)
- FastAPI backend with clean architecture
- Comprehensive documentation (README, ARCHITECTURE, CONTRIBUTING)
- MIT License
- GitHub community templates (issue templates, PR template)
- Code of Conduct (Contributor Covenant)

### Technical Details
- FastAPI for web framework
- WebSockets for real-time communication
- Google Gemini 2.0 Flash Exp model
- Spanish language support (es-US)
- Aoede voice model

[Unreleased]: https://github.com/YOUR_USERNAME/gemini-live-workshop/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/YOUR_USERNAME/gemini-live-workshop/releases/tag/v1.0.0
