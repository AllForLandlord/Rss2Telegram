# Repository Guidelines

## Project Structure & Module Organization

- `rss2telegram.py` contains the complete RSS parsing, filtering, Telegram delivery, Telegraph integration, and SQLite history logic.
- `requirements.txt` pins the Python dependencies used by the script.
- `.github/workflows/cron.yml` installs Python 3.8, restores the database artifact, and runs the bot hourly. `keepalive.yml` maintains scheduled workflow activity.
- `rss2telegram.db` stores sent-link history. Runtime configuration may also be supplied through root-level `URL.txt`, `DESTINATION.txt`, and `RULES.txt` files; do not commit secrets.

## Build, Test, and Development Commands

There is no build system or automated test suite. Create a Python 3.8+ virtual environment, install dependencies, and run:

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python rss2telegram.py
```

The script requires `BOT_TOKEN`, `DESTINATION`, and `URL` (plus any optional variables documented in `README.md`). Use local `.txt` files for values that are not present in the environment. Test changes against a disposable database and Telegram destination.

## Coding Style & Naming Conventions

Use Python with 4-space indentation, `snake_case` for functions and local variables, and uppercase names for configuration constants. Keep functions focused and preserve the existing straightforward procedural style. Follow PEP 8 where practical; no formatter or linter is currently configured, so review changed code manually before submitting.

## Testing Guidelines

No tests or coverage threshold currently exist. For changes, at minimum run `python rss2telegram.py` with safe test credentials/data, exercise RSS parsing and `RULES.txt` filtering, and verify that history is written without duplicate sends. Add focused tests if introducing reusable logic.

## Commit & Pull Request Guidelines

History uses short imperative subjects, including conventional prefixes such as `chore:` alongside concise `Add`, `Update`, and `Remove` messages. Keep commits focused and explain the user-visible effect. Pull requests should describe configuration or workflow changes, list validation performed, link related issues, and call out any new secrets, variables, or migration concerns.

## Security & Configuration Tips

Never commit `BOT_TOKEN`, Telegraph tokens, feed credentials, or personal destinations. Treat workflow variables and GitHub secrets as production configuration. Be cautious when changing Telegram message formatting, URL handling, database writes, or artifact restoration because these affect duplicate prevention and live delivery.
