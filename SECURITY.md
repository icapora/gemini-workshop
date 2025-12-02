# Security Policy

## Supported Versions

We release security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please follow these steps:

### 1. Do Not Open a Public Issue

Please do **not** create a public GitHub issue for security vulnerabilities.

### 2. Report Privately

**Email:** isaias.caporusso@gmail.com (or create a private security advisory on GitHub)

Include:
- A description of the vulnerability
- Steps to reproduce the issue
- Potential impact assessment
- Any suggested fixes (optional but appreciated)
- Your contact information for follow-up

### 3. Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Depends on severity
  - **Critical**: 7 days
  - **High**: 30 days
  - **Medium**: 60 days
  - **Low**: 90 days

### 4. Disclosure Policy

- We will acknowledge your report within 48 hours
- We will provide regular updates on our progress
- Once the vulnerability is fixed, we will:
  - Release a security advisory
  - Credit you in the advisory (if desired)
  - Coordinate the public disclosure timing with you

## Security Best Practices

### API Key Management

**NEVER** commit API keys to the repository:

```bash
# ❌ WRONG - Don't do this
export GEMINI_API_KEY="actual-key-here"
git add .env
git commit -m "Added API key"

# ✅ CORRECT - Use .env file (gitignored)
cp .env.example .env
echo "GEMINI_API_KEY=your-key-here" >> .env
# .env is already in .gitignore
```

### Environment Variables

Always use environment variables for sensitive data:

```python
# ✅ GOOD - Using Pydantic settings
from app.config import settings
api_key = settings.gemini_api_key

# ❌ BAD - Hardcoded secrets
api_key = "hardcoded-key-12345"
```

### Dependencies

We regularly update dependencies to patch security vulnerabilities:

```bash
# Check for vulnerabilities
uv run bandit -r app/ main.py

# Update dependencies
uv sync --upgrade

# Check for outdated packages
uv pip list --outdated
```

## Known Security Considerations

### WebSocket Connections

**Current State:** WebSocket connections do not include authentication by default.

**For Production Use, Implement:**
- JWT token authentication
- Rate limiting per IP/connection
- Origin validation (CORS)
- Connection limits per IP
- Request size limits
- Timeout policies

**Example Implementation:**

```python
# Add to websocket.py
from fastapi import Header, HTTPException

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Header(None)
):
    # Validate JWT token
    if not validate_token(token):
        await websocket.close(code=1008)
        return

    # Continue with connection...
```

### Audio Data

**Considerations:**
- Audio data is transmitted in real-time
- No encryption by default (use WSS in production)
- No data retention by default

**For Production:**
- Use WSS (WebSocket Secure) over TLS
- Implement end-to-end encryption for sensitive conversations
- Define audio data retention policies
- GDPR compliance if handling EU user data
- Implement data deletion mechanisms
- Log access to sensitive data

### API Key Exposure

**Risk:** The Gemini API key has full access to your Google AI account

**Recommendations:**
- Use separate API keys for development/production
- Implement API key rotation policies (rotate every 90 days)
- Monitor API usage for anomalies
- Set usage quotas in Google Cloud Console
- Use least-privilege principle (create keys with minimal permissions)
- Store keys in secure secret management (AWS Secrets Manager, HashiCorp Vault)

**For Production:**

```bash
# Use environment-specific keys
GEMINI_API_KEY_DEV=dev_key_here
GEMINI_API_KEY_PROD=prod_key_here

# Monitor usage
gcloud logging read "resource.type=api AND protoPayload.methodName=genai.generate"
```

### Input Validation

**Current State:** Limited input validation

**Recommendations:**
- Validate all WebSocket message types
- Limit audio chunk sizes (prevent DoS)
- Sanitize user text inputs
- Implement rate limiting on messages

**Example:**

```python
# Add validation
MAX_AUDIO_CHUNK_SIZE = 1024 * 100  # 100KB

if len(audio_data) > MAX_AUDIO_CHUNK_SIZE:
    raise ValueError("Audio chunk too large")
```

## Security Tools

We use the following tools for security:

| Tool | Purpose | Status |
|------|---------|--------|
| **Bandit** | Static security analysis for Python | ✅ Active |
| **Ruff** | Code quality and security linting | ✅ Active |
| **Dependabot** | Automated dependency updates | ⏭️ Recommended |
| **Pre-commit** | Git hooks for security checks | ✅ Active |
| **GitHub Security Advisories** | Vulnerability tracking | ⏭️ Recommended |

### Running Security Scans Locally

```bash
# Security linting with Bandit
uv run bandit -r app/ main.py -f json

# Check for known vulnerabilities (if safety is installed)
uv pip install safety
uv run safety check

# Run all pre-commit hooks (includes security checks)
uv run pre-commit run --all-files
```

## Security Updates

Security updates are released as:
- **Patch versions** (e.g., 1.0.1) for minor issues
- **Minor versions** (e.g., 1.1.0) for moderate issues
- **Immediate releases** for critical vulnerabilities

**Notification Channels:**
- GitHub Security Advisories
- CHANGELOG.md
- Release notes
- Email (for critical issues)

## Secure Development Guidelines

### Code Review Checklist

Before merging code, ensure:
- [ ] No hardcoded secrets or API keys
- [ ] Input validation on all user inputs
- [ ] Proper error handling (no information leakage)
- [ ] Authentication/authorization checks
- [ ] SQL injection prevention (if using databases)
- [ ] XSS prevention in output
- [ ] CSRF protection for state-changing operations
- [ ] Rate limiting on sensitive endpoints
- [ ] Logging doesn't expose sensitive data

### Production Deployment Checklist

- [ ] Use HTTPS/WSS (TLS encryption)
- [ ] Enable rate limiting
- [ ] Implement authentication
- [ ] Set up monitoring and alerting
- [ ] Regular security audits
- [ ] Backup and disaster recovery plan
- [ ] Incident response plan
- [ ] Security headers configured
- [ ] CORS properly configured
- [ ] Secrets stored in secure vault

## Contact

For security-related questions or concerns:

- **Email:** isaias.caporusso@gmail.com
- **Security Advisories:** [GitHub Security Tab](https://github.com/icapora/gemini-workshop/security)
- **General Issues:** [GitHub Issues](https://github.com/icapora/gemini-workshop/issues)

## Acknowledgments

We appreciate security researchers who help keep our project safe. Contributors will be acknowledged in:
- Security advisories
- CHANGELOG.md
- Project README (Hall of Fame section)

### Responsible Disclosure

We follow responsible disclosure practices:
1. Report received and acknowledged
2. Issue confirmed and assessed
3. Fix developed and tested
4. Fix released
5. Public disclosure (coordinated with reporter)
6. Credit given to reporter

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)

---

**Thank you for helping keep Gemini Workshop secure!** 🔒
