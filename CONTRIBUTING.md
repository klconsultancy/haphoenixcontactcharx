# Contributing

Thanks for your interest. This is the Home Assistant integration for Phoenix Contact CHARX SEC controllers. The Modbus/TCP client lives in [aiophoenixcontactcharx](https://github.com/klconsultancy/aiophoenixcontactcharx): changes to how registers are read or written belong there.

## Before you write code

Open an issue first for anything beyond a small fix, so we can agree on the approach before you spend time on it. Read [CONTEXT.md](CONTEXT.md) for the domain terms. Report security issues privately as described in [SECURITY.md](SECURITY.md).

## Development

You need the Python version Home Assistant requires (3.14).

```sh
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-test.txt
pytest
```

To try the integration in a real Home Assistant, `docker compose up` starts one with `custom_components/` mounted, at http://localhost:8123.

## Pull requests

- Keep a pull request to one change, with tests.
- CI (tests, hassfest, the HACS action, dependency review and CodeQL) must pass before merging.
- Pull requests are squash-merged, so the pull request title becomes the commit message on `main`. Write it as a [Conventional Commit](https://www.conventionalcommits.org/) with a short imperative description, such as `fix: keep total energy unknown until the meter is read`: release-please derives the next version and the changelog from these titles. Use `feat!:` or a `BREAKING CHANGE:` footer for a change that breaks existing entities or configuration.

By contributing you agree that your contribution is licensed under the [MIT license](LICENSE), and you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).
