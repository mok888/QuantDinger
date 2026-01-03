# Contributing

Thanks for your interest in contributing to **QuantDinger**! This guide explains how to report issues, propose changes, and submit pull requests.

> 🌟 **Want to join our DAO community?** Check out [CONTRIBUTORS.md](CONTRIBUTORS.md) to learn about early contributor rewards, including QDT governance token airdrops!

---

## 1) Quick links

- **Issues**: use GitHub Issues for bugs and feature requests.
- **Discussions**: use GitHub Discussions for Q&A and ideas.
- **Community**: official channels are linked in `README.md` (Telegram/Discord).

---

## 2) Ways to contribute

- **Report bugs**: provide steps to reproduce plus logs/screenshots.
- **Request features**: describe the use case, expected behavior, and alternatives.
- **Improve docs**: fix typos, clarify setup, add examples.
- **Submit code**: bug fixes, refactors, and new features.

---

## 3) Before you start

- Please read and follow [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).
- Keep changes focused and small when possible (easier review and safer merges).
- If you plan a large change, open a discussion/issue first to align on design.

---

## 4) Development setup

This repo contains:

- `backend_api_python/`: Flask backend + strategy runtime
- `quantdinger_vue/`: Vue 2 frontend

### Backend (Python)

```bash
cd backend_api_python
pip install -r requirements.txt
cp env.example .env   # Windows: copy env.example .env
python run.py
```

### Frontend (Vue)

```bash
cd quantdinger_vue
npm install
npm run serve
```

---

## 5) Branching & PR workflow

### Branch naming

Use a clear prefix:

- `fix/xxx` for bug fixes
- `feat/xxx` for new features
- `docs/xxx` for documentation
- `chore/xxx` for maintenance tasks

### Pull requests

1. Fork the repo and create a new branch from `main`.
2. Make your changes with clear, focused commits.
3. Open a PR with:
   - What changed and why
   - Screenshots/GIFs for UI changes
   - How to test (commands, steps)
   - Backward compatibility notes (if any)

---

## 6) Commit messages

Recommended format (similar to Conventional Commits):

- `feat: ...`
- `fix: ...`
- `docs: ...`
- `refactor: ...`
- `chore: ...`

---

## 7) Coding guidelines

### General

- Prefer clarity over cleverness.
- Keep functions small and cohesive.
- Add comments only where necessary (the code should be the primary documentation).

### Python

- Prefer explicit error handling and helpful error messages.
- Avoid storing secrets in code or committed files; use `.env`.

### Frontend

- Keep UI changes consistent with existing Ant Design Vue patterns.
- Avoid breaking i18n keys; reuse existing language keys where possible.

---

## 8) Tests & verification

We don’t enforce a single test command across the whole monorepo yet. Please at least:

- Backend: run the API locally and verify affected endpoints
- Frontend: run the dev server and verify affected pages/components

If you add a bug fix, please add a minimal regression test when practical.

---

## 9) Security

Please **do not** open public issues for security vulnerabilities.

For security reports, contact the maintainers via the email in `README.md` and include:

- A description of the issue
- Steps to reproduce / proof of concept
- Impact assessment (what could an attacker do?)

---

## 10) License

By contributing, you agree that your contributions will be licensed under this project’s license (see `LICENSE`).
