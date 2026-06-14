import time
import re
from dataclasses import dataclass
from typing import Optional, List
from collections import defaultdict

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
    action: str # "Auto-Resolve", "Escalate_To_Human", "UNRESOLVED"

# --- NLP Extraction (Strategy B: Heuristics) ---
def _extract_triple_heuristic(text: str) -> tuple:
    text = text.strip().rstrip('.')

    # Pattern 1: "X is/are/was Y"
    m = re.match(
        r'^(?:our|the|a|an)?\s*([a-zA-Z\s]{2,30}?)\s+'
        r'(is|are|was|were|has been|will be)\s+(.+)$',
        text, re.IGNORECASE
    )
    if m:
        return (
            m.group(1).strip().lower(),
            m.group(2).strip().lower(),
            m.group(3).strip().lower()
        )

    # Pattern 2: "X verb(ed) Y"
    m = re.match(
        r'^(?:our|the|a|an)?\s*([a-zA-Z\s]{2,20}?)\s+'
        r'([a-z]+(?:ed|s|ing)?)\s+(.+)$',
        text, re.IGNORECASE
    )
    if m:
        return (
            m.group(1).strip().lower(),
            m.group(2).strip().lower(),
            m.group(3).strip().lower()
        )

    words = text.lower().split()
    if len(words) >= 3:
        return words[0], words[1], " ".join(words[2:])

    return "unknown", "relates_to", text.lower()

def extract_claim_triple(text: str) -> tuple:
    try:
        import spacy
        # Avoid loading overhead on every call if possible, but keep simple for MVP
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(text)

        subj, pred, obj = None, None, None
        for token in doc:
            if token.dep_ in ("nsubj", "nsubjpass") and subj is None:
                subj = token.lemma_.lower()
            if token.pos_ in ("VERB", "AUX") and pred is None:
                pred = token.lemma_.lower()
            if token.dep_ in ("dobj", "attr", "pobj", "acomp") and obj is None:
                obj = " ".join(t.text for t in token.subtree).lower()

        if subj and pred and obj:
            return subj, pred, obj
    except Exception:
        pass
        
    return _extract_triple_heuristic(text)

# --- Existing Identity & TMS Logic ---
IDENTITY_CONSTRAINTS = {
    "CONSTRAINT_Q3_01": "No core infrastructure migrations during Q3 product launch to ensure stability."
}

def CheckIdentityConstraints(claim: SemanticClaim) -> bool:
    if claim.predicate and "migrate" in claim.predicate and "valkey" in claim.object.lower():
        return True
    return False

def GetAuthorAuthorityWeight(author_id: str, domain: str) -> float:
    weights = {
        "alice_founder": 1.0,
        "bob_founder": 1.0,
        "junior_dev": 0.3
    }
    return weights.get(author_id, 0.5)

def CalculateStrategicImpact(claim: SemanticClaim) -> float:
    if claim.subject and "architecture" in claim.subject:
        return 0.9
    return 0.2

def ResolveConflict(claim_A: SemanticClaim, claim_B: SemanticClaim) -> ResolutionResult:
    delta = abs(claim_A.confidence - claim_B.confidence)
    if delta > 0.15:
        winner = claim_A if claim_A.confidence > claim_B.confidence else claim_B
        loser = claim_B if winner == claim_A else claim_A
        return ResolutionResult(winner=winner, loser=loser, reason="Evidence Weight", action="Auto-Resolve")

    a_violates = CheckIdentityConstraints(claim_A)
    b_violates = CheckIdentityConstraints(claim_B)
    
    if a_violates and not b_violates:
        return ResolutionResult(winner=claim_B, loser=claim_A, reason="Identity Violation (Claim A)", action="Auto-Resolve")
    if b_violates and not a_violates:
        return ResolutionResult(winner=claim_A, loser=claim_B, reason="Identity Violation (Claim B)", action="Auto-Resolve")

    impact = max(CalculateStrategicImpact(claim_A), CalculateStrategicImpact(claim_B))
    if impact > 0.8:
        return ResolutionResult(winner=None, loser=None, reason="High-Impact Structural Tie", action="Escalate_To_Human")

    weight_a = GetAuthorAuthorityWeight(claim_A.author_id, domain=claim_A.subject)
    weight_b = GetAuthorAuthorityWeight(claim_B.author_id, domain=claim_B.subject)
    
    if weight_a > weight_b:
        return ResolutionResult(winner=claim_A, loser=claim_B, reason="Author Domain Authority", action="Auto-Resolve")
    if weight_b > weight_a:
        return ResolutionResult(winner=claim_B, loser=claim_A, reason="Author Domain Authority", action="Auto-Resolve")

    if delta < 0.10:
        return ResolutionResult(winner=None, loser=None, reason="Equal Authority Tie", action="UNRESOLVED")

    if claim_A.timestamp < claim_B.timestamp:
        return ResolutionResult(winner=claim_B, loser=claim_A, reason="Newer Overrides Older", action="Auto-Resolve")
    else:
        return ResolutionResult(winner=claim_A, loser=claim_B, reason="Newer Overrides Older", action="Auto-Resolve")

