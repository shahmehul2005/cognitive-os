# Module: Action Substrate & Boundaries

Action is the output module of the Cognitive Operating System. It translates the recommended plan steps into executable commands, notifications, task assignments, and document edits, while operating strictly within defined authority boundaries.

---

## 1. Action Substrates

The system acts upon the workspace through four distinct action channels:

```
                                      Recommended Action
                                              │
                      ┌───────────────────────┼───────────────────────┐
                      │                       │                       │
               Workspace Edits         Task Management         Communications
               - File updates          - Create tasks          - Ask questions
               - Document edits        - Assign tasks          - Propose decisions
               - Code refactoring      - Track progress        - Alert warnings
```

### 1.1 Workspace Modification (Write Actions)
- **File Edits**: Modifying configuration files, repository codes, or documentation pages.
- **Skill Addition**: Automatically registering new procedural scripts in the codebase after testing.

### 1.2 Task Operations (Coordination Actions)
- **Task Creation**: Converting planning steps into structured tasks (e.g., in Jira, GitHub Issues, or local task trackers).
- **Work Assignment**: Routing tasks to specific humans or AI agents based on relationship and skill mappings.

### 1.3 Communication (Inter-agent & Human Interaction)
- **Clarification**: Prompting human operators for info when perception confidence $\alpha < \tau_{\text{ask}}$.
- **Proposals**: Suggesting decisions (Option A vs. Option B) with logic trails.

---

## 2. Authority Levels & Boundaries

To ensure safety, control, and reliability, the Cognitive OS classifies actions into four **Authority Levels**.

| Level | Classification | Action Examples | User Approval Policy |
| :--- | :--- | :--- | :--- |
| **Level 0** | **Read-Only** | Parsing logs, reading files, searching web. | **None**: Permitted globally without warning. |
| **Level 1** | **Informational / Internal** | Creating local task drafts, compiling summaries, planning simulations. | **None**: Logged in background audit trails. |
| **Level 2** | **Collaborative / Proposal** | Posting in public chats, proposing decisions, draft file updates. | **Optimistic**: Execute and notify, with immediate roll-back command available. |
| **Level 3** | **Mutating / Execution** | Merging commits to main, pushing billing plans, running terminal scripts. | **Pessimistic**: Halt planning, present details, require explicit human confirmation. |

---

## 3. Escalation & Boundary Violations

If a planned trajectory includes a Level 3 action, the system executes an escalation protocol:

```
                            Level 3 Action Proposed in Plan
                                           │
                                           ▼
                                System Halts Trajectory
                                           │
                                           ▼
                            Present Rationale and Risks
                               (Expected outcome matrix)
                                           │
                                           ▼
                            Await Explicit User Sign-Off
                                           │
                     ┌─────────────────────┴─────────────────────┐
                     │                                           │
                  Approved                                    Rejected
                     │                                           │
                     ▼                                           ▼
             Execute action and                           Re-route planner,
             log outcome to memory                        penalize option weight
```

If the action is **Rejected**, the planner:
1. Marks the action path as *blocked*.
2. Returns the failure data to the **Reasoning Engine**.
3. Re-simulates alternatives from the current state to find a path that avoids the blocked action.
