import time
from attention_engine import AttentionEngine, PerceivedEvent, IdentityVector
from reasoning_engine import ReasoningEngine, SemanticClaim, ResolveConflict

def run_crucible():
    print("=========================================================")
    print("COGNITIVE OS: CRUCIBLE TEST (REDIS VS. VALKEY)")
    print("=========================================================")
    
    # 1. Initialize Engines
    attention = AttentionEngine()
    # Mocking the active identity for this test
    attention.active_identity = IdentityVector(mission="Maintain Q3 stability. Build reliable infrastructure.")
    reasoning = ReasoningEngine()

    print("\n--- STEP 1: PERCEPTION & ATTENTION ---")
    
    # Event 1: A trivial chatter event
    event_trivial = PerceivedEvent(
        id="evt_01",
        source="slack",
        payload="Did anyone order lunch?",
        timestamp=time.time(),
        entities=[],
        structural_verbs=[]
    )
    score_trivial = attention.process(event_trivial)
    print(f"[Attention] Event: '{event_trivial.payload}'")
    print(f"  -> Score: {score_trivial.total_score:.2f} | Routes: {score_trivial.routes}")

    # Event 2: Alice's High-Stakes Proposal
    event_alice = PerceivedEvent(
        id="evt_02",
        source="slack",
        payload="We need to switch from Redis to Valkey. Redis licensing changes are too risky.",
        timestamp=time.time(),
        entities=["Redis", "Valkey", "licensing"],
        structural_verbs=["switch", "migrate"]
    )
    score_alice = attention.process(event_alice)
    print(f"\n[Attention] Event: '{event_alice.payload}'")
    print(f"  -> Entropy Weight: {score_alice.entropy_val}")
    print(f"  -> Score: {score_alice.total_score:.2f} | Routes: {score_alice.routes}")

    print("\n--- STEP 2: UNDERSTANDING & REASONING (TMS) ---")
    print("Simulating Understanding Engine parsing Alice's proposal into a SemanticClaim...")
    
    # Alice's Claim
    claim_A = SemanticClaim(
        id="claim_alice_valkey",
        subject="System Architecture",
        predicate="migrate_to",
        object="Valkey",
        author_id="alice_founder",
        timestamp=time.time() - 100, # Older (Precedent)
        confidence=0.90,
        status="ACTIVE"
    )
    reasoning.add_claim(claim_A)
    print(f"[TMS] Logged Claim A: {claim_A.subject} {claim_A.predicate} {claim_A.object} (Conf: {claim_A.confidence})")

    # Bob's Claim (Counter-proposal)
    print("\nBob objects to the migration.")
    claim_B = SemanticClaim(
        id="claim_bob_redis",
        subject="System Architecture",
        predicate="retain",
        object="Redis",
        author_id="bob_founder",
        timestamp=time.time(), # Newer
        confidence=0.90,
        status="ACTIVE"
    )
    reasoning.add_claim(claim_B)
    print(f"[TMS] Logged Claim B: {claim_B.subject} {claim_B.predicate} {claim_B.object} (Conf: {claim_B.confidence})")

    print("\n--- STEP 3: CONFLICT RESOLUTION ---")
    print("Conflict detected! Confidence scores are identical (0.90 vs 0.90).")
    print("Triggering 4-Level ResolveConflict Algorithm...")
    
    result = ResolveConflict(claim_A, claim_B)
    reasoning.apply_resolution(result)

    print("\n=========================================================")
    print("CRUCIBLE TEST COMPLETE")
    print("=========================================================")

if __name__ == "__main__":
    run_crucible()