class ReasoningEngine:
    def __init__(self):
        # We no longer store self.tms_graph in volatile memory.
        # We query the SQLite DB instead.
        from memory_engine import BeliefStore
        BeliefStore.init_db()
        self.contradictions = []
        self.unresolved = []
        
    def add_claim(self, claim: SemanticClaim):
        from memory_engine import BeliefStore
        
        # Native Contradiction Detection
        key_sub = getattr(claim, 'subject',   'unknown').lower().strip()
        key_pred = getattr(claim, 'predicate', 'unknown').lower().strip()
        obj_new = getattr(claim, 'object', '').lower().strip()

        # Query existing beliefs from DB instead of volatile dict
        existing_beliefs_data = BeliefStore.query_beliefs_by_key(key_sub, key_pred)
        
        for e_data in existing_beliefs_data:
            if e_data['status'] != 'ACTIVE':
                continue
                
            obj_old = e_data['object'].lower().strip() if e_data['object'] else ''
            
            if obj_new != obj_old:
                # Reconstruct SemanticClaim from DB dict
                existing = SemanticClaim(
                    id=e_data['id'],
                    subject=e_data['subject'],
                    predicate=e_data['predicate'],
                    object=e_data['object'],
                    author_id=e_data['author_id'],
                    timestamp=e_data['timestamp'],
                    confidence=e_data['confidence'],
                    status=e_data['status']
                )
                
                res = ResolveConflict(existing, claim)
                self.contradictions.append({
                    'claim_a': existing,
                    'claim_b': claim,
                    'resolution': res.action
                })
                
                if res.action == "Auto-Resolve":
                    self.apply_resolution(res)
                else:
                    self.unresolved.append({'claim_a': existing, 'claim_b': claim})
                    print(f"  [TMS] CONTRADICTION UNRESOLVED: '{key_sub}' {key_pred} '{obj_old}' vs '{obj_new}'")
                    
        # Insert the new claim as a Belief into the DB
        # Determine decay rate. Structural/Identity claims decay slower (e.g., 0.01) vs episodic (0.07)
        decay_rate = 0.01 if "architecture" in key_sub else 0.07
        
        BeliefStore.insert_belief(
            belief_id=claim.id,
            subject=key_sub,
            predicate=key_pred,
            object_val=getattr(claim, 'object', ''),
            payload="", # Abstracted
            confidence=claim.confidence,
            decay_rate=decay_rate,
            timestamp=claim.timestamp,
            status=claim.status,
            author_id=claim.author_id
        )
        
    def get_confidence(self, claim: SemanticClaim, now: float = None) -> float:
        import math
        if now is None:
            now = time.time()
        days = (now - claim.timestamp) / 86400.0
        # If we had DB access here, we'd query decay_rate. For now, default to 0.07 if not specified.
        # But this function is usually used locally.
        return claim.confidence * math.exp(-0.07 * days)
        
    def apply_resolution(self, result: ResolutionResult):
        from memory_engine import BeliefStore
        
        if result.action == "Auto-Resolve":
            # Update winner to ACTIVE (if it isn't already)
            BeliefStore.update_belief_status(result.winner.id, "ACTIVE")
            
            # Update loser to SUPERCEDED
            BeliefStore.update_belief_status(result.loser.id, "SUPERCEDED")
            
            # Record the graph edge
            BeliefStore.insert_edge(source_id=result.loser.id, target_id=result.winner.id, relation_type="SUPERCEDED_BY")
            
            print(f"TMS ACTION: Auto-Resolved Conflict.")
            print(f"  WINNER: {result.winner.id} [ACTIVE]")
            print(f"  LOSER:  {result.loser.id} [SUPERCEDED]")
            print(f"  REASON: {result.reason}")
        elif result.action == "Escalate_To_Human":
            print(f"TMS ACTION: ESCALATED TO HUMAN.")
            print(f"  REASON: {result.reason}")
