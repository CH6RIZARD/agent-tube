# Comparison: This Version vs GitHub (Agent Tube)

## Summary

- **GitHub (origin/main):** `ea6f0814` (legacy commit message)
- **Your current version:** 1 local commit ahead of GitHub + uncommitted changes.

**This project is Agent Tube.** Historical commit messages in the log may still say “Digital entity 101” / “digital entity 1002”; those are old labels, not the project name. What’s on GitHub is `origin/main` at `ea6f0814`.

---

## Commits on GitHub (origin/main)

| Hash      | Message (legacy label) |
|-----------|-------------------------|
| `ea6f0814` | (was: Digital entity 101) |

---

## Your Local Commits Not on GitHub (ahead by 1)

| Hash      | Message (legacy label) |
|-----------|-------------------------|
| `175ae4bd` | (was: digital entity 1002) |

So **this version** adds one commit on top of GitHub.

---

## Uncommitted Changes (working tree)

- **Modified:** `mortal_agent/state/agent_state.json`

In that file, the only difference from the last commit is in **`mediums_seen`**:  
`"web_search": 14` → **`"web_search": 15`** (one more web_search since the last commit). All other fields (meaning_goal, meaning_questions, identity_self_description, turn_count, etc.) match the committed version.

---

## Timeline (from reflog)

- **1770338056** (~Feb 6): `dc9323bc` — mortal agent, keep going  
- **1770779193** (Feb 11): `a6df0cdf` — Needs heavy patching  
- **1770782597** (Feb 11): `ea6f0814` ← **origin/main**  
- **1770793945** (Feb 11): `175ae4bd` ← **HEAD**

---

## In Short

| Baseline (GitHub) | This version |
|-------------------|--------------|
| `ea6f0814` (GitHub) | Same + **1 commit** (`175ae4bd`) + **1 file changed** (`mortal_agent/state/agent_state.json`: `web_search` 14→15) |

To see the full line-by-line diff in your repo, run:

```bash
git diff origin/main
```

That shows both the committed diff (origin/main..HEAD) and the working-tree changes.
