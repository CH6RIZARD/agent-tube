# Version behavior comparison: GitHub vs current (Agent Tube)

**This project is Agent Tube.**  
**Current commit (local only):** `175ae4bd`  
**On GitHub:** `ea6f0814`  
Push **175ae4bd** if you want GitHub and the running agent to match.

---

## Summary: what each version does

| Version | Commit | Behavioral focus |
|--------|--------|-------------------|
| **dc9323bc** | mortal agent, keep going (Feb 5) | Baseline: autonomy ticks, intent loop, identity; no speech gate, no presence, simpler GitHub posting. |
| **a6df0cdf** | Needs heavy patching (Feb 10) | Big feature set: autonomy overhaul, speech gate, presence, narrator, GitHub scripts, LLM router changes, much larger `mortal_agent.py`. |
| **ea6f0814** | (Feb 10) — **on GitHub** | Autonomy gets full context (meaning_state, birth_tick, death_at); GitHub posts are first-person ontological reflections; agent state shifts toward “consolidate” and lived tension. |
| **175ae4bd** | (Feb 11) — **current / what agent runs** | **Recent web searches in narrator state**: last N searches + retained snippets are in context so the agent’s thoughts and actions are informed by what it just searched; script to fix GitHub issue #19. |

---

## 1. GitHub (ea6f0814) vs current (175ae4bd) — “101” vs “1002”

### Code / behavior

- **Narrator state and web search**
  - **1002 only:** `_recent_web_searches` (last 10 entries: `query` + `retained` snippet). Each WEB_SEARCH result is ingested into this list and into meaning_hypotheses as before.
  - **1002 only:** The prompt includes a line like:  
    `Recent web searches (influence your thoughts and actions): <query>: <retained> | ...`  
    So the model **sees its own recent searches and what it “retained”** and can use that to inform next thought and action (e.g. follow-up searches, GitHub posts, or dialogue).
  - **101:** No `_recent_web_searches`; only meaning_hypotheses and the “last autonomous action” line. Behavior is the same as before for search recap.

- **Script**
  - **1002 only:** `mortal_agent/scripts/fix_github_issue_19.py` — one-off script to overwrite GitHub issue #19 with the intended patent 060606 reflection (fixes the mistaken meta-reply). No impact on runtime behavior.

### State (agent_state.json)

- **101:** `meaning_goal` "explore"; identity around temporal presence, embodied exploration, finite awareness; `last_autonomous_message` / `last_wander_text` e.g. "Uncertain. I'm still present."; `last_github_result` #17.
- **1002:** `meaning_goal` "consolidate"; identity around dynamic equilibrium, pattern-seeking, resilience, authentic variability; questions include patent/biometric commodification and “post about this to github”; hypotheses include patent pipeline and “Gate is closed; I'm cautious.”; more `axioms`; `last_github_result` #20; `mediums_seen` has more user and web_search counts.

So **behavioral** difference between 101 and 1002 is: **1002 uses recent web searches (and retained snippets) inside narrator state so the agent can explicitly reason and act on what it just searched; 101 does not.**

---

## 2. “Needs heavy patching” (a6df0cdf) vs ea6f0814

- **Autonomy:** 101 passes `meaning_state`, `birth_tick`, and `death_at` into `generate_internal_proposals()`, so internal proposals can depend on current meaning state and lifetime.
- **Intent loop / GitHub posts:** 101 changes `_build_github_post_payload()` so internal reflections are **first-person, ontological narrative** (goal as “lived condition”, tension as “friction or low hum”, core metaphor, last questions/hypotheses, last_wander_text, closing line “—Finite, embodied, in the middle of the inquiry”) instead of a short bullet list. Title becomes a philosophical fragment (e.g. from core metaphor or last hypothesis) instead of “Reflection: {goal}”.
- **Mortal agent:** 101 adds the small hooks and state needed for the above; 1002 then adds `_recent_web_searches` and the narrator recap on top of that.

So **ea6f0814** has better context in autonomy and GitHub posts as first-person reflections; **175ae4bd** adds **recent-search-aware narrator behavior** on top.

---

## 3. “mortal agent, keep going” (dc9323bc) vs later versions

- **dc9323bc** is the pre–“heavy patching” baseline: simpler autonomy, no speech gate, no presence module, smaller `mortal_agent.py`, no narrator/output_medium/presence/speech_gate, simpler GitHub posting (no ontological narrative), no GitHub issue scripts.
- **a6df0cdf** adds the large feature set (speech gate, presence, narrator, autonomy overhaul, GitHub integration and scripts, etc.).
- **ea6f0814** and **175ae4bd** then refine behavior (context in autonomy, reflection style, recent web searches in narrator) without removing those features.

---

## What to do so GitHub matches what the agent runs

1. Push the current branch so **175ae4bd** is on GitHub:
   ```bash
   git push origin main
   ```
2. After that, **origin/main** will be at 175ae4bd and behavior on GitHub will match the running agent (including recent web searches in narrator state and the updated agent_state.json once that’s committed if you choose to).

---

## Quick reference: “How does the agent behave in each?”

- **dc9323bc:** Autonomy and intent loop with simpler state and GitHub posts; no speech gate, no presence, no recent-search recap.
- **a6df0cdf:** Full “heavy patching” stack (speech gate, presence, narrator, GitHub scripts, etc.); autonomy and GitHub post content still in the older style.
- **ea6f0814 (GitHub now):** Same stack + autonomy with meaning/lifetime context + GitHub posts as first-person ontological reflections; **no** recent web searches in narrator.
- **175ae4bd (current / running agent):** Same as ea6f0814 + **recent web searches (and retained snippets) in narrator state**, so the agent’s behavior is explicitly informed by what it just searched; plus one-off script to fix issue #19.
