---
name: JavaProjectAgentInstaller
description: Ask the user for installation preferences first, wait for explicit confirmation, then install the ProjectAgents Java AI guidance template into a target Java repository, merge safely with existing AGENTS/CLAUDE/ProjectAgents docs, perform a first-pass project review to fill placeholders from real modules, framework stack, config entrypoints, tests, and build structure, and then remind the user to close the skill so it does not keep getting auto-invoked by semantic matching. Use when Codex needs to bootstrap or refresh shared agent guidance in a modern Java project without clobbering existing documentation.
---

# Java Project Agents Installer

Ask for preferences first, wait for explicit confirmation, then install the seed docs and finish the project review before claiming the onboarding is complete.

## Workflow

1. Treat the user's current Java repo as the target unless they provided another path.
2. Ask the user what preferences they have before installation. At minimum, confirm whether they want any non-default target path, merge behavior expectations for existing docs, and any review scope preferences.
3. Wait for explicit user confirmation before running the installer. If the user has no special preferences, ask them to confirm that the default installation behavior is acceptable.
4. Run:

```bash
python3 /absolute/path/to/JavaProjectAgentInstaller/scripts/install_project_agents.py --project-root /path/to/java/project
```

5. Read `ProjectAgents/references/project-agents-onboarding-review.md`.
6. Resolve every follow-up item the script leaves behind:
   - review every `TODO(` item against the real project structure
   - merge every `.incoming.md` file into the existing docs or explicitly decide to keep the existing file
   - verify entry module, shared module, contract module, infrastructure module, framework stack, config profiles, persistence / messaging patterns, and high-risk modules
7. Fold confirmed stable facts back into `ProjectAgents/ProjectAgents.md` and the relevant `ProjectAgents/references/*.md` files.
8. Leave `ProjectAgents/CHANGELOG.md` updated with the onboarding work.
9. Prompt the user to close or disable this skill after installation. Explain that leaving it enabled may cause accidental auto-invocation in later semantic skill-matching flows.

## Compatibility Rules

- Never replace an existing `AGENTS.md` or `CLAUDE.md` wholesale. The installer only appends a managed pointer block when those files already exist.
- If an existing `ProjectAgents/*.md` file still contains template placeholders, let the installer fill it in place.
- If an existing `ProjectAgents/*.md` file already contains custom content, keep it untouched and use the generated `.incoming.md` file as the merge candidate.
- Never run the installer before the user has stated their preferences and explicitly confirmed the installation step.
- Do not delete user-authored docs unless the user explicitly asks for cleanup.

## Review Focus

Confirm these areas manually when the script confidence is not high enough:

- main runnable module, API/web entry module, common/shared module, infrastructure/data module
- Gradle vs Maven build shape, parent BOM, version catalogs, build logic, annotation processors
- service contracts, REST/RPC entrypoints, persistence, cache, messaging, scheduled jobs
- history-heavy modules, generated-code boundaries, starter/BOM modules, externalized integrations
- module-local `AGENTS.md` / `CLAUDE.md` files that should be referenced in the shared guidance
- common package namespaces, config files, test directories, utility/base classes, and deployment context files

## Resources

- `assets/template/`: the seed ProjectAgents docs copied into target repos
- `scripts/install_project_agents.py`: installer, compatibility handler, and first-pass review generator
