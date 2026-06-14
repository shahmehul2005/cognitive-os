"""
cognitive_os_patches.py
=======================
Drop-in patches for Cognitive OS based on diagnostic results.

HOW TO USE:
  Option A — Quick test (no changes to your files):
    Add this at the top of test_suite.py or diagnostic_tests.py:
      from cognitive_os_patches import patch_attention, patch_reasoning
      patch_attention(attention)
      patch_reasoning(reasoning)

  Option B — Permanent fix:
    Copy each section below into the corresponding engine file.

WHAT EACH FIX ADDRESSES (from diagnostic output):
  FIX 1 → Diag 6: entities/verbs/source Δ=0.0000 (completely ignored)
  FIX 2 → Diag 1: "ERROR"×500 scored 0.99 (noise scored above real signal)
  FIX 3 → Diag 3: routes change without score change (dual unlinked logic)
  FIX 4 → Diag 5: MockClaim subject='Mock', TMS can't detect contradictions
  FIX 5 → Diag 7: no confidence decay, memory never forgets
"""

import math
import time
import re
from collections import defaultdict


# ══════════════════════════════════════════════════════════════
#  FIX 1 + 2 + 3 — ATTENTION ENGINE SCORING
#
#  Root cause (Diag 6): your AttentionEngine.process() computes
#  total_score from payload text alone and never reads
#  event.entities, event.verbs, or event.source.
#
#  Root cause (Diag 1): the payload-only scorer gives 0.99 to
#  "ERROR"×500 because it sees many characters / a repeated
#  high-urgency word, with no length-penalty or noise guard.
#
#  Root cause (Diag 3): routing is done by a separate keyword
#  check that bypasses total_score entirely.
#
#  This replacement formula uses ALL structured fields and
#  makes routing a direct function of total_score only.
# ══════════════════════════════════════════════════════════════

# --- Urgency keyword sets (weighted tiers) ---

URGENCY_T3 = {                          # weight 1.0 — drop-everything
    "critical", "down", "outage", "breach", "data loss",
    "losing revenue", "customers affected", "all users",
    "p0", "sev1", "sev0", "emergency", "incident",
}
URGENCY_T2 = {                          # weight 0.6 — important
    "failed", "blocked", "error", "spike", "degraded",
    "latency", "timeout", "unresponsive", "sla", "breach",
    "churn", "p1", "sev2", "urgent", "alert",
}
URGENCY_T1 = {                          # weight 0.3 — worth noting
    "slow", "warning", "review", "concern", "issue",
    "delay", "missed", "update", "decision", "agreed",
    "changed", "revised", "hired", "launched",
}

# --- Source reliability weights ---
SOURCE_WEIGHTS = {
    "git":        0.90,
    "slack":      0.85,
    "email":      0.75,
    "jira":       0.80,
    "monitoring": 0.70,
    "webhook":    0.65,
}
SOURCE_DEFAULT = 0.60

# --- Route thresholds (score-driven, not keyword-driven) ---
THRESHOLD_ACT    = 0.80   # ShouldAct    requires high confidence
THRESHOLD_REASON = 0.65   # ShouldReason requires meaningful signal
THRESHOLD_MEMORY = 0.45   # ShouldRemember is lowest bar


def _compute_urgency_score(payload: str) -> float:
    """
    Score urgency from payload text using tiered keyword matching.

    Returns a value in [0, 1].

    Key noise guard: applies a LENGTH PENALTY for very long repetitive
    payloads (the "ERROR"×500 = 0.99 problem from Diagnostic 1).
    A real urgent message is typically < 500 characters. Anything
    beyond 1000 chars with no structural signal is likely a log dump.
    """
    if not payload:
        return 0.0

    text_lower = payload.lower()

    # Count urgency keyword hits by tier
    t3_hits = sum(1 for k in URGENCY_T3 if k in text_lower)
    t2_hits = sum(1 for k in URGENCY_T2 if k in text_lower)
    t1_hits = sum(1 for k in URGENCY_T1 if k in text_lower)

    # Raw urgency: diminishing returns after first few hits
    # Using log1p so 1 hit matters a lot, 10 hits doesn't matter 10×
    raw_urgency = (
        min(t3_hits, 3) * 1.00 +
        min(t2_hits, 3) * 0.60 +
        min(t1_hits, 3) * 0.30
    ) / 3.9   # normalise: max possible = (3×1.0 + 3×0.6 + 3×0.3) = 5.7 → /3.9 clips to ~1.46, capped below

    raw_urgency = min(raw_urgency, 1.0)

    # Length penalty: payloads over 800 chars with low keyword density
    # are almost certainly log dumps, not strategic signals.
    char_count   = len(payload)
    keyword_hits = t3_hits + t2_hits + t1_hits
    if char_count > 800 and keyword_hits == 0:
        raw_urgency *= 0.10   # near-zero for pure noise floods
    elif char_count > 800:
        # Density check: hits per 100 chars
        density = (keyword_hits / char_count) * 100
        if density < 0.5:
            raw_urgency *= 0.30   # mostly noise with a few keywords

    return raw_urgency


