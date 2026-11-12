# Working agreement

## Remote

All work in this folder belongs to
[`pallavisingh15112005-gif/cropora_AI_`](https://github.com/pallavisingh15112005-gif/cropora_AI_).
`origin` is configured and `main` tracks `origin/main`.

## Commit and push

- Commit every meaningful change.
- Push to `origin main` after committing; never leave work only local.
- Use Conventional Commit subjects, e.g. `feat: add paper trading`,
  `fix: handle empty positions`, `docs: update setup steps`.
- Keep commits focused; do not bundle unrelated changes.

```bash
git add -A
git commit -m "feat: <what changed>"
git push
```

## Secrets and data

- Never commit API keys, tokens, or `.streamlit/secrets.toml`.
- The paper-trading database (`data/*.db`) is local and gitignored.
- Prices are simulated; do not present them as real market data.
