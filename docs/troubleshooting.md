# Troubleshooting & Known Issues

A reference guide documenting every issue encountered during the initial setup of this Claude agent workflow project. Use this to prepare for and quickly resolve common problems when building similar autonomous pipeline systems.

---

## Table of Contents

1. [Python Import Errors (src layout)](#1-python-import-errors-src-layout)
2. [allowed_tools Is Not a Valid Action Input](#2-allowed_tools-is-not-a-valid-action-input)
3. [--allowedTools in claude_args Has No Effect](#3---allowedtools-in-claude_args-has-no-effect)
4. [Agent Hits max_turns Before Finishing](#4-agent-hits-max_turns-before-finishing)
5. [Agent Completes But No PR Created (Branch 404)](#5-agent-completes-but-no-pr-created-branch-404)
6. [Permission Denied: uv sync](#6-permission-denied-uv-sync)
7. [Permission Denied: git commit (HEREDOC Format)](#7-permission-denied-git-commit-heredoc-format)
8. [GitHub Label Not Found](#8-github-label-not-found)
9. [Docker init.sql Not Re-running After Schema Changes](#9-docker-initsql-not-re-running-after-schema-changes)
10. [Retry Comments Inflate Turn Count](#10-retry-comments-inflate-turn-count)
11. [Multiline Commit Messages Always Denied](#11-multiline-commit-messages-always-denied)

---

## 1. Python Import Errors (src layout)

**When**: Running `uv run python -m pipeline.flows.earthquake_flow` for the first time.

**Error**:
```
ModuleNotFoundError: No module named 'pipeline'
```

**Root cause**: The project uses a `src/` layout (`src/pipeline/`), but the `pyproject.toml` was missing the build system configuration that tells Python where to find the package.

**Fix**: Add a `[build-system]` section with hatchling and explicitly declare the package path:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/pipeline"]
```

Also add `pythonpath = ["src"]` to pytest config so tests can import the package:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

Then run `uv sync --all-extras` to reinstall.

**Lesson**: When using `uv` with a `src/` layout, you need hatchling as the build backend with an explicit packages path. This is a common gotcha that doesn't occur with flat layouts.

---

## 2. allowed_tools Is Not a Valid Action Input

**When**: First attempt at configuring Claude agent tool permissions.

**Error** (in GitHub Actions log):
```
Warning: Unexpected input(s) 'allowed_tools', valid inputs are ['anthropic_api_key', 'claude_args', 'settings', ...]
```

**What we tried**:
```yaml
- uses: anthropics/claude-code-action@v1
  with:
    allowed_tools: "Bash(uv run *)"  # WRONG — not a valid input
```

**Root cause**: `allowed_tools` is not a recognized input parameter for `claude-code-action@v1`. The action silently warns and ignores it, running with only the default tools.

**Fix**: Use the `settings` input with a JSON permissions object instead. See [issue #7](#7-permission-denied-git-commit-heredoc-format) for the final working configuration.

**Lesson**: Always check the action's actual input parameters in its `action.yml` or documentation. The `settings` input with a JSON `permissions.allow` array is the correct approach.

---

## 3. --allowedTools in claude_args Has No Effect

**When**: Second attempt at configuring tool permissions, after discovering `allowed_tools` was invalid.

**What we tried**:
```yaml
- uses: anthropics/claude-code-action@v1
  with:
    claude_args: "--max-turns 25 --allowedTools 'Bash(uv run *)'"
```

**What happened**: The action ran, but checking the `ALLOWED_TOOLS` environment variable in the logs showed only the default tools — our additions were ignored.

**Root cause**: The `--allowedTools` flag passed via `claude_args` doesn't properly integrate with the action's permission system. The action has its own mechanism for tool permissions that overrides CLI flags.

**Fix**: Use the `settings` input:

```yaml
settings: |
  {
    "permissions": {
      "allow": [
        "Bash(uv run *)"
      ]
    }
  }
```

**Lesson**: Tool permissions for `claude-code-action` must go through the `settings` input as JSON. The `claude_args` parameter is only for flags like `--max-turns`, not for permission configuration.

---

## 4. Agent Hits max_turns Before Finishing

**When**: First successful agent run on a real pipeline issue (Open-Meteo weather pipeline).

**Error** (in GitHub Actions log):
```json
{
  "type": "result",
  "subtype": "error_max_turns",
  "num_turns": 25
}
```

**What happened**: Claude wrote all the code (7 files, 369 lines, 12 tests) but ran out of turns before it could run lint, run tests, commit, and push. Since it never pushed, no PR was created.

**Root cause**: `--max-turns 25` is too few for building a complete pipeline with tests. A typical pipeline build takes 30-40 turns (read existing code, write new files, run lint, fix issues, run tests, fix issues, commit, push).

**Fix**: Increase to 50 turns:

```yaml
claude_args: "--max-turns 50"
```

**Lesson**: For multi-file pipeline tasks, budget at least 50 turns. Simple tasks (bug fixes, adding a test) may work with 25, but building a full pipeline from scratch needs more. Monitor API costs — each turn uses Claude API credits.

---

## 5. Agent Completes But No PR Created (Branch 404)

**When**: The agent shows `"subtype": "success"` in logs but no PR appears on GitHub.

**Error** (in GitHub Actions log):
```
Branch claude/issue-5-20260212-1417 does not exist remotely
GET /repos/.../compare/main...claude/issue-5-20260212-1417 - 404
```

**What happened**: The action's post-processing step tries to compare the agent's branch to `main` to create a PR. But if the agent never pushed the branch (due to permission denials or max_turns), the branch doesn't exist remotely, and the comparison returns 404.

**Root cause**: This is always a symptom of another issue — either:
- The agent ran out of turns before pushing (see [issue #4](#4-agent-hits-max_turns-before-finishing))
- A permission denial prevented `git commit` or `git push` (see [issues #6](#6-permission-denied-uv-sync) and [#7](#7-permission-denied-git-commit-heredoc-format))

**How to diagnose**: Check the `permission_denials` array in the action's log output:

```bash
gh run view <RUN_ID> --log 2>&1 | grep -A20 "permission_denials"
```

If the array is empty, check `num_turns` — the agent probably hit the limit.

**Fix**: Resolve the underlying permission or max_turns issue, then re-trigger by commenting `@claude` on the issue.

**Lesson**: A "success" result from the agent only means Claude finished its work without errors — it doesn't guarantee the branch was pushed. Always check for the PR link in the issue comment. If it says "View job" but no "View PR", the branch wasn't pushed.

---

## 6. Permission Denied: uv sync

**When**: Agent tried to run `uv sync --all-extras` inside its session.

**Error** (in `permission_denials` array):
```json
{
  "tool_name": "Bash",
  "tool_input": {
    "command": "uv sync --all-extras"
  }
}
```

**Root cause**: The permissions list included `Bash(uv run *)` but not `Bash(uv sync *)`. The glob `uv run *` doesn't match `uv sync --all-extras`.

**Why the agent tries this**: Even though `uv sync` runs in the workflow step before Claude, the agent sometimes tries to re-sync after modifying files (e.g., if it thinks new dependencies might be needed).

**Fix**: Add `"Bash(uv sync *)"` to the permissions allow list.

**Lesson**: The permission globs are literal prefix matches. `uv run *` and `uv sync *` are separate patterns. Think about all the `uv` subcommands the agent might need.

---

## 7. Permission Denied: git commit (HEREDOC Format)

**When**: Agent successfully wrote all code, ran tests, and tried to commit.

**Error** (in `permission_denials` array):
```json
{
  "tool_name": "Bash",
  "tool_input": {
    "command": "git commit -m \"$(cat <<'EOF'\nAdd OCC Wells Pipeline...\nEOF\n)\""
  }
}
```

**Root cause**: The action's built-in default includes `Bash(git commit *)`, but Claude constructs multiline commit messages using a HEREDOC pattern (`$(cat <<'EOF' ... EOF)`). The embedded newlines in the HEREDOC cause the glob pattern to fail to match.

**This was the hardest bug to find** because:
- The action reported success (`"subtype": "success"`)
- `Bash(git commit *)` was in the `ALLOWED_TOOLS` list
- The denial was only visible in the `permission_denials` array buried in the JSON output

**Fix**: Add `"Bash(git *)"` to the permissions allow list. This broader pattern matches any git command regardless of argument formatting.

```json
"allow": [
  "Bash(git *)",
  ...
]
```

**Lesson**: Claude likes to write multiline commit messages with HEREDOCs. The action's built-in `Bash(git commit *)` doesn't handle this. Always add `Bash(git *)` to your settings permissions as a safety net.

---

## 8. GitHub Label Not Found

**When**: Creating the first test issue via `gh issue create --label "pipeline-request"`.

**Error**:
```
label "pipeline-request" not found
```

**Root cause**: GitHub labels must exist before they can be applied. The issue template file (`.github/ISSUE_TEMPLATE/pipeline_request.md`) references `labels: pipeline-request` in its frontmatter, but the label doesn't exist in the repo.

**Fix**: Either create the label first (`gh label create pipeline-request`) or remove the `--label` flag from the CLI command. The issue template will still work without the label existing — GitHub just won't auto-apply it.

**Lesson**: Issue templates can reference labels that don't exist yet. The template will render fine, but the label won't be applied until it's created in the repo settings.

---

## 9. Docker init.sql Not Re-running After Schema Changes

**When**: Adding new tables (e.g., `weather_forecasts` or `oklahoma_wells`) to `docker/init.sql` and expecting them to appear.

**What happened**: The new table doesn't exist even after restarting the container.

**Root cause**: PostgreSQL's `docker-entrypoint-initdb.d` scripts (like `init.sql`) only execute on the **first** container start when the data volume is empty. Subsequent starts skip initialization because the volume already contains data.

**Fix**: Remove the volume and recreate:

```bash
docker compose -f docker/docker-compose.yml down -v
docker compose -f docker/docker-compose.yml up -d
```

**Warning**: This deletes **all data** (pipeline rows, Prefect run history). If you need to preserve data, manually run the CREATE TABLE statement instead:

```bash
docker exec -it pipeline-postgres psql -U pipeline_user -d pipeline_db \
  -c "CREATE TABLE IF NOT EXISTS your_table (...);"
```

**Lesson**: Always remember `down -v` after schema changes. Consider documenting this prominently for collaborators who may add tables via PRs.

---

## 10. Retry Comments Inflate Turn Count

**When**: Re-triggering the agent with `@claude` comments after fixing permission or config issues.

**What happened**: The agent ran out of turns (`error_max_turns`) even though permissions were fixed (zero denials). The agent used 51 turns on a 50-turn limit and never reached the git push step.

**Root cause**: Each `@claude` retry comment adds to the issue thread. When the agent triggers, it reads the **entire issue thread** — the original issue body, all previous `@claude` comments, and the action's status update comments from failed runs. Processing this historical context consumes turns before the agent even starts writing code.

In our case, issue #5 had:
- The original issue body (detailed pipeline spec)
- 3 retry comments with `@claude`
- 3 action status comments from failed runs
- All of this context was re-processed on each attempt

**Fix**: Increase `--max-turns` to account for the overhead. We increased from 50 to 75:

```yaml
claude_args: "--max-turns 75"
```

**Alternative approaches**:
- Close the noisy issue and create a fresh one with a clean thread
- Edit the original issue to add context instead of adding comments
- Keep retry comments short (just `@claude` with no extra text)

**Lesson**: Budget extra turns for issues with long comment threads. A clean issue needs ~40 turns for a complex pipeline. Each retry attempt adds ~5-10 turns of overhead from context processing. For a third retry, you might need 60-75 turns.

**Cost impact**: Each turn costs API credits. The failed 51-turn run cost $2.06 with no output. Factor in retry costs when debugging permission issues — fix permissions first, then re-trigger.

---

## 11. Multiline Commit Messages Always Denied

**When**: Agent writes all code, passes tests, but `git commit` is denied — even with `Bash(git *)` in the permissions allow list.

**Error** (in `permission_denials` array):
```json
{
  "tool_name": "Bash",
  "tool_input": {
    "command": "git commit -m \"Add feature\n\nDetailed description of changes...\""
  }
}
```

**Root cause**: The permission glob matching system in Claude Code **cannot match commands containing embedded newline characters** (`\n`). The `*` wildcard in patterns like `Bash(git *)` or `Bash(git commit *)` stops matching at `\n` boundaries. This means any `git commit -m` with a multiline message — whether using literal `\n`, HEREDOCs, or `$(cat <<EOF)` — will always be denied.

**What we tried that didn't work**:
- `Bash(git commit *)` (action's built-in) — fails on `\n`
- `Bash(git *)` (broader pattern) — also fails on `\n`
- Both together — still fails

**Fix**: Add a rule to `CLAUDE.md` telling the agent to use single-line commit messages:

```markdown
## Git Conventions
- Use single-line commit messages: `git commit -m "Short description"`
- Do NOT use multiline messages (no \n, no HEREDOCs)
```

Claude reads `CLAUDE.md` before starting work and follows these conventions. With a single-line message, `Bash(git commit *)` matches correctly.

**This was the most persistent bug** — it caused 4 consecutive failed runs on issue #5 ($7+ in API costs) before we identified that the glob system fundamentally cannot handle newlines, regardless of what patterns you add.

**Lesson**: Always instruct the agent to use single-line commit messages in `CLAUDE.md`. This is a platform limitation, not a configuration error. No amount of permission tuning can fix it — the instruction to the agent is the only reliable solution.

---

## Quick Reference: Final Working claude.yml

After resolving all issues above, the working configuration is:

```yaml
- uses: anthropics/claude-code-action@v1
  with:
    anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
    claude_args: "--max-turns 75"
    settings: |
      {
        "permissions": {
          "allow": [
            "Bash(uv run *)",
            "Bash(uv sync *)",
            "Bash(git *)",
            "Bash(cat *)",
            "Read",
            "Edit",
            "MultiEdit",
            "Write",
            "Glob",
            "Grep"
          ]
        }
      }
```

**Key takeaways**:
- Use `settings` (not `allowed_tools` or `--allowedTools`) for permissions
- Include `Bash(git *)` to handle multiline commit messages
- Include `Bash(uv sync *)` alongside `Bash(uv run *)`
- Set `--max-turns 75` for complex pipeline tasks (accounts for retry overhead)
- Always check `permission_denials` in the logs when the agent succeeds but no PR appears

---

## Debugging Checklist

When the agent runs but no PR appears:

1. **Check the Actions tab** — did the workflow run? Was it `success`, `failure`, or `skipped`?
2. **If skipped** — the `@claude` trigger condition wasn't met. Check title/body for exact match.
3. **If failure** — view the logs: `gh run view <RUN_ID> --log 2>&1 | tail -80`
4. **If success but no PR** — check for permission denials:
   ```bash
   gh run view <RUN_ID> --log 2>&1 | grep -A5 "permission_denials"
   ```
5. **If no permission denials** — check `num_turns` vs `--max-turns`. The agent may have run out of turns.
6. **Re-trigger** — comment `@claude` on the issue after fixing the underlying problem.
