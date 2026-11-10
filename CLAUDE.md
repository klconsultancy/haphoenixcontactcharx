## Agent skills

### Issue tracker

Issues live in GitHub Issues at `klconsultancy/haphoenixcontactcharx`. See `docs/agents/issue-tracker.md`.

### Triage labels

Default label vocabulary: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context repo: one `CONTEXT.md` at the repo root. `docs/adr/` does not exist yet — it will be created when the first ADR is needed. See `docs/agents/domain.md`.

## Pull requests and releases

PRs are squash-merged and the PR title becomes the commit on `main`, so the title must be a Conventional Commit (`fix:`, `feat:`, `feat!:` for a change that breaks entities or configuration, `docs:`, `ci:`, `build:`, `chore:`). release-please builds the next version and `CHANGELOG.md` from those titles, keeps a release PR open and raises `version` in `manifest.json`; merging that PR tags the release and creates the GitHub release HACS installs. Don't bump `manifest.json`'s version by hand. Renovate handles dependency updates; there is no Dependabot.

A release candidate is a tag `vX.Y.Z-rc.N` on `main`, pushed by an admin: `release.yaml` makes it a GitHub pre-release, which HACS offers to users who enabled beta versions. Never make one with `release-as` and `prerelease` in `release-please-config.json`: release-please then counts the rc as the previous release, and the final release's notes, which HACS shows at the update, leave out everything the rc had (it happened with 2.0.0). Before merging a release PR, check that its notes tell a user of the last stable release everything they need, breaking changes first.
