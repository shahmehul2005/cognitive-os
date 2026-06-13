# Module: Attention Allocation & Routing Filters

Attention is the primary gatekeeper of the Cognitive Operating System. The moat of this architecture is not its ability to store everything, but its ability to aggressively filter $99.2\%$ of noise so that the remaining $0.8\%$ of high-utility strategic signals can be processed efficiently.

This document steps down from theoretical math into the brutal algorithmic specificity required for implementation.

---

## 1. The Core Attention Algorithm

When a raw signal arrives, the Attention Engine must assign it a dynamic score and route it in sub-milliseconds.

### 1.1 Data Structures
```python
@dataclass
class PerceivedEvent:
    id: str
    source: str # e.g., "slack", "github", "jira"
    payload: str
    timestamp: float
    entities: List[str]
    structural_verbs: List[str] # e.g., ["migrate", "deprecate", "hire"]

@dataclass
class AttentionScore:
    total_score: float
    recency_val: float
    entropy_val: float
    identity_val: float
    routes: List[str] # e.g., ["ShouldRemember", "ShouldReason"]
```

### 1.2 Executable Pseudocode
```python
def CalculateAttentionScore(event: PerceivedEvent, active_identity: IdentityVector) -> AttentionScore:
    # 1. Recency (Decays over time, but for a new event, it is 1.0)
    time_delta_hours = (current_time() - event.timestamp) / 3600
    recency_val = math.exp(-0.1 * time_delta_hours) 
    
    # 2. Entropy / Structural Weight (How much does this change the world?)
    # Routine chatter has low entropy. Structural verbs have high entropy.
    structural_weight = 0.0
    if any(verb in event.structural_verbs for verb in ["migrate", "deprecate", "launch", "fail"]):
        structural_weight = 0.85
    elif any(verb in event.structural_verbs for verb in ["fix", "update", "meeting"]):
        structural_weight = 0.30
    
    # 3. Identity Alignment (Does this relate to our core goals?)
    # Vector cosine similarity between the event text and the active strategy manifesto
    event_embedding = get_embedding(event.payload)
    identity_val = cosine_similarity(event_embedding, active_identity.embedding)
    
    # 4. Final Calculation
    # Weights: w_r = 0.2, w_e = 0.5, w_i = 0.3
    total = (0.2 * recency_val) + (0.5 * structural_weight) + (0.3 * identity_val)
    
    # 5. Routing Gates
    routes = []
    if total > 0.70:
        routes.append("ShouldReason")
    if total > 0.40 or "fact" in event.entities:
        routes.append("ShouldRemember")
        
    return AttentionScore(total, recency_val, structural_weight, identity_val, routes)
```

---

## 2. Attention Failure Modes & Recoveries

Algorithms fail. The Cognitive OS explicitly defines how to recover when the Attention Engine hallucinates or drops the ball.

### 2.1 Failure Mode 1: False Negative (The "Dropped Ball")
**Scenario**: A critical bug is reported in a Slack thread. The payload lacks structural verbs (the user just says "it broke again"), so `structural_weight` is $0.1$. The `total_score` evaluates to $0.35$. The system drops it. The engineers never see it.
**Recovery Mechanism**: The `Resonance Check`.
- If an event is dropped, but its embedding is highly similar to $N$ other dropped events within a 24-hour window, the `ConsolidationDaemon` aggregates them.
- *Pseudocode Rule*: `if count(dropped_events where similarity(e1, e2) > 0.9) > 3 then force_route(aggregated_event, "ShouldReason")`

### 2.2 Failure Mode 2: False Positive (The "Panic Attack")
**Scenario**: The CEO uses the word "migrate" metaphorically ("We need to migrate our thinking"). `structural_weight` spikes to $0.85$. The system panics, routes it to `ShouldReason`, and tries to generate a database migration plan.
**Recovery Mechanism**: The `Reasoning Reality Check`.
- Attention is just a gate. It passes the event to the Truth Maintenance System (Reasoning). 
- The Reasoning engine attempts to extract the `(Subject, Predicate, Object)` triple. It extracts `(Thinking, migrate, None)`. 
- Because the object does not map to a known infrastructure node in the ontology, Reasoning flags it as `Metaphorical/Invalid` and safely degrades the event to episodic memory without triggering an alert.

---

## 3. The Pruning Algorithm (Forgetting)

Attention is not just about what comes in; it's about actively destroying what is no longer needed.

```python
def PruneMemoryNetwork(memory_graph: Graph):
    for node in memory_graph.get_all_nodes():
        # Activation Energy Calculation
        # Time since last retrieval + Number of inbound links
        days_since_read = (current_time() - node.last_retrieved) / 86400
        link_weight = len(node.inbound_edges) * 0.1
        
        activation_energy = (1.0 / (days_since_read + 1)) + link_weight
        
        # Hard limits
        if node.type == "IdentityConstraint":
            continue # Never prune core constraints
            
        if activation_energy < 0.05:
            # Delete from active VRAM/Vector DB
            de_index(node)
            # Write to cold storage for compliance only
            archive_to_cold_storage(node)
```
