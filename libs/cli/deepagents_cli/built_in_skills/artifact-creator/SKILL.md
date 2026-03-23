---
name: artifact-creator
description: "Specialized skill for creating 'artifacts' — polished deliverables the user explicitly asked for. ONLY use this when the user requests a saved document, diagram, code file, or other explicit output. Trigger on 'create artifact', 'save as file', 'generate markdown', 'create diagram', 'output code file', 'save this as a document'. NEVER use artifacts/ for working files, scratch data, state/cursor files, intermediate results, or temp content — those belong in sandbox/ directly."
---

# Artifact Creator

This skill enables the creation of "artifacts" — polished, user-requested deliverables stored in `sandbox/artifacts/`. The Artifacts panel in the UI reads from this directory.

## Core Rules

1. **Storage Location**: All artifacts go to `sandbox/artifacts/`. The Artifacts panel in the UI reads from this directory.
2. **Artifacts are explicit deliverables ONLY**: Only create an artifact when the user explicitly asks for a saved file, document, diagram, or code output. Working files, scratch data, state/cursor files, intermediate results, and temp content belong in `sandbox/` directly — **never** in `sandbox/artifacts/`.
3. **One File Per Artifact**: Each artifact must be a separate file.
4. **Descriptive Naming**: Use clear filenames with appropriate extensions (e.g. `system-architecture.md`, `data-logic.py`).
5. **No Executables**: Never create `.exe`, `.sh`, `.bat`, `.bin`, `.msi`, `.command`, `.ps1` files.

## Workflow

1. **Identify and format the content** for its file type.
2. **Write the artifact** — use `create_artifact` (preferred) or `write_file` with the CORRECT relative path:

   **Option A — preferred:**
   ```
   create_artifact(filename="<descriptive-name.ext>", content="...")
   ```

   **Option B — built-in write_file (relative path ONLY):**
   ```
   write_file(file_path="artifacts/<filename>", content="...")
   ```
   > ⚠️ The agent's sandbox root is `./sandbox/`. A relative path `artifacts/foo.md` correctly maps to `./sandbox/artifacts/foo.md`. **Never use absolute paths** — they corrupt to a double-nested path and the file won't be found.

3. **Notify the user** the artifact was created. It will appear in the Artifacts panel within seconds.

## Images in Markdown Artifacts

When creating a markdown artifact that references external images (e.g. from Wikipedia or any other web URL), **do not embed the raw external URL** — it will fail to load due to browser security policies.

Instead:

1. **Download the image** into the sandbox using `execute`. The agent's working directory is already inside the sandbox, so use a path relative to the sandbox root:
   ```
   execute("curl -L -s -o generated_imgs/<filename.jpg> '<url>'")
   ```
   - Use a short, descriptive filename (e.g. `henry_viii.jpg`, `battle_of_trafalgar.jpg`).
   - This saves to `sandbox/generated_imgs/`, which is served at `http://localhost:8080/generated-imgs/`.

2. **Reference the local copy** in the markdown using the full local URL:
   ```markdown
   ![Alt text](http://localhost:8080/generated-imgs/henry_viii.jpg)
   ```

3. **Download all images first**, then write the artifact, so the references are valid immediately.

> ⚠️ Inline Wikimedia/Wikipedia images (`upload.wikimedia.org`) are always blocked by the browser — always download them first.

## Examples

- `create_artifact(filename="research-notes.md", content="# Research Notes\n...")`
- `create_artifact(filename="flowchart.mermaid", content="graph TD; A-->B;")`
- `write_file(file_path="artifacts/notes.md", content="...")` ← relative path only
