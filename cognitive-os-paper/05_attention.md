# Module: Attention & Empirical Routing

Attention is the primary gatekeeper of the Cognitive Operating System. The moat of this architecture is not its ability to store everything, but its ability to aggressively filter $99.2\%$ of noise so that the remaining $0.8\%$ of high-utility strategic beliefs can be processed efficiently by the Reasoning module.

---

## 1. The Attention Selection Function

When a raw signal arrives, the Attention Engine must assign it a dynamic score and route it in sub-milliseconds to determine if it should be instantiated as a Belief in the central graph.

### 1.1 The Scoring Formula
The raw attention score is a mathematically formalized function of Urgency, Structural complexity, and Source authority:

$$S_{att} = w_u \cdot U(x) + w_s \cdot S(x) + w_a \cdot A(x)$$

Where:
- $U(x)$: Urgency density (keyword presence normalized by length penalty to filter log storms).
- $S(x)$: Structural density (presence of valid NLP entities and verbs).
- $A(x)$: Authority weight of the source node.

### 1.2 Empirical Weight Calibration (The "Why")

In early prototypes, weighting constants (e.g., $w_u = 0.50$, $w_s = 0.35$, $w_a = 0.15$) and routing thresholds (e.g., `THRESHOLD_ACT = 0.75`) were assigned heuristically. 

**This is theoretically invalid for a true cognitive architecture.**

In the Cognitive OS, these values are not arbitrary constants; they are **Priors**. They must be empirically derived and continuously adapted through a feedback loop:
1. **Ground Truth Labeling**: Human operators label a subset of organizational signals (e.g., $\{ \text{payload}, \text{expected\_route} \}$).
2. **F1-Score Optimization**: The OS runs a background hyperparameter tuning loop over the dataset to find the exact thresholds that maximize the F1-score (precision and recall) of the routing decisions.
3. **Continuous Adaptation**: As the organization's language and operational tempo change (e.g., during an incident versus during a holiday), the Learning module shifts these weights dynamically to prevent attention fatigue.

---

## 2. Attention Failure Modes & Recoveries

The selection function is probabilistic. The Cognitive OS explicitly defines how to recover when the Attention Engine drops the ball or hallucinates.

### 2.1 Failure Mode 1: False Negative (The "Dropped Ball")
**Scenario**: A critical bug is reported. The payload lacks structural verbs (e.g., "it broke again"), so $S(x)$ evaluates to $0.0$. The $S_{att}$ evaluates to $0.35$. The system drops it.
**Recovery Mechanism**: The `Resonance Check`.
- If a signal is dropped, but its embedding is highly similar to $N$ other dropped signals within a 24-hour window, the Consolidation module aggregates them and forces a routing bypass, escalating the aggregate signal directly to Reasoning.

### 2.2 Failure Mode 2: False Positive (The "Panic Attack")
**Scenario**: The CEO uses the word "migrate" metaphorically ("We need to migrate our thinking"). Urgency $U(x)$ spikes. The system panics, routes it to Action, and tries to generate a database migration plan.
**Recovery Mechanism**: The `Reasoning Reality Check`.
- Attention is just a gate. It passes the candidate belief to the Truth Maintenance System (Reasoning). 
- Reasoning extracts the semantic triple: `(Thinking, migrate, None)`. 
- Because the object does not map to a known infrastructure node in the Belief Graph, Reasoning flags it as a `Metaphor` and safely degrades the belief to episodic memory without triggering an action.
