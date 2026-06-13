# Module: MVP Specification

This document specifies the exact scope and functional boundaries of the Cognitive Operating System's Minimum Viable Product (MVP). The MVP is designed to run locally, establishing that a shared workspace context can be dynamically managed and consolidated.

---

## 1. Scope Boundaries

To maintain speed and focus on our core value proposition, the MVP is strictly bounded by the following rules:

```
                            MVP Scope Constraints
       ┌───────────────────────────────┼───────────────────────────────┐
       │                               │                               │
    IN SCOPE                        OUT OF SCOPE                    LIMITS
    - 2 Founders                    - Calendar Sync                 - CLI/File interface
    - 1 Shared AI Agent             - Email Integrations            - Single local directory
    - Local Decision Engine         - Slack/Discord Webhooks        - Max 1000 memory nodes
    - Workspace Identity Schema     - Enterprise Permissions
    - Local Memory Engine           - User Authentication UI
    - Nightly Consolidation Cron
```

---

## 2. Core Components

The MVP contains four functional modules implemented as local scripts running in a single Python execution environment:

### 2.1 Workspace Identity
- **File**: `workspace_identity.json`
- **Logic**: Loads the core mission parameters, constraint variables (e.g., maximum budget), and target goals. Modulates all plan utilities.

### 2.2 Memory Engine (SQLite/JSON + Vectors)
- **Files**: `memory_db.sqlite` (for episodic logs and semantic graph triples) and `embeddings.json` (for vector embeddings).
- **Logic**: Implements localized versions of `Remember()`, `Retrieve()`, and `RankImportance()`. Runs vector checks against query inputs.

### 2.3 Decision & Planning Engine
- **Files**: `decision_engine.py`
- **Logic**: Parses inputs for decision triggers. Performs simulations over proposed trajectories, checks constraints in `workspace_identity.json`, prints a comparative Option A vs. Option B recommendation schema, and logs output to Decision memory.

### 2.4 Consolidation Loop
- **Files**: `consolidation_daemon.py` (triggered via system daemon or cron).
- **Logic**: Runs a nightly compression loop that:
  - Abstracts episodic logs into semantic graph entities.
  - Deletes expired items using the `Forget()` algorithm.
  - Updates goal completions and records failures.

---

## 3. Verification Scenario

To prove the MVP successfully makes the workspace smarter over time, we will run the following verification scenario:

```
    Step 1: Setup Workspace -> Load Identity ("Build MVP in 30 days")
                                     │
                                     ▼
    Step 2: Episodic Input -> Founder A states "Database decision: Pick SQLite for speed."
                                     │
                                     ▼
    Step 3: Run Consolidation -> Abstract episode to Semantic fact: (SQLite, usedFor, Database)
                                     │
                                     ▼
    Step 4: Query Retrieval -> Founder B asks "What database engine are we using?"
                                     │
                                     ▼
    Expected Output: AI correctly retrieves fact "SQLite" from consolidated Semantic Memory.
```

### 3.1 Success Metrics
- **Retrieval accuracy**: 100% correct matching on the database engine.
- **Episodic cleanup**: The raw chat log containing the decision is successfully pruned or archived, leaving the active workspace index clean and unpolluted.