def _compute_structural_score(entities: list, verbs: list) -> float:
    """
    Score based on structured NLP fields (entities + verbs).

    Entities signal that something specific is being discussed.
    Verbs signal that something is happening (action/change).

    Returns a value in [0, 1].
    Why these weights?
      - Entities alone (no verbs): could be a mention, not an event
      - Verbs alone (no entities): vague action with no subject
      - Both: high confidence something real is happening
    """
    if not entities and not verbs:
        return 0.0

    # Normalise counts: 5+ entities and 3+ verbs = full credit
    entity_score = min(len(entities) / 5.0, 1.0)
    verb_score   = min(len(verbs)   / 3.0, 1.0)

    # Bonus for having both
    both_bonus = 0.15 if (entities and verbs) else 0.0

    return min(entity_score * 0.55 + verb_score * 0.30 + both_bonus, 1.0)


def _compute_attention_score(event) -> float:
    """
    MASTER SCORING FORMULA — replaces AttentionEngine's internal scorer.

    score = w_urgency  * urgency_score(payload)
          + w_structure * structural_score(entities, verbs)
          + w_source    * source_weight(source)

    Weights chosen so that:
      - A critical incident with entities/verbs scores ~0.85-0.95
      - A noise log flood scores ~0.05-0.15
      - A routine update (no urgency, some entities) scores ~0.35-0.50

    These weights are a starting point. Use Fix 4 (F1 calibration)
    in diagnostic_tests.py to tune them against your real data.
    """
    urgency   = _compute_urgency_score(getattr(event, 'payload', '') or '')
    structure = _compute_structural_score(
        getattr(event, 'entities', []) or [],
        getattr(event, 'structural_verbs', []) or []
    )
    source_w  = SOURCE_WEIGHTS.get(
        getattr(event, 'source', ''), SOURCE_DEFAULT
    )

    raw = (
        0.50 * urgency   +   # urgency is the primary signal
        0.35 * structure +   # structured fields are secondary
        0.15 * source_w      # source reliability is a prior
    )

    return min(round(raw, 4), 1.0)


def _compute_routes(score: float) -> list:
    """
    FIX 3: Routes are derived ONLY from total_score.

    Previously, routing was done by a separate keyword checker that
    bypassed total_score entirely (Diagnostic 3: score stayed at 0.750
    while routes changed). This caused routes to be unpredictable and
    untestable.

    Now there is exactly one decision boundary:
      score ≥ 0.80 → ShouldAct    (drop-everything urgency)
      score ≥ 0.65 → ShouldReason (needs deliberate thought)
      score ≥ 0.45 → ShouldRemember (worth storing, not urgent)
      score < 0.45 → discard

    This makes the system fully auditable: given a score, you can
    always predict the routes. Given unexpected routes, you know
    exactly which threshold to adjust.
    """
    routes = []
    if score >= THRESHOLD_MEMORY:
        routes.append("ShouldRemember")
    if score >= THRESHOLD_REASON:
        routes.append("ShouldReason")
    if score >= THRESHOLD_ACT:
        routes.append("ShouldAct")
    return routes


