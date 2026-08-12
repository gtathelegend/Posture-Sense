# Contributing to PostureSense v2

Thank you for your interest in contributing to **PostureSense v2**! We welcome contributions from open-source developers, physical therapists, computer vision researchers, and UX designers.

---

## Code of Conduct

By participating in this project, you agree to maintain a respectful, inclusive, and professional environment for all contributors.

---

## Development Setup

1. **Fork & Clone the Repository**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/Posture-Sense.git
   cd Posture-Sense
   ```

2. **Create a Virtual Environment**:
   ```bash
   python -m venv venv
   # Activate environment:
   source venv/bin/activate  # Linux/macOS
   .\venv\Scripts\Activate.ps1 # Windows
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Copy Environment Template**:
   ```bash
   cp .env.example .env
   ```

5. **Run Local Server**:
   ```bash
   python app.py
   ```

---

## Branch Naming Conventions

Use descriptive branch names prefixed with the change category:

- `feature/` : New features or engine improvements (e.g., `feature/squat-depth-rom`)
- `fix/`     : Bug fixes or stability patches (e.g., `fix/ema-landmark-smoothing`)
- `docs/`    : Documentation additions or fixes (e.g., `docs/update-architecture`)
- `refactor/`: Code readability or structural enhancements (e.g., `refactor/flask-blueprints`)

---

## Commit Message Conventions

PostureSense v2 follows **Conventional Commits**:

```
<type>(<scope>): <short description>
```

### Types

- `feat`    : A new feature or engine capability.
- `fix`     : A bug fix.
- `docs`    : Documentation only changes.
- `style`   : Code style / formatting changes (no logic impact).
- `refactor`: Code change that neither fixes a bug nor adds a feature.
- `test`    : Adding or correcting tests.
- `chore`   : Repository maintenance or build configuration updates.

### Example Commit Messages

```
feat(movement): add concentric phase velocity tracking
fix(security): sanitize report filename parameters
docs(readme): add performance benchmark summary badge
```

---

## Testing Requirements

Before submitting a Pull Request, all automated tests **must pass**:

```bash
python -m pytest
```

If you add new engine features or REST endpoints, you are expected to include corresponding unit/integration test cases under `tests/`.

---

## Code Style & Standards

- **Python**: Follow PEP 8 style guidelines. Use type hints where helpful.
- **JavaScript**: Use modern ES6+ modules, `const`/`let`, arrow functions, and strict equality (`===`).
- **YAML Configs**: Format YAML files with 2-space indentation.
- **Documentation**: Use standard GitHub-Flavored Markdown.

---

## Pull Request (PR) Process

1. Ensure your branch is up-to-date with `main` or `v2`.
2. Run `python -m pytest` to verify 100% test passage.
3. Push your branch to GitHub and open a Pull Request against the `v2` branch.
4. Complete the PR template checklist.
5. Code reviews are conducted by maintainers prior to merging.
