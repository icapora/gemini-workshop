# Real-time conversation

<div align="center">

![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Gemini](https://img.shields.io/badge/Google-Gemini%202.0-orange.svg)
![Code Style](https://img.shields.io/badge/code%20style-ruff-000000.svg)
![Type Checked](https://img.shields.io/badge/type%20checked-mypy-blue.svg)
[![codecov](https://codecov.io/gh/isaias-alt/gemini-workshop/branch/master/graph/badge.svg)](https://codecov.io/gh/isaias-alt/gemini-workshop)
![UV](https://img.shields.io/badge/deps-uv-green.svg)

**A production-ready, real-time voice conversation application powered by Google's Gemini Live API**

[Features](#-features) • [Demo](#-demo) • [Quick Start](#-quick-start) • [Examples](#-example-use-cases) • [Development](#-development) • [Architecture](#-architecture) • [Contributing](#-contributing)

</div>

---

## 🌟 Features

### Core Functionality

- 🎤 **Continuous Audio Streaming** - No push-to-talk, just natural conversation
- 📝 **Real-time Transcriptions** - See what you say and what Gemini responds
- 🔊 **Audio Responses** - Hear Gemini's voice responses in real-time
- 🔄 **Bidirectional WebSocket** - Low-latency full-duplex communication
- 🎯 **Client-side VAD** - Silero VAD v5 for accurate voice activity detection
- 🌐 **Web-based Interface** - No installation required for end users

### UI Features

- 🎥 **Video Call Layout** - Dual-panel interface (User + Gemini) with real-time visualizations
- 📊 **Audio Visualizers** - Animated frequency bars showing input/output audio levels
- 💬 **Flexible Chat Panel** - Toggle between bottom and side layouts
- 🎛️ **Settings Modal** - Configure streaming mode, periodic flush, and chat layout
- 🔄 **Auto-Reconnection** - Automatic reconnection with exponential backoff
- ⏱️ **Connection Stats** - Live connection timer, turn counter, and reconnection tracking
- 🎨 **Modern UI/UX** - Dark theme with smooth animations and responsive design
- 📱 **Mobile Responsive** - Optimized layout for all screen sizes

## 🎬 Demo

<!-- Add your demo GIF or screenshot here -->
<div align="center">

![Demo Screenshot](https://via.placeholder.com/800x400?text=Add+Your+Demo+Screenshot+Here)

*Real-time voice conversation with Gemini AI*

<!-- You can also add a video demo -->
<!-- [![Demo Video](https://img.youtube.com/vi/YOUR_VIDEO_ID/0.jpg)](https://www.youtube.com/watch?v=YOUR_VIDEO_ID) -->

</div>

## 🚀 Quick Start

### Prerequisites

- **For Docker (Option 1)**: Docker and Docker Compose
- **For Local (Option 2)**: Python 3.11+ and [UV](https://github.com/astral-sh/uv)
- A [Google AI Studio](https://aistudio.google.com/) API key with Gemini access

### Option 1: Docker (Recommended - No Python Installation Required)

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/gemini-live-workshop.git
   cd gemini-live-workshop
   ```

2. **Configure your API key**
   ```bash
   cp .env.example .env
   # Edit .env and add your GEMINI_API_KEY
   ```

3. **Run with Docker Compose**
   ```bash
   docker-compose up
   ```

That's it! Open [http://localhost:8000](http://localhost:8000) in your browser.

### Option 2: Local Development with UV (Fast & Modern)

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/gemini-live-workshop.git
   cd gemini-live-workshop
   ```

2. **Install UV** (if not already installed)
   ```bash
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

3. **Install dependencies** (10-100x faster than pip!)
   ```bash
   uv sync
   ```

4. **Configure your API key**
   ```bash
   cp .env.example .env
   # Edit .env and add your GEMINI_API_KEY
   ```

5. **Run the application**
   ```bash
   uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

Then open [http://localhost:8000](http://localhost:8000) in your browser and allow microphone access when prompted.

> **Note**: This project uses UV for dependency management. UV is significantly faster than pip and manages dependencies via `pyproject.toml`.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Browser Client                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  Microphone │  │   Speaker   │  │   Transcription UI      │  │
│  │  (PCM 16kHz)│  │  (PCM 24kHz)│  │  (Input/Output Text)    │  │
│  └──────┬──────┘  └──────▲──────┘  └────────────▲────────────┘  │
│         │                │                      │                │
│         └────────────────┴──────────────────────┘                │
│                          │                                       │
│                   WebSocket Connection                           │
└──────────────────────────┼───────────────────────────────────────┘
                           │
┌──────────────────────────┼───────────────────────────────────────┐
│              FastAPI Server (Python)                             │
│                          │                                       │
│  ┌───────────────────────▼───────────────────────────────────┐   │
│  │              WebSocket Router (/ws)                        │   │
│  │  - Receives PCM audio from browser                         │   │
│  │  - Sends audio responses and transcriptions                │   │
│  └───────────────────────┬───────────────────────────────────┘   │
│                          │                                       │
│  ┌───────────────────────▼───────────────────────────────────┐   │
│  │              GeminiLiveService                             │   │
│  │  - Manages Gemini Live API connection                      │   │
│  │  - Handles audio streaming and responses                   │   │
│  └───────────────────────┬───────────────────────────────────┘   │
└──────────────────────────┼───────────────────────────────────────┘
                           │
                    WebSocket (wss://)
                           │
┌──────────────────────────▼───────────────────────────────────────┐
│                   Google Gemini Live API                         │
│              (gemini-2.0-flash-exp model)                        │
└──────────────────────────────────────────────────────────────────┘
```

For detailed architecture documentation, see [ARCHITECTURE.md](ARCHITECTURE.md).

For transcription limitations and streaming modes, see [TRANSCRIPTION_LIMITS.md](TRANSCRIPTION_LIMITS.md).

## 💡 Example Use Cases

This workshop demonstrates the Gemini Live API capabilities. Here are some practical applications:

### 1. Voice Assistant for Accessibility
Build voice-controlled interfaces for users with mobility limitations or visual impairments.

```python
# Example: Voice-controlled navigation
"Navigate to settings" → Gemini processes → App responds with audio + action
```

### 2. Real-time Language Translation
Create a live interpreter for multilingual conversations.

```python
# Example: English → Spanish real-time translation
User speaks: "How are you?" → Gemini translates → "¿Cómo estás?"
```

### 3. Voice-based Transcription Service
Transcribe meetings, interviews, or lectures in real-time with AI-powered accuracy.

```python
# Example: Meeting transcription
Audio input → Gemini Live API → Real-time text transcription
```

### 4. Interactive Voice Learning Platform
Educational applications with conversational AI tutoring.

```python
# Example: Language learning practice
Student: "How do I say 'hello' in French?"
Gemini: "You say 'Bonjour' [plays pronunciation audio]"
```

## 📁 Project Structure

```
├── main.py                       # FastAPI application entry point
├── app/
│   ├── config.py                 # Pydantic settings & configuration
│   ├── exceptions.py             # Custom exception classes
│   ├── routers/
│   │   └── websocket.py          # WebSocket endpoint handler
│   └── services/
│       └── gemini_live.py        # Gemini Live API service
├── static/
│   └── index.html                # Complete web client (HTML+CSS+JS)
│       ├── UI Components         # Video call layout, chat, settings modal
│       ├── VAD Integration       # Silero VAD v5 implementation
│       ├── Audio System          # WebSocket audio streaming & playback
│       ├── Visualizers           # Real-time audio frequency bars
│       └── State Management      # Connection, transcription, UI state
├── tests/                        # Comprehensive test suite (80%+ coverage)
│   ├── conftest.py               # Pytest fixtures
│   ├── test_main.py              # Application tests
│   ├── test_health.py            # Health endpoint tests
│   └── services/
│       └── test_gemini_live.py   # Service tests
├── pyproject.toml                # Modern Python packaging (PEP 517/518)
├── .pre-commit-config.yaml       # Pre-commit hooks (Ruff + Mypy)
├── Dockerfile                    # Multi-stage Docker build
├── docker-compose.yml            # Local development setup
├── .env.example                  # Environment variables template
├── ARCHITECTURE.md               # Detailed architecture docs
├── CONTRIBUTING.md               # Contribution guidelines
├── SECURITY.md                   # Security policy
└── CHANGELOG.md                  # Version history
```

## 🧪 Development

This project follows modern Python best practices with comprehensive testing, type safety, and code quality tools.

### Development Workflow

1. **Install pre-commit hooks** (runs automatically on `git commit`)
   ```bash
   uv run pre-commit install
   ```

2. **Run tests** with coverage reporting
   ```bash
   uv run pytest --cov=app --cov=main --cov-report=term-missing
   ```

3. **Type checking** with Mypy
   ```bash
   uv run mypy app/ main.py
   ```

4. **Linting and formatting** with Ruff
   ```bash
   # Check for issues
   uv run ruff check .

   # Auto-fix issues
   uv run ruff check --fix .

   # Format code
   uv run ruff format .
   ```

5. **Run all quality checks** (linting + type checking + tests)
   ```bash
   uv run pre-commit run --all-files
   uv run pytest
   ```

### Code Quality Standards

- **Test Coverage**: 80%+ (enforced in CI)
- **Type Hints**: 90%+ coverage with Mypy
- **Code Style**: Ruff (replaces black + isort + flake8)
- **Python Versions**: 3.11, 3.12, 3.13 (tested in CI)

### Development Tools

| Tool | Purpose | Config |
|------|---------|--------|
| **UV** | Fast dependency management (10-100x faster than pip) | `pyproject.toml` |
| **Pytest** | Testing framework with async support | `pyproject.toml` |
| **Ruff** | Linting and formatting (60-80% faster CI) | `pyproject.toml` |
| **Mypy** | Static type checking | `pyproject.toml` |
| **Pre-commit** | Git hooks for code quality | `.pre-commit-config.yaml` |

### Performance Metrics

- **Dependency Install**: 10-100x faster with UV vs pip
- **CI Pipeline**: ~60-80% faster with Ruff vs black+isort+flake8
- **Type Safety**: 90%+ type hint coverage
- **Test Coverage**: 80%+ coverage across all modules

## 🔧 Configuration

| Environment Variable | Description | Default | Required |
|---------------------|-------------|---------|----------|
| `GEMINI_API_KEY` | Your Google AI Studio API key | - | Yes |
| `GEMINI_MODEL` | Gemini model to use | `gemini-2.0-flash-exp` | No |
| `HOST` | Server host | `0.0.0.0` | No |
| `PORT` | Server port | `8000` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |
| `FLUSH_INTERVAL_BYTES` | Audio flush interval | `160000` | No |

## 🛠️ Tech Stack

- **Backend**: [FastAPI](https://fastapi.tiangolo.com/) + WebSockets
- **AI**: [Google Gemini Live API](https://ai.google.dev/)
- **Audio**: Web Audio API (PCM 16kHz mono)
- **Frontend**: Vanilla HTML/CSS/JavaScript

## 🗺️ Roadmap

### Completed
- ✅ Real-time bidirectional audio streaming
- ✅ WebSocket communication with Gemini Live API
- ✅ Manual Voice Activity Detection (VAD)
- ✅ Real-time transcription (input/output)
- ✅ Comprehensive test suite (80%+ coverage)
- ✅ Type safety with Mypy (90%+ coverage)
- ✅ Modern dependency management (UV + pyproject.toml)
- ✅ Docker support for easy deployment
- ✅ Pre-commit hooks for code quality
- ✅ CI/CD pipeline with GitHub Actions

### Planned Features
- 🔜 WebSocket authentication (JWT tokens)
- 🔜 Rate limiting per connection
- 🔜 Automatic VAD (Voice Activity Detection)
- 🔜 Multi-language support configuration
- 🔜 Audio recording and playback
- 🔜 Session history and analytics
- 🔜 WebSocket compression
- 🔜 Horizontal scaling support
- 🔜 Prometheus metrics export
- 🔜 OpenTelemetry tracing

### Community Requests
Have an idea? [Open an issue](https://github.com/YOUR_USERNAME/gemini-live-workshop/issues/new) or start a [discussion](https://github.com/YOUR_USERNAME/gemini-live-workshop/discussions)!

## 🤝 Contributing

Contributions are welcome! We follow modern Python best practices and maintain high code quality standards.

### Quick Start for Contributors

1. **Fork and clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/gemini-live-workshop.git
   cd gemini-live-workshop
   ```

2. **Install dependencies with UV**
   ```bash
   uv sync
   ```

3. **Install pre-commit hooks**
   ```bash
   uv run pre-commit install
   ```

4. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```

5. **Make your changes** and ensure quality checks pass
   ```bash
   uv run ruff check --fix .
   uv run mypy app/ main.py
   uv run pytest --cov
   ```

6. **Commit using conventional commits**
   ```bash
   git commit -m "feat: add amazing feature"
   # or: fix:, docs:, test:, refactor:, chore:
   ```

7. **Push and create a Pull Request**
   ```bash
   git push origin feature/amazing-feature
   ```

### Contribution Guidelines

- **Tests required**: All new features must include tests (70%+ coverage)
- **Type hints required**: All functions must have type annotations
- **Code style**: Ruff enforced (runs automatically via pre-commit)
- **Documentation**: Update README and docstrings as needed
- **Conventional commits**: Use semantic commit messages

For detailed guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md).

### Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold this code.

## 🔒 Security

Security is a top priority. This project includes:

- **Security scanning** with Bandit in CI/CD
- **Dependency updates** tracked via Dependabot (recommended)
- **Pre-commit security checks** for common vulnerabilities
- **Comprehensive security policy** in [SECURITY.md](SECURITY.md)

### Reporting Vulnerabilities

Please **do not** open public issues for security vulnerabilities. Instead:

- **Email**: isaias.caporusso@gmail.com
- **Response time**: Within 48 hours
- See [SECURITY.md](SECURITY.md) for full details

## 🌟 Community

### Getting Help

- 📖 [Documentation](ARCHITECTURE.md) - Detailed architecture and design docs
- 💬 [Discussions](https://github.com/YOUR_USERNAME/gemini-live-workshop/discussions) - Ask questions and share ideas
- 🐛 [Issues](https://github.com/YOUR_USERNAME/gemini-live-workshop/issues) - Report bugs or request features

### Stay Updated

- ⭐ Star this repository to show support
- 👀 Watch for updates and new releases
- 🔄 Follow the [CHANGELOG.md](CHANGELOG.md) for version updates

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Google AI](https://ai.google.dev/) for the Gemini Live API
- [FastAPI](https://fastapi.tiangolo.com/) for the amazing Python web framework
- [Astral](https://astral.sh/) for UV and Ruff - blazingly fast Python tooling
- The open source community for inspiration and support

## 📊 Project Stats

<div align="center">

| Metric | Value |
|--------|-------|
| **Lines of Code** | ~1,500 |
| **Test Coverage** | 80%+ |
| **Type Hint Coverage** | 90%+ |
| **Python Versions** | 3.11, 3.12, 3.13 |
| **Dependencies** | 6 core + 7 dev |
| **CI/CD Time** | ~1-2 minutes |
| **Docker Image Size** | ~200MB (multi-stage) |
| **Code Quality** | A+ (Ruff + Mypy) |

</div>

---

<div align="center">

**[⬆ Back to top](#-gemini-live-api---real-time-voice-chat)**

Made with ❤️ ☕ 🤖 by the community

*Powered by Google Gemini 2.5 • Built with FastAPI • Tooling by Astral*

</div>