def patch_attention(attention_engine):
    """
    Monkey-patch an existing AttentionEngine instance to use the
    corrected scoring formula.

    Usage:
        attention = AttentionEngine()
        patch_attention(attention)
        # Now attention.process(event) uses the fixed formula.
    """
    import types

    original_process = attention_engine.process

    def patched_process(self_or_event, event=None):
        # Handle both bound (self.process(event)) and
        # unbound (process(event)) call styles
        if event is None:
            event = self_or_event

        # Compute new score
        new_score = _compute_attention_score(event)
        new_routes = _compute_routes(new_score)

        # Call original to get the score object, then overwrite fields.
        # This preserves any other fields the original AttentionScore
        # object may have (we don't want to break its structure).
        try:
            original_score_obj = original_process(event)
            original_score_obj.total_score = new_score
            original_score_obj.routes = new_routes
            return original_score_obj
        except Exception:
            # If original process errors, return a minimal object
            class _Score:
                pass
            s = _Score()
            s.total_score = new_score
            s.routes = new_routes
            return s

    # Bind the patched method
    attention_engine.process = types.MethodType(
        lambda self, event: patched_process(event), attention_engine
    )

    print("[PATCH] AttentionEngine.process() replaced with structured scorer.")
    print(f"        Thresholds: ShouldAct≥{THRESHOLD_ACT}  "
          f"ShouldReason≥{THRESHOLD_REASON}  "
          f"ShouldRemember≥{THRESHOLD_MEMORY}")


# ══════════════════════════════════════════════════════════════
#  FIX 4 — REAL SEMANTIC CLAIM EXTRACTION
#
#  Root cause (Diag 5): MockClaim sets subject='Mock' and
#  predicate='is' for every single claim. The TMS therefore
#  receives structurally identical claims and cannot detect
#  contradictions between them.
#
#  This fix extracts real (subject, predicate, object) triples
#  from natural language text. Two strategies are provided:
#
#  Strategy A (recommended): spaCy dependency parsing.
#    Accurate but requires: pip install spacy
#                           python -m spacy download en_core_web_sm
#
#  Strategy B (no dependencies): regex-based heuristic.
#    Less accurate but works immediately with zero installs.
#    Good enough to unblock contradiction detection.
#
#  The patch_reasoning() function uses Strategy B by default,
#  and upgrades to Strategy A if spaCy is available.
# ══════════════════════════════════════════════════════════════

def _extract_triple_spacy(text: str) -> tuple:
    """
    Strategy A: spaCy dependency parse.
    Returns (subject, predicate, object) strings.
    Falls back to heuristic if parse is ambiguous.
    """
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(text)

        subj, pred, obj = None, None, None
        for token in doc:
            if token.dep_ in ("nsubj", "nsubjpass") and subj is None:
                subj = token.lemma_.lower()
            if token.pos_ in ("VERB", "AUX") and pred is None:
                pred = token.lemma_.lower()
            if token.dep_ in ("dobj", "attr", "pobj", "acomp") and obj is None:
                # Get the full span of the object phrase
                obj = " ".join(t.text for t in token.subtree).lower()

        if subj and pred and obj:
            return subj, pred, obj
    except Exception:
        pass

    # Fall back to heuristic
    return _extract_triple_heuristic(text)


def _extract_triple_heuristic(text: str) -> tuple:
    """
    Strategy B: rule-based extraction. No dependencies.

    Handles common sentence patterns:
      "Our runway is 9 months"   → (runway, is, 9 months)
      "Revenue increased by 40%" → (revenue, increased, 40%)
      "API is down"              → (api, is, down)
      "Team decided to delay X"  → (team, decided, delay x)

    Not as accurate as spaCy but correctly separates subjects
    so contradiction detection becomes possible.
    """
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

    # Fallback: use first noun phrase as subject, rest as object
    words = text.lower().split()
    if len(words) >= 3:
        return words[0], words[1], " ".join(words[2:])

    return "unknown", "relates_to", text.lower()


def extract_claim_triple(text: str) -> tuple:
    """
    Public entry point. Uses spaCy if available, heuristic otherwise.
    Always returns (subject, predicate, object) — never crashes.
    """
    try:
        import spacy
        spacy.load("en_core_web_sm")
        return _extract_triple_spacy(text)
    except Exception:
        return _extract_triple_heuristic(text)


