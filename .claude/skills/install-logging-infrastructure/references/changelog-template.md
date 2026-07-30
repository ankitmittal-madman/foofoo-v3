# Change Log — Reference Template

A single master `CHANGELOG.md` at the project root. Every coding session
that produces code adds an entry — this is enforced by the always-on
coding-standard skill (see `claude-coding-standards` skill), not by this
installer.

## File structure

```markdown
# [Project Name] — Master Change Log
*Every code change goes here. Format is at the bottom of this file.*

---

## [Unreleased]
<!-- Add new changes here. Move to a version block when a milestone completes. -->

---

## [vX.Y.Z] — [Milestone/Sprint name] — YYYY-MM-DD

### Added
- Description of new file or feature, with file paths

### Changed
- Description of what changed in existing code, and why

### Fixed
- Description of bug fixed

### Packages (if dependencies changed)
| Package | Version | Purpose |
|---|---|---|

---

## Change Log Entry Format

When adding an entry, use this template:

\`\`\`markdown
## [vX.Y.Z] — [Milestone Name] — YYYY-MM-DD

### Added
- ...

### Changed
- ...

### Fixed
- ...
\`\`\`

---
*This file lives at the project root. Every Claude Code session that
produces code must add an entry here.*
```

## Notes for the installer

- If `CHANGELOG.md` already exists with a different format, do not
  overwrite it — ask the user whether to adopt this structure going
  forward or keep theirs
- Seed the `[Unreleased]` section, leave version blocks for the user/future
  sessions to fill in as milestones complete
- This file should never be deleted entries from — append-only, same
  principle as `KNOWLEDGE.html`'s injection points
