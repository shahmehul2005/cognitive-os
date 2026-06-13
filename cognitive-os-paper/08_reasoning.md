# Module: Reasoning & The Truth Maintenance System

The Reasoning Engine is the recurrent central processor of the Cognitive Operating System. If Attention decides *what* the system looks at, Reasoning decides *what is true*. 

This document moves past abstract logic and defines the brutal algorithmic specificity required for the Truth Maintenance System (TMS) to resolve conflicts autonomously without human intervention.

---

## 1. The Core Problem: Contradiction

When two agents (or humans) assert conflicting facts, flat databases simply overwrite the old fact with the new one. This causes Organizational Amnesia. The Cognitive OS explicitly models contradictions.

```python
@dataclass
class SemanticClaim:
    id: str
    subject: str
    predicate: str
    object: str
    author_id: str
    timestamp: float
    confidence: float
    status: str # "ACTIVE", "SUPERCEDED", "REFUTED", "PENDING"
```

If Claim A asserts `(Database, is, Redis)` and Claim B asserts `(Database, is, Valkey)`, the system detects a structural contradiction.

---

## 2. Deep Conflict Resolution: The Algorithm

The user asked the hardest question: **"What happens when two beliefs have identical confidence?"**

We cannot rely on simple math (e.g., $0.90$ vs $0.90$). The system executes a strict, deterministic resolution hierarchy.

### 2.1 The Execution Hierarchy

```python
def ResolveConflict(claim_A: SemanticClaim, claim_B: SemanticClaim) -> ResolutionResult:
    # Level 1: Pure Evidence Weight (Confidence Delta)
    # If one claim has significantly more evidentiary support, it wins immediately.
    delta = abs(claim_A.confidence - claim_B.confidence)
    if delta > 0.15:
        winner = claim_A if claim_A.confidence > claim_B.confidence else claim_B
        loser = claim_B if winner == claim_A else claim_A
        return ResolutionResult(winner=winner, loser=loser, reason="Evidence Weight", action="Auto-Resolve")

    # If confidence is tied, we move to structural constraints.

    # Level 2: The Identity Constraint Check
    # The Identity module holds the absolute boundaries of the organization.
    a_violates = CheckIdentityConstraints(claim_A)
    b_violates = CheckIdentityConstraints(claim_B)
    
    if a_violates and not b_violates:
        return ResolutionResult(winner=claim_B, loser=claim_A, reason="Identity Violation (A)", action="Auto-Resolve")
    if b_violates and not a_violates:
        return ResolutionResult(winner=claim_A, loser=claim_B, reason="Identity Violation (B)", action="Auto-Resolve")
        
    # If neither violates identity (or both do), we move to Authority.

    # Level 3: Organizational Authority (Role Weight)
    # The system tracks the hierarchical or domain-specific authority of the authors.
    # A VP of Eng overrides a Jr. Dev on infrastructure claims.
    weight_a = GetAuthorAuthorityWeight(claim_A.author_id, domain=claim_A.subject)
    weight_b = GetAuthorAuthorityWeight(claim_B.author_id, domain=claim_B.subject)
    
    if weight_a > weight_b:
        return ResolutionResult(winner=claim_A, loser=claim_B, reason="Author Domain Authority", action="Auto-Resolve")
    if weight_b > weight_a:
        return ResolutionResult(winner=claim_B, loser=claim_A, reason="Author Domain Authority", action="Auto-Resolve")

    # If authority is identical (e.g., two co-founders disagree), we move to Precedent.

    # Level 4: Historical Precedent (Status Quo Bias)
    # If everything else is tied, the system favors the existing architecture to prevent thrashing.
    if claim_A.timestamp < claim_B.timestamp:
        # A is older, meaning it is the incumbent.
        return ResolutionResult(winner=claim_A, loser=claim_B, reason="Status Quo Precedent", action="Auto-Resolve")
    else:
        return ResolutionResult(winner=claim_B, loser=claim_A, reason="Status Quo Precedent", action="Auto-Resolve")
```

### 2.2 The Final Fallback: Escalation
If the system detects that the conflict is both structurally tied *and* carries a massive risk payload (e.g., it impacts >30% of the active roadmap), it aborts Level 4 and triggers an escalation.

```python
    # Inserted before Level 4
    if CalculateStrategicImpact(claim_A) > 0.8:
        return ResolutionResult(
            winner=None, 
            loser=None, 
            reason="High-Impact Structural Tie", 
            action="Escalate_To_Human"
        )
```

---

## 3. Applying the Result (The TMS Update)

When `ResolveConflict` returns an `Auto-Resolve` action, the Truth Maintenance System updates the graph state. It does not delete the loser.

```python
def ApplyResolution(result: ResolutionResult):
    # 1. Update the loser's state to ensure it is not used in active planning
    result.loser.status = "SUPERCEDED"
    
    # 2. Draw a causal edge in the graph for auditability
    create_edge(source=result.loser.id, target=result.winner.id, relation="SUPERCEDED_BY")
    
    # 3. Log the algorithmic rationale to Decision Memory
    log_decision(
        subject=f"Conflict Resolution: {result.winner.subject}",
        winner=result.winner,
        loser=result.loser,
        rationale=result.reason
    )
```

By persisting the `SUPERCEDED` claim and the causal edge, the organism never suffers from Amnesia. If Founder A asks a year later, *"Why didn't we switch to Valkey?"*, the system traverses the edge backwards and outputs: *"The claim was superceded due to an Identity Violation (Q3 Stability Constraint)."*