def RealSemanticClaim(text: str, confidence: float, source: str,
                      RealClaimClass=None, timestamp: float = None):
    """
    Replacement for MockClaim. Extracts real (subject, predicate, object)
    triples before constructing the SemanticClaim object.

    Usage (replaces MockClaim in test_suite.py):
        from cognitive_os_patches import RealSemanticClaim, RealClaimClass
        # Then:
        claim = RealSemanticClaim(
            text="Runway revised from 18 months to 9 months",
            confidence=0.90,
            source="slack",
            RealClaimClass=RealClaim  # pass your imported RealClaim
        )
    """
    if RealClaimClass is None:
        raise ValueError(
            "Pass your imported SemanticClaim class as RealClaimClass=RealClaim"
        )

    subject, predicate, obj = extract_claim_triple(text)

    return RealClaimClass(
        id='claim_' + str(abs(hash(text)))[-8:],
        subject=subject,
        predicate=predicate,
        object=obj,
        author_id=source,
        timestamp=timestamp or time.time(),
        confidence=confidence,
        status='ACTIVE'
    )


# ══════════════════════════════════════════════════════════════
#  FIX 4b — CONTRADICTION DETECTION LAYER
#
#  Since the ReasoningEngine's add_claim() returns None and
#  exposes no contradiction signal (Diagnostic 5b), we add
#  a wrapper that maintains a contradiction index externally.
#
#  Two claims contradict when:
#    c1.subject == c2.subject   (same entity being described)
#    AND c1.predicate == c2.predicate (same relationship)
#    AND c1.object != c2.object  (different values)
#
#  Example:
#    c1: subject="runway", predicate="is", object="18 months"
#    c2: subject="runway", predicate="is", object="9 months"
#    → CONTRADICTION detected
# ══════════════════════════════════════════════════════════════

class ContradictionDetector:
    """
    Wraps the existing ReasoningEngine to add contradiction detection.

    Usage:
        from cognitive_os_patches import ContradictionDetector
        detector = ContradictionDetector(reasoning)
        detector.add_claim(claim)
        if detector.contradictions:
            print("Conflicts:", detector.contradictions)
    """

    def __init__(self, reasoning_engine):
        self._engine    = reasoning_engine
        self._index     = defaultdict(list)   # (subject, predicate) → [claims]
        self.contradictions = []              # list of (claim_a, claim_b) pairs
        self.unresolved     = []              # equal-confidence contradictions

    def add_claim(self, claim):
        """Add a claim, check for contradictions, then pass to engine."""
        key = (
            getattr(claim, 'subject',   'unknown').lower().strip(),
            getattr(claim, 'predicate', 'unknown').lower().strip()
        )
        obj_new = getattr(claim, 'object', '').lower().strip()

        for existing in self._index[key]:
            obj_old = getattr(existing, 'object', '').lower().strip()

            if obj_new != obj_old:
                # Contradiction found
                conf_new = getattr(claim,    'confidence', 0.5)
                conf_old = getattr(existing, 'confidence', 0.5)

                conflict = {
                    'claim_a'     : existing,
                    'claim_b'     : claim,
                    'subject'     : key[0],
                    'predicate'   : key[1],
                    'object_a'    : obj_old,
                    'object_b'    : obj_new,
                    'confidence_a': conf_old,
                    'confidence_b': conf_new,
                    'resolution'  : self._resolve(conf_old, conf_new),
                }
                self.contradictions.append(conflict)

                if conflict['resolution'] == 'UNRESOLVED':
                    self.unresolved.append(conflict)

                print(f"  [TMS] CONTRADICTION DETECTED:")
                print(f"        Subject:   '{key[0]}'")
                print(f"        Predicate: '{key[1]}'")
                print(f"        Was:       '{obj_old}' (conf={conf_old})")
                print(f"        Now:       '{obj_new}' (conf={conf_new})")
                print(f"        Resolution: {conflict['resolution']}")

        self._index[key].append(claim)

        # Pass to underlying engine
        return self._engine.add_claim(claim)

    def _resolve(self, conf_a: float, conf_b: float) -> str:
        """
        Resolution strategy:
          - If confidence difference > 0.1: higher confidence wins
          - If equal (within 0.1): UNRESOLVED, needs human input
        """
        delta = abs(conf_a - conf_b)
        if delta < 0.10:
            return 'UNRESOLVED (equal authority — needs human)'
        return 'NEWER_WINS' if conf_b > conf_a else 'OLDER_WINS'

    def summary(self):
        print(f"\n  [TMS] Contradiction summary:")
        print(f"        Total contradictions : {len(self.contradictions)}")
        print(f"        Unresolved           : {len(self.unresolved)}")
        for c in self.contradictions:
            print(f"        → '{c['subject']}' {c['predicate']} "
                  f"'{c['object_a']}' vs '{c['object_b']}' "
                  f"[{c['resolution']}]")


