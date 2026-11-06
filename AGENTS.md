# Working agreement

## Remote

All work in this folder belongs to
[`pallavisingh15112005-gif/cropora_AI_`](https://github.com/pallavisingh15112005-gif/cropora_AI_).
`origin` is configured and `main` tracks `origin/main`.

## Commit and push

- Commit every meaningful change.
- Push to `origin main` after committing; never leave work only local.
- Use Conventional Commit subjects, e.g. `feat: add document chat`,
  `fix: handle empty upload`, `docs: update setup steps`.
- Keep commits focused; do not bundle unrelated changes.

```bash
git add -A
git commit -m "feat: <what changed>"
git push
```

## Secrets

Never commit API keys, tokens, or `.streamlit/secrets.toml`. Use
`.streamlit/secrets.toml.example` for documentation and `.env.example` for
local environment variables.
