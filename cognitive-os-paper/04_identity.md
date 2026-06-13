# Module: Identity & Filters

This document defines the structural representation of the system's **Identity** and explains how identity acts as a constraint filter for reasoning and planning.

---

## 1. Identity Schema

Identity is represented as a structured data model loaded at startup and updated during strategic reviews.

```json
{
  "identity_schema_version": "1.0",
  "mission": {
    "core_purpose": "Build a Cognitive Operating System for Teams to align collective intelligence.",
    "horizon": "5-year timeline"
  },
  "vision": {
    "target_state": "Every enterprise workspace executes with fluid, friction-free AI-human cognitive loops."
  },
  "values": [
    {
      "name": "Rigorous Theory",
      "description": "Establish deep, mathematically backed conceptual foundations before writing code."
    },
    {
      "name": "Transparency",
      "description": "Keep all decision rationale audit trails readable to humans."
    }
  ],
  "principles": [
    "Prioritize collective memory consolidation over immediate storage.",
    "Minimize coordination overhead at all cost."
  ],
  "constraints": {
    "resource_limits": {
      "max_monthly_compute_budget_usd": 500
    },
    "security": {
      "allow_external_execution_without_approval": false
    }
  },
  "current_strategy": {
    "focus": "Theory Phase and conceptual documentation modeling.",
    "stage": "Pre-MVP (Stage 2)"
  },
  "risk_appetite": {
    "operational_risk": "low",
    "experimental_risk": "high"
  },
  "culture": {
    "communication_style": "rigorous, concise, research-grade"
  },
  "goals": [
    {
      "id": "goal_01",
      "description": "Complete Cognitive OS Phase 1 modules specifications.",
      "target_date": "2026-07-01"
    }
  ]
}
```

---

## 2. Influence of Identity on Reasoning

Identity acts as a heuristic modulator and boundary check on the system's **Reasoning Engine** and **Planning** modules. Rather than letting the system search the entire space of possible actions, Identity constrains the search path.

```
                      Planning Module Proposes Trajectories (Option A, B, C)
                                               │
                                               ▼
                              Identity Constraint Evaluator (Φ_id)
                                               │
                       ┌───────────────────────┴───────────────────────┐
                       │                                               │
              Satisfies Constraints?                         Violates Constraints?
                       │                                               │
                       ▼                                               ▼
             Keep path and evaluate                         Prune path immediately
                  expected utility                        (Log violation warning)
```

### 2.1 Action Utility Modulation
Every planned action sequence $\tau$ has a raw expected reward $R_{raw}(\tau)$. The Identity constraints scale this reward:
$$R_{effective}(\tau) = R_{raw}(\tau) \cdot \prod_{v \in \text{Values}} w_v \cdot \text{Match}(\tau, v)$$
Where:
- $w_v \in [0, 1]$ is the weight of value $v$.
- $\text{Match}(\tau, v) \in [0, 1]$ measures how well the proposed action trajectory aligns with the value definition. If an action violates a value (e.g., non-transparent execution when transparency is valued), $\text{Match}(\tau, v) \to 0$, rendering the action's effective reward zero.

### 2.2 Boundary Checking (Hard Constraints)
While values act as soft modulators, `constraints` act as hard boundaries. Before any plan is committed to **Action**, the system runs an assertion check:
$$\forall c \in \text{Constraints}, \quad \text{Assert}(a_i, c) = \text{True}$$
If any action $a_i$ violates a constraint $c$ (e.g., attempting external command execution without user approval when forbidden), the Reasoning Engine raises a safety exception, aborts the plan, and flags the conflict to the workspace human operators.

---

## 3. Cognitive Algorithms

### 3.1 UpdateIdentity()
Modulates global constraints, strategies, and appetites based on cumulative feedback outcomes.

* **Inputs**:
  - `realized_outcomes`: List of tuples containing `(task_id, success_rating, failure_category)`.
  - `goal_status`: List of updates to goals `(goal_id, is_completed)`.
* **Output**:
  - `identity_updated`: Boolean indicating if a change was written to the schema.

```python
def UpdateIdentity(realized_outcomes, goal_status):
    identity = Configuration.load_identity()
    updated = False
    
    # 1. Goal Status Consolidation
    for goal_id, is_completed in goal_status:
        goal = next((g for g in identity.goals if g.id == goal_id), None)
        if goal and is_completed and goal.status != "achieved":
            goal.status = "achieved"
            updated = True
            Log("Goal achieved: " + goal.description)
            
    # 2. Strategic Shift Verification
    all_active_goals_achieved = all(g.status == "achieved" for g in identity.goals)
    if all_active_goals_achieved and identity.current_strategy.stage == "Pre-MVP (Stage 2)":
        # Transition strategy to MVP implementation
        identity.current_strategy.focus = "MVP Implementation Phase"
        identity.current_strategy.stage = "MVP (Stage 6)"
        # Add next set of standard goals
        identity.goals.append({
            "id": "goal_02",
            "description": "Initialize database engines and build collective memory schema.",
            "target_date": get_relative_date(days=30),
            "status": "pending"
        })
        updated = True
        
    # 3. Dynamic Risk Appetite Calibration
    high_impact_failures = [o for o in realized_outcomes if o.success_rating < -0.8 and o.failure_category == "security"]
    if len(high_impact_failures) >= 2:
        # Tighten constraints dynamically if safety bounds are repeatedly hit
        if identity.constraints.security.allow_external_execution_without_approval:
            identity.constraints.security.allow_external_execution_without_approval = False
            identity.risk_appetite.operational_risk = "extremely_low"
            updated = True
            Log("Warning: High operational failures detected. Disabling autonomous external execution.")
            
    if updated:
        Configuration.save_identity(identity)
        
    return updated
```

---

## 4. Success Metrics & Evaluation

To ensure the system remains aligned with team culture and rules, we measure the **Consistency of AI Decisions with Team Principles**.

### 4.1 Formulations

1. **Hard Constraint Alignment ($A_{\text{hard}}$)**:
   $$A_{\text{hard}} = 1.0 - \frac{|D_{\text{violated\_hard}}|}{|D_{\text{total}}|}$$
   *Measures the proportion of executed decisions that strictly adhered to the hard security and operational boundaries.*

2. **Soft Value Alignment ($A_{\text{soft}}$)**:
   $$A_{\text{soft}} = \frac{1}{|D_{\text{total}}|} \sum_{d \in D} \prod_{v \in \text{Values}} \text{Match}(d, v)$$
   *Measures the average alignment score of decision paths with the team's soft culture and values (transparency, theory first, etc.).*

### 4.2 Evaluation Protocol

During the Weekly Consolidation run, the system audits the last 7 days of Decisions Memory:
- **Assertion**:
  - We require $A_{\text{hard}} = 1.0$ (zero tolerance for hard boundary violations).
  - We require $A_{\text{soft}} \ge 0.90$.
- **Mitigation**: If $A_{\text{soft}} < 0.90$, the learning engine generates a value misalignment analysis report, surfacing the offending decision profiles to the founders for manual alignment adjustments.