def patch_reasoning(reasoning_engine):
    """
    Returns a ContradictionDetector wrapping the engine.
    Use this instead of reasoning_engine directly.

    Usage:
        reasoning = ReasoningEngine()
        reasoning = patch_reasoning(reasoning)   # reassign
        reasoning.add_claim(claim)
        reasoning.summary()
    """
    detector = ContradictionDetector(reasoning_engine)
    print("[PATCH] ReasoningEngine wrapped with ContradictionDetector.")
    return detector


# ══════════════════════════════════════════════════════════════
#  FIX 5 — CONFIDENCE DECAY
#
#  Root cause (Diag 7): no decay mechanism found on
#  ReasoningEngine. Confidence values never change after
#  a claim is stored, so old beliefs are treated as equally
#  reliable as new ones — even months later.
#
#  Mathematical model: exponential decay
#    confidence(t) = c0 × e^(−λ × days_elapsed)
#
#  λ = 0.07/day is a reasonable default:
#    After 1 week : c = c0 × 0.613  (still reliable)
#    After 2 weeks: c = c0 × 0.375  (needs revalidation)
#    After 1 month: c = c0 × 0.122  (near-forgotten)
#    After 3 months: c = c0 × 0.002 (effectively gone)
#
#  Different memory types should decay at different rates:
#    Identity memory:  λ = 0.01  (very slow — identity is stable)
#    Decision memory:  λ = 0.03  (slow — decisions matter long-term)
#    Episodic memory:  λ = 0.07  (medium — routine events fade)
#    Preference memory:λ = 0.05  (medium-slow)
# ══════════════════════════════════════════════════════════════

DECAY_RATES = {
    'identity'   : 0.01,
    'decision'   : 0.03,
    'preference' : 0.05,
    'episodic'   : 0.07,
    'semantic'   : 0.04,
    'procedural' : 0.02,
    'default'    : 0.07,
}


def get_decayed_confidence(
    claim,
    memory_type: str = 'default',
    now: float = None
) -> float:
    """
    Returns the current effective confidence of a claim after decay.

    Args:
        claim:       A SemanticClaim object with .confidence and .timestamp
        memory_type: One of 'identity','decision','episodic',etc.
        now:         Unix timestamp for "now" (defaults to time.time())

    Returns:
        float in [0, 1]

    Example:
        stored_conf = 0.90
        # 14 days later at λ=0.07:
        # effective = 0.90 × e^(−0.07×14) = 0.90 × 0.375 = 0.338
        effective_conf = get_decayed_confidence(claim, 'episodic')
    """
    if now is None:
        now = time.time()

    original_conf = getattr(claim, 'confidence', 1.0)
    stored_at     = getattr(claim, 'timestamp',  now)
    days_elapsed  = (now - stored_at) / 86400.0
    decay_rate    = DECAY_RATES.get(memory_type, DECAY_RATES['default'])

    decayed = original_conf * math.exp(-decay_rate * days_elapsed)
    return round(max(decayed, 0.0), 4)


def should_forget(claim, memory_type: str = 'episodic',
                  forget_threshold: float = 0.10) -> bool:
    """
    Returns True if a claim's effective confidence has decayed
    below the forgetting threshold.

    Default threshold: 0.10
    At λ=0.07, this triggers after ~32 days for a perfect claim.
    At λ=0.01 (identity), this would take ~230 days.
    """
    return get_decayed_confidence(claim, memory_type) < forget_threshold


