# Module: Future Simulation & Planning

Planning is the proactive simulation of alternative future paths to select the trajectory that best satisfies the system's goals and identity constraints. It bridges the gap between reasoning (what is true) and action (what to do).

---

## 1. The Simulation Loop

For any given goal state $S_G$, the planning module evaluates multiple paths ($\tau_A, \tau_B, \dots$) using a simulation loop:

```
                                      Goal State (S_G)
                                             │
                                             ▼
                             Action Path Simulation Generator
                                             │
                    ┌────────────────────────┴────────────────────────┐
                    │                                                 │
                Option A                                          Option B
                    │                                                 │
                    ▼                                                 ▼
             Outcome Prediction                                Outcome Prediction
        (Transition Probabilities)                        (Transition Probabilities)
                    │                                                 │
                    ▼                                                 ▼
              Risk Appraisal                                    Risk Appraisal
             (Failure Nodes)                                   (Failure Nodes)
                    │                                                 │
                    └────────────────────────┬────────────────────────┘
                                             │
                                             ▼
                                  Path Recommendation Matrix
                                       (Maximum Utility)
```

### 1.1 Action Path Generation
The planner queries **Procedural Memory** to compile a set of sequence actions (tasks) that can transition the workspace from current state $S_0$ to target state $S_G$. If multiple paths are possible:
- **Option A**: Low risk, high compute time (e.g., run full test suites before pushing).
- **Option B**: High risk, low compute time (e.g., hotfix directly with smoke tests).

### 1.2 Transition Probability & Prediction
The engine calculates the transition probability $P(s_{t+1} \mid s_t, a_t)$ using historical records from **Episodic** and **Failure Memory**:
- If action $a_t$ has historically failed in similar contexts, the probability of reaching the success state is decreased.

### 1.3 Risk Appraisal
Each simulated trajectory $\tau$ is scanned for potential failure modes:
$$\text{Risk}(\tau) = \sum_{a \in \tau} P(\text{Failure} \mid a) \cdot \text{Cost}(\text{Failure})$$
Where:
- $P(\text{Failure} \mid a)$ is the probability of action failure (derived from Failure Memory).
- $\text{Cost}(\text{Failure})$ is the impact score (e.g., loss of user trust, compute budget wastage).

---

## 2. Planning Recommendation Schema

Before executing any plan, the system structures the output as a comparative **Recommendation Matrix**. This is presented to the human operators or passed directly to the Action module depending on the authority boundaries.

```json
{
  "goal_id": "goal_01",
  "current_state": "workspace_build_failing",
  "target_state": "workspace_build_passing_with_docs",
  "simulations": [
    {
      "option_id": "option_A",
      "steps": [
        "Create branch fix/auth-token",
        "Re-write logic to handle null tokens in auth_helper.py",
        "Run local tests unit/*.py",
        "Submit pull request and auto-merge if passing"
      ],
      "predicted_outcome": "build_success_clean",
      "probability_of_success": 0.92,
      "estimated_compute_cost_usd": 0.05,
      "risk_analysis": {
        "severity": "low",
        "description": "Slow validation delay; blocks active deployment by 15 mins."
      }
    },
    {
      "option_id": "option_B",
      "steps": [
        "Edit auth_helper.py directly on main branch",
        "Push commits directly bypassing PR checks"
      ],
      "predicted_outcome": "build_success_dirty",
      "probability_of_success": 0.60,
      "estimated_compute_cost_usd": 0.01,
      "risk_analysis": {
        "severity": "high",
        "description": "High chance of breaking production tests. Violates constraints.security.allow_external_execution."
      }
    }
  ],
  "recommendation": "option_A"
}
```
---

## 3. Dynamic Plan Re-calibration
Planning is not static. If the **Perception** module detects a new event during plan execution (e.g., a test failure occurs during step 3), the planner halts execution, feeds the failure into the **Reasoning Engine**, updates the transition probabilities, and re-runs the simulation tree to compute a corrective path.

---

## 4. Cognitive Algorithms

### 4.1 Predict()
Estimates the transition outcome, probability of success, and risk index of a proposed action.

* **Inputs**:
  - `current_state`: State dictionary $S_t$.
  - `action`: Proposed action dictionary $a_t$.
* **Output**:
  - `prediction`: Dict containing `{"next_state": State, "probability": Float, "risk": Float}`.

