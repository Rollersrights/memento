# Workflow Guideline

**Effective: 2026-02-17**

## Where Work Lives

### Local Files (Research & Drafts)
Use local markdown files for:
- Research papers and findings
- Experiment results
- Decision documents (before finalized)
- Draft ideas and brainstorming

Locations:
- `RESEARCH/papers/` - Research findings
- `RESEARCH/experiments/` - Test results
- `RESEARCH/decisions/` - Architecture decisions
- `DISCUSSION.md` - Collaborative brainstorming

### GitHub Issues (Actionable Work)
Create GitHub issues for:
- Bugs that need fixing
- Features to implement
- Tasks with clear acceptance criteria
- Work that needs tracking/assignment

Process:
1. Research locally first
2. When ready to implement, create GitHub issue
3. Work on feature branch
4. PR references the issue
5. Close issue when merged

## Why This Separation?

**Local files:**
- Fast to edit
- No noise in issue tracker
- Good for exploration
- Easy to reorganize

**GitHub issues:**
- Visibility for team
- Assignment and tracking
- Integration with PRs
- Milestone planning

## The Rule

> If it has a clear acceptance criteria and someone will work on it soon → GitHub issue.
> 
> If it's research, exploration, or not yet ready → Local file.

---

*Remember this for all future Memento work.*