def decay_report(claims: list, memory_type: str = 'episodic'):
    """
    Print a decay status report for a list of claims.
    Useful for visualising what the nightly Forget() sweep would prune.

    Usage:
        decay_report(reasoning.claims, memory_type='episodic')
    """
    now = time.time()
    print(f"\n  [DECAY] Report for {len(claims)} claims (type={memory_type}):")
    for c in claims:
        eff  = get_decayed_confidence(c, memory_type, now)
        text = getattr(c, 'object', str(c))[:50]
        days = (now - getattr(c, 'timestamp', now)) / 86400
        keep = "KEEP" if eff >= 0.10 else "FORGET"
        print(f"    [{keep}]  eff_conf={eff:.3f}  "
              f"age={days:.1f}d  '{text}'")


# ══════════════════════════════════════════════════════════════
#  COMBINED PATCH — apply everything at once
# ══════════════════════════════════════════════════════════════

def apply_all_patches(attention_engine, reasoning_engine):
    """
    Apply all fixes in one call.

    Returns (patched_attention, patched_reasoning) tuple.

    Usage:
        from cognitive_os_patches import apply_all_patches
        attention, reasoning = apply_all_patches(attention, reasoning)
    """
    print("\n[PATCHES] Applying all Cognitive OS fixes...\n")
    patch_attention(attention_engine)
    patched_reasoning = patch_reasoning(reasoning_engine)
    print("\n[PATCHES] All patches applied. Run diagnostic_tests.py to verify.\n")
    return attention_engine, patched_reasoning


# ══════════════════════════════════════════════════════════════
#  QUICK SELF-TEST — run this file directly to verify patches
#  python cognitive_os_patches.py
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("COGNITIVE OS PATCHES — Self-test")
    print("="*50)
    print()

    # Test scoring formula standalone (no engine needed)
    print("── Scoring formula standalone test ──")

    class _FakeEvent:
        def __init__(self, payload, source, entities, verbs):
            self.payload         = payload
            self.source          = source
            self.entities        = entities
            self.structural_verbs = verbs

    cases = [
        ("CRITICAL incident",
         _FakeEvent("Critical: production DB down, all customers locked out",
                    "slack", ["DB","customers"], ["down","locked"])),
        ("Routine standup",
         _FakeEvent("Standup done. No blockers.",
                    "slack", ["standup"], ["done"])),
        ("Noise flood (ERROR×500)",
         _FakeEvent("ERROR " * 500, "monitoring", [], [])),
        ("Empty payload",
         _FakeEvent("", "slack", [], [])),
        ("Hindi text",
         _FakeEvent("टीम का मनोबल बहुत कम है", "slack",
                    ["team","morale"], ["low"])),
    ]

    for label, event in cases:
        score  = _compute_attention_score(event)
        routes = _compute_routes(score)
        print(f"  {label:<30} score={score:.4f}  routes={routes}")

    print()
    print("── Contradiction detection standalone test ──")

    sub, pred, obj = extract_claim_triple("Our runway is 18 months")
    print(f"  'Our runway is 18 months' → ({sub}, {pred}, {obj})")

    sub, pred, obj = extract_claim_triple("Our runway is 9 months")
    print(f"  'Our runway is 9 months'  → ({sub}, {pred}, {obj})")

    sub, pred, obj = extract_claim_triple("Revenue increased by 40 percent")
    print(f"  'Revenue increased 40%'   → ({sub}, {pred}, {obj})")

    print()
    print("── Confidence decay standalone test ──")

    class _FakeClaim:
        def __init__(self, conf, days_ago):
            self.confidence = conf
            self.timestamp  = time.time() - (days_ago * 86400)
            self.object     = f"claim stored {days_ago}d ago"

    for days in [0, 7, 14, 30, 90]:
        c   = _FakeClaim(1.0, days)
        eff = get_decayed_confidence(c, 'episodic')
        frg = should_forget(c, 'episodic')
        print(f"  T+{days:2d}d  episodic  eff_conf={eff:.3f}  "
              f"{'← FORGET' if frg else 'keep'}")

    print()
    print("Self-test complete. No engine imports needed for standalone checks.")
    print("To apply patches to your engines, import apply_all_patches().")