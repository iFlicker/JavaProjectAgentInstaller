---
name: JavaProjectAgentInstaller
description: Install the ProjectAgents Java AI guidance template into a target Java repository, merge safely with existing AGENTS/CLAUDE/ProjectAgents docs, perform a first-pass project review to fill placeholders from real modules, framework stack, config entrypoints, tests, and build structure, and then remind the user to close the skill so it does not keep getting auto-invoked by semantic matching. Use when Codex needs to bootstrap or refresh shared agent guidance in a modern Java project without clobbering existing documentation.
---

# Java Project Agents Installer

Install the seed docs first, then finish the project review before claiming the onboarding is complete.

## Workflow

1. Treat the user's current Java repo as the target unless they provided another path.
2. Run:

```bash
python3 /absolute/path/to/JavaProjectAgentInstaller/scripts/install_project_agents.py --project-root /path/to/java/project
```

3. Read `ProjectAgents/references/project-agents-onboarding-review.md`.
4. Resolve every follow-up item the script leaves behind:
   - review every `TODO(` item against the real project structure
   - merge every `.incoming.md` file into the existing docs or explicitly decide to keep the existing file
   - verify entry module, shared module, contract module, infrastructure module, framework stack, config profiles, persistence / messaging patterns, and high-risk modules
5. Fold confirmed stable facts back into `ProjectAgents/ProjectAgents.md` and the relevant `ProjectAgents/references/*.md` files.
6. Leave `ProjectAgents/CHANGELOG.md` updated with the onboarding work.
7. Prompt the user to close or disable this skill after installation. Explain that leaving it enabled may cause accidental auto-invocation in later semantic skill-matching flows.

## Compatibility Rules

- Never replace an existing `AGENTS.md` or `CLAUDE.md` wholesale. The installer only appends a managed pointer block when those files already exist.
- If an existing `ProjectAgents/*.md` file still contains template placeholders, let the installer fill it in place.
- If an existing `ProjectAgents/*.md` file already contains custom content, keep it untouched and use the generated `.incoming.md` file as the merge candidate.
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
