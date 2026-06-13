# Module: Learning & Consolidation (The Sleep Phase)

Collective intelligence improves when a system can reflect on past actions, synthesize experience, and adapt its internal rules. The Cognitive Operating System implements an offline, recurring **Sleep Phase** to organize its knowledge, compress memory, and adjust strategic parameters.

---

## 1. First-Principles Purpose
Learning exists because real-time execution is noisy and focused on immediate task completion. While executing tasks, agents cannot perform deep cross-context reviews, build ontological abstractions, or prune decayed logic without suffering latency penalties. The Sleep Phase serves to decouple immediate action from long-term memory optimization—allowing the workspace to consolidate raw logs, evaluate prediction deviations, and run truth validation when the system is offline.

---

## 2. The Consolidation Hierarchy

Consolidation runs in a nested cascade at scheduled intervals:

```
                              Daily Consolidation Loop (Every 24h)
                                              │
                                              ▼
                              Weekly Consolidation Loop (Every 7d)
                                              │
                                              ▼
                             Monthly Consolidation Loop (Every 30d)
```

* **Daily Loop**: Focuses on raw episodic dialogues and sensory logs from the past 24 hours. It extracts semantic candidate facts and decays temporary records.
* **Weekly Loop**: Focuses on daily candidates. It resolves contradictions between new facts and legacy knowledge using the Truth Maintenance System, and updates failure heuristics based on task outcomes.
* **Monthly Loop**: Evaluates actor relationship scores, updates global ontology mappings based on strategic updates, and offloads old decisions to historical archives.

---

## 3. Cognitive Algorithms

We define the core learning operations using abstract, implementation-free system commands:

### 3.1 Forget()
Prunes decayed active indexes and archives raw logs to compliance storage.
* **Inputs**:
  - `decay_threshold`: Cutoff value $\tau_{\text{forget}}$.
* **Output**:
  - `pruned_count`: Number of de-indexed memory traces.

```python
def Forget(decay_threshold):
    decayable_nodes = MemoryStore.query_active_decayable_nodes()
    pruned_count = 0
    
    for node in decayable_nodes:
        energy = RankImportance(node)
        
        if energy < decay_threshold:
            # Attempt to extract semantic facts before erasing raw episodic logs
            if node.type == "Episodic" and HasUnconsolidatedFacts(node):
                Compress([node])
                
            # 1. Archive raw payload to compliance cold storage for audit checks
            ComplianceStorage.write(node.id, node.type, node.payload)
            
            # 2. De-index from the active associative network
            MemoryStore.de_index_node(node.id)
            pruned_count += 1
            
    return pruned_count
```

### 3.2 Compress()
Abstracts specific episodic records into reusable semantic facts.
* **Inputs**:
  - `episodic_nodes`: List of raw conversation/commit logs.
* **Output**:
  - `semantic_facts`: New fact triples registered in memory.

```python
def Compress(episodic_nodes):
    semantic_facts = []
    source_texts = [n.content for n in episodic_nodes]
    
    # Call abstract fact extractor interface
    extracted_claims = FactExtractor.parse(source_texts)
    
    for claim in extracted_claims:
        # Check for duplication or contradictions in active Semantic network
        existing_nodes = MemoryStore.query_semantic_relation(claim.subject, claim.predicate, claim.object)
        
        if not existing_nodes:
            node_id = Remember(
                content={"subject": claim.subject, "predicate": claim.predicate, "object": claim.object},
                memory_type="Semantic",
                confidence_score=0.8,
                provenance_id=episodic_nodes[0].id
            )
            semantic_facts.append(claim)
            
    return semantic_facts
```

### 3.3 Consolidate()
Orchestrates the offline consolidation cycle ("Sleep Phase").
* **Inputs**:
  - None.
* **Output**:
  - `success`: Execution status.

```python
def Consolidate():
    # 1. Fetch unconsolidated episodic logs
    raw_episodes = MemoryStore.query_unconsolidated_episodic()
    
    # 2. Extract facts and build semantic abstractions
    if raw_episodes:
        Compress(raw_episodes)
        
    # 3. Clean active space by running forgetting decay
    pruned = Forget(decay_threshold=0.15)
    
    # 4. Trigger strategic audits on schedules
    if IsWeeklyInterval():
        RunWeeklyConsolidation()
    if IsMonthlyInterval():
        RunMonthlyConsolidation()
        
    # Mark episodes as consolidated
    MemoryStore.flag_consolidated(raw_episodes)
    return True
```

---

## 4. Evaluation Protocols
Learning efficiency is evaluated during the monthly audits against three invariants:

* **Repeated Discussion Index ($I_{\text{repeat}}$)**: Ratio of repeated conversations to total team interactions. Target: $I_{\text{repeat}} < 5\%$.
* **Compression Ratio ($CR_{\text{cons}}$)**: Size of raw logs divided by size of consolidated facts. Target: $CR_{\text{cons}} \ge 10\text{x}$.
* **Information Preservation ($R_{\text{pres}}$)**: Percentage of critical choices preserved after compression. Target: $R_{\text{pres}} \ge 98\%$.
