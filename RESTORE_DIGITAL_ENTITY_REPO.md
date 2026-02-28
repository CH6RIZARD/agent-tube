# How to restore the digital-entity repo on GitHub

**Goal:** [digital-entity](https://github.com/CH6RIZARD/digital-entity) should contain only the **digital entity** (mortal agent) project. No Agent Tube content (no dorm, server.py, Agent Tube README). This workspace (agent-tube) is tied to [agent-tube](https://github.com/CH6RIZARD/agent-tube).

---

## Option 1: Reset digital-entity to a commit from before the mesh (recommended if you have the hash)

Use this if you know the commit on digital-entity that was “digital entity only” (e.g. before dorm, server.py, Agent Tube README were pushed there).

1. **Clone digital-entity in a separate folder** (not inside agenttube):
   ```powershell
   cd D:\
   git clone https://github.com/CH6RIZARD/digital-entity.git digital-entity-restore
   cd digital-entity-restore
   ```

2. **Find the right commit** (the last one that did *not* have Agent Tube files):
   ```powershell
   git log --oneline
   ```
   Look for a commit **before** you see “Agent Tube”, “dorm”, “server.py”, “Push agent-tube”, etc. Note that commit hash (e.g. `ea6f0814` or `175ae4bd`).

3. **Reset main to that commit and force-push**:
   ```powershell
   git checkout main
   git reset --hard <COMMIT_HASH>
   git push origin main --force
   ```
   Replace `<COMMIT_HASH>` with the hash from step 2.

4. **Update the README on digital-entity** (so it’s clearly “digital entity”, not Agent Tube):
   - On GitHub: open **digital-entity** → **README.md** → Edit.
   - Replace the contents with the text from **README_FOR_DIGITAL_ENTITY_REPO.md** in this (agent-tube) workspace.
   - Commit the change.

---

## Option 2: Fix digital-entity without rewriting history (remove Agent Tube files + README)

Use this if you want to keep current commits but remove only Agent Tube content and fix the README.

1. **Clone digital-entity** in a separate folder:
   ```powershell
   cd D:\
   git clone https://github.com/CH6RIZARD/digital-entity.git digital-entity-fix
   cd digital-entity-fix
   ```

2. **Remove files that belong only to Agent Tube** (they should not be in digital-entity):
   ```powershell
   git rm --cached "dorm_v2 (21).html" hugo.glb server.py run.py SpawnLoadout.js requirements.txt run_soak_test.py 2>$null
   Remove-Item -Path "dorm_v2 (21).html", "hugo.glb", "server.py", "run.py", "SpawnLoadout.js", "requirements.txt", "run_soak_test.py" -ErrorAction SilentlyContinue
   ```
   If any of these don’t exist in the clone, that’s fine. Then remove them from the repo if they’re still tracked:
   ```powershell
   git status
   git rm "dorm_v2 (21).html" hugo.glb server.py run.py SpawnLoadout.js requirements.txt run_soak_test.py 2>$null; git status
   ```

3. **Replace README.md with the digital-entity README**  
   Copy the full contents of **README_FOR_DIGITAL_ENTITY_REPO.md** from this (agent-tube) workspace into `README.md` in the digital-entity-fix clone, then:
   ```powershell
   git add README.md
   git commit -m "digital-entity only: restore README, remove Agent Tube assets"
   git push origin main
   ```

4. **Optional:** Add a **.gitignore** entry so you don’t re-add these by mistake when working from a shared folder:
   ```
   /dorm_v2*
   /hugo.glb
   /server.py
   /run.py
   /SpawnLoadout.js
   /requirements.txt
   /run_soak_test.py
   ```
   Only if those paths are meant to exist only in agent-tube.

---

## Summary

| Repo | Purpose | README |
|------|--------|--------|
| **digital-entity** | Mortal agent / digital entity only (no dorm, no server.py) | Use **README_FOR_DIGITAL_ENTITY_REPO.md** from this workspace |
| **agent-tube** (this workspace) | Agent Tube: mortal agent + dorm sim + server.py + SpawnLoadout, etc. | **README.md** in this repo (Agent Tube) |

After restoring digital-entity, push **this** workspace only to **agent-tube**:
```powershell
cd D:\agenttube
git push agent-tube main
```