```python
def Predict(current_state, action):
    # Search Failure Memory for matching actions in similar contexts
    failure_nodes = Database.query_failures(action_type=action["type"], state_context=current_state)
    total_runs = Database.count_historical_actions(action["type"])
    
    if total_runs == 0:
        # Optimistic assumption for brand-new actions
        success_probability = 0.90
        risk_index = 0.10
    else:
        failure_count = len(failure_nodes)
        success_probability = 1.0 - (failure_count / total_runs)
        
        # Calculate risk severity based on failure impacts
        total_severity = sum(f.impact_severity for f in failure_nodes)
        risk_index = (total_severity / total_runs) if failure_count > 0 else 0.05
        
    predicted_state = ExtrapolateNextState(current_state, action)
    
    return {
        "next_state": predicted_state,
        "probability": max(0.01, success_probability),
        "risk": min(1.0, risk_index)
    }
```

### 4.2 Plan()
Generates and compares action trajectories to achieve a target goal state.

* **Inputs**:
  - `target_state`: Target Goal state $S_G$.
* **Output**:
  - `recommendation_matrix`: JSON object listing simulated trajectories, risk indicators, and the recommended selection.

```python
def Plan(target_state):
    current_state = GetCurrentWorkspaceState()
    identity = Configuration.load_identity()
    
    # Generate candidate paths via tree search (MCTS / A*)
    candidate_paths = SearchTrajectoryTree(current_state, target_state)
    simulations = []
    
    for path in candidate_paths:
        path_probability = 1.0
        total_risk = 0.0
        estimated_cost = 0.0
        temp_state = current_state
        is_valid = True
        
        for action in path["steps"]:
            # Evaluate hard boundary constraint satisfaction
            if not SatisfiesConstraints(action, identity.constraints):
                is_valid = False
                break
                
            prediction = Predict(temp_state, action)
            path_probability *= prediction["probability"]
            total_risk += prediction["risk"]
            estimated_cost += CalculateActionCost(action)
            temp_state = prediction["next_state"]
            
        if is_valid:
            simulations.append({
                "option_id": path["id"],
                "steps": path["steps"],
                "predicted_outcome": "success" if path_probability > 0.5 else "failure",
                "probability_of_success": path_probability,
                "estimated_compute_cost_usd": estimated_cost,
                "risk_analysis": {
                    "severity": "high" if total_risk > 0.6 else "low",
                    "description": f"Cumulative path risk is {total_risk:.2f}"
                }
            })
            
    # Re-rank options based on identity value utility multipliers
    for option in simulations:
        option["utility"] = CalculateEffectiveUtility(option, identity.values)
        
    simulations.sort(key=lambda x: x["utility"], reverse=True)
    best_recommendation = simulations[0]["option_id"] if simulations else None
    
    return {
        "goal_id": target_state.get("goal_id", "unspecified"),
        "current_state": current_state,
        "target_state": target_state,
        "simulations": simulations,
        "recommendation": best_recommendation
    }
```

---

## 5. Success Metrics & Evaluation

To verify our future simulations, we measure the **Prediction Quality** of the transition probability models.

### 5.1 Formulations

1. **Prediction Cross-Entropy Loss ($L_{\text{pred}}$)**:
   $$L_{\text{pred}} = -\frac{1}{|A_{\text{executed}}|} \sum_{i=1}^{|A_{\text{executed}}|} \sum_{s' \in S} \mathbb{I}(s_{i,\text{realized}} = s') \cdot \log P(s' \mid s_i, a_i)$$
   *Measures the accuracy of the transition probability distribution predicted by the simulation engine compared to the actual state realized in the workspace.*

2. **Risk Calibration Variance ($\sigma^2_{\text{risk}}$)**:
   $$\sigma^2_{\text{risk}} = \frac{1}{|A_{\text{executed}}|} \sum_{i=1}^{|A_{\text{executed}}|} \left( \mathbb{I}(\text{Fail}_i) - \text{Risk}(a_i) \right)^2$$
   *Measures how closely our computed risk index matches the historical action failure rates.*

### 5.2 Evaluation Protocol

During the Weekly Consolidation audit:
- **Calculation**: Compile all Level 3 and Level 2 actions executed. Compare the expected outcomes in the simulated recommendations with git repository history and build logs.
- **Goal Bounds**:
  - We require $L_{\text{pred}} \le 0.25$.
  - We require $\sigma^2_{\text{risk}} \le 0.05$.
- **Correction Loop**: If $L_{\text{pred}} > 0.35$, the system triggers a **Prior Optimization** sweep, shifting historical weights in Failure Memory to align probability weights with actual observations.


