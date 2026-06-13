import time
from dataclasses import dataclass
from typing import Optional, List

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

@dataclass
class ResolutionResult:
    winner: Optional[SemanticClaim]
    loser: Optional[SemanticClaim]
    reason: str
    action: str # "Auto-Resolve", "Escalate_To_Human"

# Mock Identity Constraints for the Crucible Test
IDENTITY_CONSTRAINTS = {
    "CONSTRAINT_Q3_01": "No core infrastructure migrations during Q3 product launch to ensure stability."
}

def CheckIdentityConstraints(claim: SemanticClaim) -> bool:
    """
    Returns True if the claim violates a hard identity constraint.
    Mock implementation for the Redis/Valkey scenario.
    """
    if "migrate_to" in claim.predicate and "Valkey" in claim.object:
        # Alice's claim violates the Q3 No Migration Constraint
        return True
    return False

def GetAuthorAuthorityWeight(author_id: str, domain: str) -> float:
    """
    Returns the organizational weight of the author in the given domain.
    Founders have equal weight in this test scenario.
    """
    weights = {
        "alice_founder": 1.0,
        "bob_founder": 1.0,
        "junior_dev": 0.3
    }
    return weights.get(author_id, 0.5)

def CalculateStrategicImpact(claim: SemanticClaim) -> float:
    """
    Calculates the blast radius of this claim.
    A database pivot is a high impact change.
    """
    if claim.subject == "System Architecture":
        return 0.9
    return 0.2

def ResolveConflict(claim_A: SemanticClaim, claim_B: SemanticClaim) -> ResolutionResult:
    """
    The brutal 4-level Truth Maintenance System conflict resolution algorithm.
    """
    # Level 1: Pure Evidence Weight (Confidence Delta)
    delta = abs(claim_A.confidence - claim_B.confidence)
    if delta > 0.15:
        winner = claim_A if claim_A.confidence > claim_B.confidence else claim_B
        loser = claim_B if winner == claim_A else claim_A
        return ResolutionResult(winner=winner, loser=loser, reason="Evidence Weight", action="Auto-Resolve")

    # Level 2: The Identity Constraint Check
    a_violates = CheckIdentityConstraints(claim_A)
    b_violates = CheckIdentityConstraints(claim_B)
    
    if a_violates and not b_violates:
        return ResolutionResult(winner=claim_B, loser=claim_A, reason="Identity Violation (Claim A)", action="Auto-Resolve")
    if b_violates and not a_violates:
        return ResolutionResult(winner=claim_A, loser=claim_B, reason="Identity Violation (Claim B)", action="Auto-Resolve")

    # High-Impact Escalation Check before moving to arbitrary tie-breakers
    impact = max(CalculateStrategicImpact(claim_A), CalculateStrategicImpact(claim_B))
    if impact > 0.8:
        return ResolutionResult(winner=None, loser=None, reason="High-Impact Structural Tie", action="Escalate_To_Human")

    # Level 3: Organizational Authority (Role Weight)
    weight_a = GetAuthorAuthorityWeight(claim_A.author_id, domain=claim_A.subject)
    weight_b = GetAuthorAuthorityWeight(claim_B.author_id, domain=claim_B.subject)
    
    if weight_a > weight_b:
        return ResolutionResult(winner=claim_A, loser=claim_B, reason="Author Domain Authority", action="Auto-Resolve")
    if weight_b > weight_a:
        return ResolutionResult(winner=claim_B, loser=claim_A, reason="Author Domain Authority", action="Auto-Resolve")

    # Level 4: Historical Precedent (Status Quo Bias)
    if claim_A.timestamp < claim_B.timestamp:
        return ResolutionResult(winner=claim_A, loser=claim_B, reason="Status Quo Precedent", action="Auto-Resolve")
    else:
        return ResolutionResult(winner=claim_B, loser=claim_A, reason="Status Quo Precedent", action="Auto-Resolve")

class ReasoningEngine:
    def __init__(self):
        self.tms_graph = []
        self.edges = []
        
    def add_claim(self, claim: SemanticClaim):
        self.tms_graph.append(claim)
        
    def apply_resolution(self, result: ResolutionResult):
        if result.action == "Auto-Resolve":
            # 1. Update loser state
            result.loser.status = "SUPERCEDED"
            # 2. Draw causal edge
            self.edges.append({"source": result.loser.id, "target": result.winner.id, "relation": "SUPERCEDED_BY"})
            # 3. Output decision rationale
            print(f"TMS ACTION: Auto-Resolved Conflict.")
            print(f"  WINNER: {result.winner.id} [{result.winner.status}]")
            print(f"  LOSER:  {result.loser.id} [{result.loser.status}]")
            print(f"  REASON: {result.reason}")
        elif result.action == "Escalate_To_Human":
            print(f"TMS ACTION: ESCALATED TO HUMAN.")
            print(f"  REASON: {result.reason}")
