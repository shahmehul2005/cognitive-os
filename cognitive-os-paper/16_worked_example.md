# Stage 16: The Worked Example (Instantiating the Cycle)

To bridge the ambition-to-clarity gap, we trace a single, high-stakes scenario through every module of the Cognitive OS, down to the specific data structures and algorithmic decisions.

**The Scenario**: Founder A and Founder B are discussing a backend database pivot in Slack.
- **Founder A (Alice)**: "We need to switch from Redis to Valkey. Redis licensing changes are too risky."
- **Founder B (Bob)**: "I disagree. A migration right now violates our Q3 Stability constraint. Valkey isn't battle-tested enough."

Here is how the Cognitive Organism processes this event.

---

## 1. Perception
The `SlackSensor` daemon captures the raw text and normalizes it into standard `PerceivedEvent` payloads.

```json
{
  "event_id": "evt_slack_093a",
  "source": "slack_channel_architecture",
  "author_id": "alice_founder",
  "timestamp": 1781368000,
  "raw_content": "We need to switch from Redis to Valkey. Redis licensing changes are too risky.",
  "extracted_entities": ["Redis", "Valkey", "licensing"]
}
```

---

## 2. Attention
The `AttentionEngine` evaluates this payload against the noise floor. It runs `CalculateAttentionScore(evt)`.

1. **Recency**: Score is high ($1.0$), it just happened.
2. **Uncertainty (Entropy)**: The payload proposes a fundamental infrastructure change. It contains high-entropy structural verbs ("switch from X to Y"). Entropy Score: $0.85$.
3. **Identity Alignment**: Does this map to known strategic vectors? Yes, it mentions "licensing" and "infrastructure", mapping to the Active Strategy. Score: $0.90$.

*Total Attention Score*: $0.92$ (Threshold is $0.70$).
*Routing Action*: `ShouldRemember(True)` and `ShouldCreateDecision(True)`. 
The event is elevated from raw text into the active working memory for Reasoning.

---

## 3. Understanding
The `UnderstandingEngine` converts the natural language into formal ontological triples.
- Resolves "We" $\to$ "System Architecture".
- Generates Claim 1: `(System Architecture, migrate_to, Valkey)` (Proposed by Alice).
- Generates Claim 2: `(Redis, status, high_risk)` (Proposed by Alice).

A minute later, Perception catches Bob's reply. Understanding parses Bob's reply:
- Generates Claim 3: `(System Architecture, migrate_to, Valkey)` $\to$ `status: Refuted` (Proposed by Bob).
- Identifies the justification: `(Valkey, attribute, unproven)`.

---

## 4. Memory Retrieval & Identity Constraint Check
Before the Reasoning Engine processes this conflict, it fetches relevant context.

**Retrieval Query**: `Search(tags=["Redis", "Valkey", "infrastructure_strategy"])`
- *Semantic Memory Returns*: "Current primary datastore is Redis (Confidence: 0.99)."
- *Identity Module Returns Constraint*: `CONSTRAINT_Q3_01: "No core infrastructure migrations during Q3 product launch to ensure stability."`

---

## 5. Reasoning Engine (TMS) & Conflict Resolution
The Truth Maintenance System (TMS) now has two conflicting claims of identical systemic weight:
- **Claim A**: Migrate to Valkey (Author: Alice, Role: Founder, Confidence: 0.90).
- **Claim B**: Do not migrate to Valkey (Author: Bob, Role: Founder, Confidence: 0.90).

**The Brutal Algorithm execution (`ResolveConflict`):**
1. **Confidence Delta**: $|0.90 - 0.90| = 0.0$. Neither wins on raw evidence weight.
2. **Identity Constraint Check**: Does either claim violate a hard identity boundary?
   - Claim A (Migrate) *violates* `CONSTRAINT_Q3_01` (No core infra migrations).
   - Claim B (Do not migrate) *aligns* with `CONSTRAINT_Q3_01`.
3. **Resolution**: The Reasoning Engine sides with Claim B.

**TMS Update**:
- Claim A status $\to$ `Superceded (Violates Identity Constraint)`.
- Claim B status $\to$ `Active / Verified`.

*System Action*: The system automatically posts a summary back to Slack:
*"I have logged the proposal to switch to Valkey. However, based on the Q3 Stability Constraint established last month, this migration has been flagged as blocked. Do you wish to override the Q3 Identity constraint?"*

---

## 6. Learning & Consolidation (The Sleep Phase)
At 2:00 AM, the `ConsolidationDaemon` wakes up to clean the day's episodic logs.

1. **Pruning**: It deletes the raw Slack formatting and timestamps, keeping only the semantic facts.
2. **Abstraction**: It compresses the conversation into a `DecisionMemory` node:
```json
{
  "node_id": "dec_valkey_vs_redis_q3",
  "type": "Decision",
  "summary": "Proposal to migrate from Redis to Valkey was rejected.",
  "rationale": "Violated Q3 Stability Identity Constraint. Redis licensing risks accepted temporarily.",
  "authors": ["alice", "bob"],
  "expiration": 1790000000 // End of Q3, when this should be re-evaluated
}
```
3. **Future State**: Six months from now, if a new engineer asks, "Why are we still paying for Redis?", the system will immediately pull `dec_valkey_vs_redis_q3` and explain the exact structural reason, without anyone needing to search through 10,000 Slack messages.
