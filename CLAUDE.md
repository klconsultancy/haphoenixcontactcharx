## Agent skills

### Issue tracker

Issues live in GitHub Issues at `klconsultancy/haphoenixcontactcharx`. See `docs/agents/issue-tracker.md`.

### Triage labels

Default label vocabulary: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context repo: one `CONTEXT.md` at the repo root. `docs/adr/` does not exist yet — it will be created when the first ADR is needed. See `docs/agents/domain.md`.

## Pull requests and releases

PRs are squash-merged and the PR title becomes the commit on `main`, so the title must be a Conventional Commit (`fix:`, `feat:`, `feat!:` for a change that breaks entities or configuration, `docs:`, `ci:`, `build:`, `chore:`). release-please builds the next version and `CHANGELOG.md` from those titles, keeps a release PR open and raises `version` in `manifest.json`; merging that PR tags the release and creates the GitHub release HACS installs. Don't bump `manifest.json`'s version by hand. Renovate handles dependency updates; there is no Dependabot.
