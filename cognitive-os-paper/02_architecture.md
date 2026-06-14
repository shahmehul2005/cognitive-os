# Module: Architecture & The Belief Graph Topology

This document details the global recurrent topology of the Cognitive Operating System (Cognitive OS). We depart from traditional microservice architectures. Instead, the architecture is a set of formal mathematical operations executed over a single, central data structure: **The Belief Graph**.

---

## 1. The Central Belief Graph

At the core of the Cognitive OS is a directed, weighted graph $\mathcal{G} = (\mathcal{V}, \mathcal{E}, \mathcal{W})$ where:
- $\mathcal{V}$ are **Beliefs** (semantic claims).
- $\mathcal{E}$ are **Logical Dependencies** (e.g., Belief A *implies* Belief B, or Belief C *contradicts* Belief D).
- $\mathcal{W}$ are the **Confidence Weights** and **Decay Rates** associated with each belief.

Every module in the Cognitive OS is simply a functional operation applied to this graph.

---

## 2. Global Recurrent Topology

Because collective intelligence is continuous and adaptive, the modules constantly feed back into the graph in a recurrent loop.

```text
                      The Belief Graph (Central Truth)
                      
                      ↗                   \
                     /                     ▼
        Attention (05) ◄─── Reasoning (08) ───► Identity (04)
        [Selection]         [Constraint Prop.]  [Boundary Filter]
        
              ▲                  │                  │
              │                  │                  ▼
        Perception (02) ◄── Prediction (09)     Planning (09)
        [Signal Ingest]     [Surprise Eval]     [Trajectory Proj.]
                                                    │
                                                    ▼
                                                Action (10)
                                                [Execution]
                                                    │
                                                    ▼
                                              Learning &
                                          Consolidation (06)
                                          [Weight Calibration]
```

### 2.1 Belief Graph Operations:
1. **Perception $\to$ Attention**: Raw external signals are parsed into candidate beliefs. Attention scores these candidates to determine if they are worth the computational cost of attempting a graph insertion.
2. **Attention $\to$ Reasoning**: High-score candidate beliefs are pushed to Reasoning. Reasoning attempts to insert the belief into the graph, propagating logical constraints and detecting contradictions against existing beliefs (Truth Maintenance).
3. **Reasoning $\leftrightarrow$ Memory**: Memory is the persistence state of the Belief Graph. Reasoning retrieves related subgraph structures to evaluate the truth of incoming candidates.
4. **Identity $\to$ Reasoning**: Identity beliefs are invariant root nodes with $0.0$ decay. If a candidate belief contradicts an Identity belief, it is immediately rejected.
5. **Reasoning $\to$ Prediction**: The updated graph generates predictions about future states. High-surprise outcomes (prediction errors) dynamically lower the Attention thresholds to ingest more data.
6. **Planning $\to$ Action**: Planning generates hypothetical future subgraphs (plans) and selects the one that maximizes utility without violating Identity constraints. Action executes it.
7. **Consolidation & Learning (Sleep)**: During low-activity periods, the system sweeps the Belief Graph. It applies exponential decay to unreferenced episodic beliefs (Forgetting) and strengthens the weights of verified structural beliefs (Learning).

---

## 3. Perception: The Gateway

Perception is responsible for observing the workspace environment and converting unstructured noise into structured candidate Beliefs.

### 3.1 Candidate Belief Schema
Instead of raw "events" or "messages", Perception produces candidate beliefs for the Attention module:

```json
{
  "belief_id": "uuid",
  "timestamp": 1781360653.932,
  "source": {
    "entity_id": "alice_founder",
    "authority_weight": 0.95
  },
  "semantic_triple": {
    "subject": "production database",
    "predicate": "is",
    "object": "unresponsive"
  },
  "initial_confidence": 0.90
}
```

### 3.2 Epistemic Uncertainty
Perception does not assume absolute truth. It models uncertainty at the boundary:
* **Confidence Priors ($c \in [0.1, 1.0]$)**: Direct sensor streams (like `git` commits) carry high confidence. Human chat transcripts carry lower initial confidence.
* **Entropy Flags**: When semantic parsing is ambiguous, the candidate belief is flagged, prompting Reasoning to ask clarifying questions before committing the belief to the graph.
