---
name: create-pr
description: Create a GitHub pull request from current branch with proper format and checks
---

# Create PR

Create a pull request from the current branch.

## Steps

1. **Get current branch and status:**

   ```bash
   git branch --show-current
   git status
   ```

   If on main/master, ask: "You're on main. Do you want to create a branch?"
   - If yes, ask for branch name and create it
   - If no, abort

2. **Show summary of changes** (commits since main):

   ```bash
   git log main..HEAD --oneline
   git diff main..HEAD --stat
   ```

3. **Check for uncommitted changes:**
   If there are uncommitted changes, ask: "There are uncommitted changes. Do you want to commit them?"
   - Options: "Yes, commit all" / "Yes, let me select files" / "No, continue without committing"

   If committing, use conventional commits format: `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`, `test:`, `style:`.

4. **Run auto-fix and checks:**

   ```bash
   make fix-all
   make check-all
   ```

   Fix any remaining issues before proceeding.

5. **Push to remote:**

   ```bash
   git push -u origin <branch>
   ```

6. **Extract PR info from commits/branch:**
   - Extract ticket ID from branch name if present (e.g., `rodruizronaldcr/hnt-5-implement-agentic-foundation` -> `HNT-5`)
   - Summarize changes from commit messages

7. **Create PR:**

   ```bash
   gh pr create --title "<type>(<ticket-id>): <description>" --body "$(cat <<'EOF'
   ## Summary

   <bullet points of what was done>

   ## Linear Ticket

   <link to Linear ticket if ticket ID found, otherwise remove section>

   ## Test Plan

   - [ ] make check-all passes
   - [ ] Manually verified the change works as expected

   EOF
   )"
   ```

8. **Show PR URL** to user.

9. **Ask if user wants to open the PR in browser:**
   ```bash
   gh pr view --web
   ```

## Notes

- If no ticket ID found in branch name, omit the Linear Ticket section
- PR title format: `type(TICKET-ID): description` or `type: description` if no ticket (e.g., `feat(HNT-5): add agent PoC`)
- Always run `make fix-all` then `make check-all` before creating PR
- If checks fail, fix issues and re-run before proceeding
