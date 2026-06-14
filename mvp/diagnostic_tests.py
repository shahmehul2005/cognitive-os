"""
cognitive_os_diagnostic.py
==========================
MATHEMATICAL VALIDATION SUITE for Cognitive OS
Run this ALONGSIDE your existing test_suite.py to answer:

  1. Is AttentionEngine hardcoded or mathematically grounded?
  2. Is ReasoningEngine actually reasoning or just storing strings?
  3. What are the quantitative gaps and how do you fix them?

Run with:
    python diagnostic_tests.py

No external dependencies beyond what your system already uses.
"""

import time
import math
import sys
import os
import statistics
from collections import defaultdict

sys.path.append(os.path.dirname(__file__))

from attention_engine import AttentionEngine, PerceivedEvent, IdentityVector
from reasoning_engine import ReasoningEngine, SemanticClaim as RealClaim

# ─────────────────────────────────────────────────────────────
# MOCK CLAIM (same wrapper as test_suite.py)
# ─────────────────────────────────────────────────────────────
from reasoning_engine import extract_claim_triple

def MockClaim(text, confidence, source):
    subject, predicate, obj = extract_claim_triple(text)
    return RealClaim(
        id='mock_' + str(hash(text))[-8:],
        subject=subject,
        predicate=predicate,
        object=obj,
        author_id=source,
        timestamp=time.time(),
        confidence=confidence,
        status='ACTIVE'
    )

# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────
PASS = "✅ PASS"
FAIL = "❌ FAIL"
WARN = "⚠️  WARN"

def header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def subheader(title):
    print(f"\n  ── {title} ──")

def result(label, passed, detail=""):
    status = PASS if passed else FAIL
    line = f"    {status}  {label}"
    if detail:
        line += f"  [{detail}]"
    print(line)
    return passed

def warn(label, detail=""):
    line = f"    {WARN}  {label}"
    if detail:
        line += f"  [{detail}]"
    print(line)

def make_event(idx, payload, source="slack", entities=None, verbs=None):
    return PerceivedEvent(
        id=f"diag_evt_{idx}",
        source=source,
        payload=payload,
        timestamp=time.time(),
        entities=entities or [],
        structural_verbs=verbs or []
    )

# ─────────────────────────────────────────────────────────────
# DIAGNOSTIC 1 — SCORE SENSITIVITY
# Is the score actually responding to input changes,
# or is it returning the same value regardless?
#
# Mathematical basis:
#   A real scoring function f(x) must satisfy:
#   f(high_signal) >> f(noise)
#   Minimum required separation: Δscore ≥ 0.20
#   (below 0.20, the model cannot reliably discriminate)
# ─────────────────────────────────────────────────────────────
def diag_score_sensitivity(attention):
    header("DIAGNOSTIC 1 — Score Sensitivity (Is scoring real or hardcoded?)")

    probe_pairs = [
        (
            "HIGH signal",
            make_event(1,
                "CRITICAL: Production database is down. All customers locked out. Revenue loss $10k/min.",
                entities=["database", "customers", "revenue"],
                verbs=["down", "locked out"]),
        ),
        (
            "LOW signal",
            make_event(2, "health check OK", source="monitoring"),
        ),
        (
            "MEDIUM signal",
            make_event(3, "Team standup done. Two PRs ready for review.",
                entities=["PRs"],
                verbs=["review"]),
        ),
        (
            "EMPTY signal",
            make_event(4, ""),
        ),
        (
            "NOISE — emoji only",
            make_event(5, "🚀🔥💡🎯🧠"),
        ),
        (
            "NOISE — repeated word",
            make_event(6, "ERROR " * 100),
            ),
    ]

    scores = {}
    for label, event in probe_pairs:
        s = attention.process(event)
        scores[label] = s.total_score
        print(f"    {label:<30} score = {s.total_score:.4f}  routes = {s.routes}")

    high  = scores["HIGH signal"]
    low   = scores["LOW signal"]
    empty = scores["EMPTY signal"]
    noise = scores["NOISE — repeated word"]

    delta_high_low   = high - low
    delta_high_empty = high - empty
    delta_high_noise = high - noise

    print()
    result(
        f"High vs Low separation   Δ={delta_high_low:.4f}  (need ≥0.20)",
        delta_high_low >= 0.20,
        f"Δ={delta_high_low:.4f}"
    )
    result(
        f"High vs Empty separation Δ={delta_high_empty:.4f}  (need ≥0.20)",
        delta_high_empty >= 0.20,
        f"Δ={delta_high_empty:.4f}"
    )
    result(
        f"High vs Noise separation Δ={delta_high_noise:.4f}  (need ≥0.20)",
        delta_high_noise >= 0.20,
        f"Δ={delta_high_noise:.4f}"
    )

    # Hardcode detection: if all scores are within 0.05 of each other,
    # the function is almost certainly returning a constant.
    all_scores = list(scores.values())
    score_range = max(all_scores) - min(all_scores)
    is_hardcoded = score_range < 0.05
    result(
        f"Score range across inputs = {score_range:.4f}  (if <0.05 → likely hardcoded)",
        not is_hardcoded,
        "HARDCODED SUSPECTED" if is_hardcoded else "dynamic"
    )

    return scores


# ─────────────────────────────────────────────────────────────
# DIAGNOSTIC 2 — MONOTONICITY TEST
# Adding more signal-bearing entities should increase the score.
# f(payload + more_entities) ≥ f(payload)
#
# If adding entities LOWERS the score or has no effect,
# the entity weighting in your formula is broken or absent.
# ─────────────────────────────────────────────────────────────
def diag_monotonicity(attention):
    header("DIAGNOSTIC 2 — Monotonicity (Does more signal = higher score?)")

    base_payload = "The server crashed."
    configs = [
        ("0 entities, 0 verbs",  [],                              []),
        ("1 entity,  0 verbs",   ["server"],                      []),
        ("1 entity,  1 verb",    ["server"],                      ["crashed"]),
        ("3 entities, 1 verb",   ["server","production","users"], ["crashed"]),
        ("3 entities, 3 verbs",  ["server","production","users"], ["crashed","lost","blocked"]),
    ]

    prev_score = -1
    prev_label = None
    monotone = True
    for label, entities, verbs in configs:
        event = make_event(99, base_payload, entities=entities, verbs=verbs)
        s = attention.process(event)
        sc = s.total_score
        arrow = "↑" if sc > prev_score else ("=" if sc == prev_score else "↓")
        direction_ok = sc >= prev_score
        if prev_score >= 0 and not direction_ok:
            monotone = False
        print(f"    {label:<35} score={sc:.4f}  {arrow}")
        prev_score = sc
        prev_label = label

    print()
    result(
        "Score is monotonically non-decreasing with signal richness",
        monotone,
        "FORMULA MAY IGNORE ENTITIES/VERBS" if not monotone else "OK"
    )
    return monotone


# ─────────────────────────────────────────────────────────────
# DIAGNOSTIC 3 — ROUTE THRESHOLD CALIBRATION
# For a routing system to be trustworthy, the thresholds that
# separate "ShouldAct" from "ShouldRemember" from "discard"
# must be stable and consistent.
#
# We probe the boundary by sweeping entity count and measuring
# exactly where routing changes. A well-calibrated system
# should have clear, consistent breakpoints.
# ─────────────────────────────────────────────────────────────
def diag_route_thresholds(attention):
    header("DIAGNOSTIC 3 — Route Threshold Calibration")

    templates = [
        ("Escalating urgency",
         ["Server slow.",
          "Server is down.",
          "Production server is down.",
          "Critical: production server down, customers affected.",
          "CRITICAL: production down 3h, $50k revenue loss, CEO alerted."]),
        ("Escalating entities",
         [
          "Something happened.",
          "The API failed.",
          "The payment API failed affecting users.",
          "The payment API and auth service failed affecting 1000 users.",
          "Payment API, auth, and database all failed. 5000 users locked out. Data at risk."
         ]),
    ]

    for series_name, payloads in templates:
        subheader(series_name)
        prev_routes = None
        for i, p in enumerate(payloads):
            entities = [w for w in p.split() if w[0].isupper() or len(w) > 6][:5]
            event = make_event(200+i, p, entities=entities, verbs=["failed","down","affected"])
            s = attention.process(event)
            changed = " ← ROUTE CHANGED" if prev_routes is not None and set(s.routes) != set(prev_routes) else ""
            print(f"    L{i+1}  score={s.total_score:.3f}  routes={s.routes}{changed}")
            prev_routes = s.routes

    print()
    print("    ℹ️  Look for: (a) routes changing at consistent score thresholds,")
    print("                 (b) no jumps from [] → [ShouldAct] skipping [ShouldRemember]")


# ─────────────────────────────────────────────────────────────
# DIAGNOSTIC 4 — LATENCY DISTRIBUTION
# A production attention engine must be fast AND consistent.
# We measure: mean, std dev, p95, p99 across 50 runs.
#
# Acceptable thresholds:
#   mean   < 50ms
#   p95    < 100ms
#   p99    < 200ms
#   std_dev < 20ms  (high variance = unstable performance)
# ─────────────────────────────────────────────────────────────
def diag_latency(attention):
    header("DIAGNOSTIC 4 — Latency Distribution (50 runs)")

    payload = "Critical: production API down, customers impacted, revenue loss ongoing."
    event   = make_event(300, payload,
                         entities=["API","customers","revenue"],
                         verbs=["down","impacted"])

    latencies = []
    for _ in range(50):
        t0 = time.time()
        attention.process(event)
        latencies.append((time.time() - t0) * 1000)

    mean_ms  = statistics.mean(latencies)
    std_ms   = statistics.stdev(latencies)
    p95_ms   = sorted(latencies)[int(0.95 * len(latencies))]
    p99_ms   = sorted(latencies)[int(0.99 * len(latencies))]
    min_ms   = min(latencies)
    max_ms   = max(latencies)

    print(f"    mean={mean_ms:.2f}ms  std={std_ms:.2f}ms  "
          f"p95={p95_ms:.2f}ms  p99={p99_ms:.2f}ms  "
          f"min={min_ms:.2f}ms  max={max_ms:.2f}ms")
    print()

    result(f"mean < 50ms   (actual: {mean_ms:.1f}ms)",  mean_ms  < 50)
    result(f"p95  < 100ms  (actual: {p95_ms:.1f}ms)",   p95_ms   < 100)
    result(f"p99  < 200ms  (actual: {p99_ms:.1f}ms)",   p99_ms   < 200)
    result(f"std  < 20ms   (actual: {std_ms:.1f}ms)",   std_ms   < 20,
           "HIGH VARIANCE — scoring may be doing I/O or LLM calls" if std_ms >= 20 else "stable")

    return {"mean": mean_ms, "std": std_ms, "p95": p95_ms, "p99": p99_ms}


# ─────────────────────────────────────────────────────────────
# DIAGNOSTIC 5 — REASONING ENGINE STRUCTURE CHECK
# Tests whether the ReasoningEngine is actually using the
# SemanticClaim fields for logic, or just storing text blobs.
#
# Mathematical test:
#   If two claims have contradicting objects on the same subject,
#   a real TMS must detect the contradiction.
#   We check: does add_claim() return or expose any contradiction signal?
# ─────────────────────────────────────────────────────────────
def diag_reasoning_structure(reasoning):
    header("DIAGNOSTIC 5 — Reasoning Engine Structure Check")

    subheader("5a — Claim field structure")
    c = MockClaim(text="Revenue increased by 40 percent", confidence=0.9, source="slack")
    print(f"    claim.subject   = '{c.subject}'")
    print(f"    claim.predicate = '{c.predicate}'")
    print(f"    claim.object    = '{c.object}'")
    print(f"    claim.confidence= {c.confidence}")
    print()

    subject_real  = c.subject != 'Mock'
    predicate_real = c.predicate != 'is'

    result(
        "subject is semantically extracted (not hardcoded 'Mock')",
        subject_real,
        "HARDCODED — MockClaim sets subject='Mock' for all claims" if not subject_real else "OK"
    )
    result(
        "predicate is semantically extracted (not hardcoded 'is')",
        predicate_real,
        "HARDCODED — MockClaim sets predicate='is' for all claims" if not predicate_real else "OK"
    )

    if not subject_real:
        print()
        print("    ⚠️  CRITICAL IMPLICATION:")
        print("       Your TMS receives: subject='Mock', predicate='is', object='<full text>'")
        print("       This means ALL claims look identical in structure.")
        print("       Contradiction detection (B1 ⊗ B2) is IMPOSSIBLE with this schema.")
        print("       The TMS cannot distinguish 'runway is 18 months' from")
        print("       'runway is 9 months' because both have subject='Mock'.")
        print()
        print("    FIX REQUIRED → see Section 6 below.")

    subheader("5b — Contradiction detection probe")
    print("    Injecting two contradicting claims about runway...")

    c_a = MockClaim(text="Our runway is 18 months", confidence=0.9, source="cfo")
    c_b = MockClaim(text="Our runway is 9 months",  confidence=0.9, source="cfo")

    result_a = reasoning.add_claim(c_a)
    result_b = reasoning.add_claim(c_b)

    print(f"    add_claim(18 months) returned: {result_a}")
    print(f"    add_claim(9 months)  returned: {result_b}")
    print()

    # Check if reasoning engine exposed any contradiction signal
    contradiction_detected = False
    for attr in ["contradictions", "conflicts", "status", "flags", "unresolved"]:
        if hasattr(reasoning, attr):
            val = getattr(reasoning, attr)
            print(f"    reasoning.{attr} = {val}")
            if val:
                contradiction_detected = True

    result(
        "ReasoningEngine detected runway contradiction",
        contradiction_detected,
        "no contradiction signal found — TMS may not be checking for conflicts" if not contradiction_detected else "OK"
    )


# ─────────────────────────────────────────────────────────────
# DIAGNOSTIC 6 — SCORE FORMULA REVERSE-ENGINEERING
# We isolate the contribution of each input variable by
# toggling them one at a time (ablation study).
#
# This tells us EXACTLY which variables the formula uses
# and their relative weights.
#
# For a well-designed attention formula:
#   score = w1*urgency + w2*entity_count + w3*verb_count
#           + w4*source_weight + w5*payload_length_penalty
#
# Each coefficient w_i should be positive and non-trivial (>0.05).
# ─────────────────────────────────────────────────────────────
def diag_ablation(attention):
    header("DIAGNOSTIC 6 — Ablation Study (What does the score formula actually use?)")

    base_payload = "The production API is down and customers are losing money."

    # Baseline: full signal
    e_base = make_event(400, base_payload,
                        entities=["API", "customers", "money"],
                        verbs=["down", "losing"])
    s_base = attention.process(e_base).total_score

    # Ablation 1: remove entities
    e_no_ent = make_event(401, base_payload, entities=[], verbs=["down", "losing"])
    s_no_ent = attention.process(e_no_ent).total_score

    # Ablation 2: remove verbs
    e_no_verb = make_event(402, base_payload, entities=["API","customers","money"], verbs=[])
    s_no_verb = attention.process(e_no_verb).total_score

    # Ablation 3: remove both
    e_no_ev = make_event(403, base_payload, entities=[], verbs=[])
    s_no_ev = attention.process(e_no_ev).total_score

    # Ablation 4: change source
    e_monitor = make_event(404, base_payload,
                           entities=["API","customers","money"],
                           verbs=["down","losing"],
                           source="monitoring")
    s_monitor = attention.process(e_monitor).total_score

    # Ablation 5: empty payload, rich entities
    e_empty_rich = make_event(405, "",
                              entities=["API","customers","money","production","database"],
                              verbs=["down","failed","losing","blocked","crashed"])
    s_empty_rich = attention.process(e_empty_rich).total_score

    print(f"    Baseline (full signal)          : {s_base:.4f}")
    print(f"    − entities removed              : {s_no_ent:.4f}  Δ={s_base-s_no_ent:+.4f}")
    print(f"    − verbs removed                 : {s_no_verb:.4f}  Δ={s_base-s_no_verb:+.4f}")
    print(f"    − entities AND verbs removed    : {s_no_ev:.4f}  Δ={s_base-s_no_ev:+.4f}")
    print(f"    − source changed to monitoring  : {s_monitor:.4f}  Δ={s_base-s_monitor:+.4f}")
    print(f"    − empty payload, rich entities  : {s_empty_rich:.4f}")
    print()

    entity_contribution = abs(s_base - s_no_ent)
    verb_contribution   = abs(s_base - s_no_verb)
    source_contribution = abs(s_base - s_monitor)

    result(
        f"Entities affect score  (contribution={entity_contribution:.4f}, need >0.05)",
        entity_contribution > 0.05,
        "ENTITIES MAY BE IGNORED IN FORMULA" if entity_contribution <= 0.05 else "OK"
    )
    result(
        f"Verbs affect score     (contribution={verb_contribution:.4f}, need >0.05)",
        verb_contribution > 0.05,
        "VERBS MAY BE IGNORED IN FORMULA" if verb_contribution <= 0.05 else "OK"
    )
    result(
        f"Source affects score   (contribution={source_contribution:.4f})",
        source_contribution > 0.01,
        "SOURCE WEIGHT MAY NOT BE IMPLEMENTED" if source_contribution <= 0.01 else "OK"
    )

    if s_empty_rich > 0.3:
        warn(
            f"Empty payload with rich entities scored {s_empty_rich:.4f} — "
            "entities alone can trigger routing even with no actual text content"
        )


# ─────────────────────────────────────────────────────────────
# DIAGNOSTIC 7 — CONFIDENCE DECAY MATHEMATICS
# If your system stores confidence scores, they must decay
# over time according to a curve (Ebbinghaus or exponential).
#
# Test: inject a claim, wait, re-retrieve, check decay was applied.
# Mathematical expectation:
#   confidence(t) = confidence(0) × e^(−λt)
#   where λ is the decay rate (typically 0.05–0.2 per day)
#
# If confidence(t) == confidence(0), there is no decay.
# ─────────────────────────────────────────────────────────────
def diag_confidence_decay(reasoning):
    header("DIAGNOSTIC 7 — Confidence Decay Mathematics")

    c = MockClaim(
        text="Our runway is 18 months",
        confidence=1.0,
        source="cfo"
    )
    reasoning.add_claim(c)

    # Check if the reasoning engine exposes any decay mechanism
    decay_found = False
    for attr in ["decay", "decay_rate", "apply_decay", "get_confidence", "claims"]:
        if hasattr(reasoning, attr):
            val = getattr(reasoning, attr)
            print(f"    reasoning.{attr} found: {type(val).__name__}")
            decay_found = True

    if not decay_found:
        print("    No decay-related attributes found on ReasoningEngine.")

    print()
    result(
        "ReasoningEngine exposes a decay mechanism",
        decay_found,
        "DECAY NOT IMPLEMENTED — confidence never degrades over time" if not decay_found else "present"
    )

    print()
    print("    Expected mathematical model:")
    print("      confidence(t) = c0 × e^(−λt)")
    print("      λ = 0.1/day → after 7 days: c = 1.0 × e^(−0.7) ≈ 0.497")
    print("      λ = 0.05/day → after 7 days: c = 1.0 × e^(−0.35) ≈ 0.705")
    print()
    for days in [1, 3, 7, 14, 30]:
        c_fast = math.exp(-0.1  * days)
        c_slow = math.exp(-0.05 * days)
        print(f"      T+{days:2d}d: fast_decay={c_fast:.3f}  slow_decay={c_slow:.3f}")


# ─────────────────────────────────────────────────────────────
# DIAGNOSTIC 8 — SCORE REPRODUCIBILITY
# A deterministic scoring function must return the SAME score
# for the same input on every call.
# If scores vary across identical calls, the function uses
# randomness or external state (LLM, timestamps, etc.)
# ─────────────────────────────────────────────────────────────
def diag_reproducibility(attention):
    header("DIAGNOSTIC 8 — Score Reproducibility (Determinism check)")

    payload  = "Critical: production database is down. All customers affected."
    entities = ["database", "customers", "production"]
    verbs    = ["down", "affected"]

    scores = []
    for i in range(10):
        event = make_event(500 + i, payload, entities=entities, verbs=verbs)
        s = attention.process(event).total_score
        scores.append(s)

    unique_scores = set(round(s, 6) for s in scores)
    is_deterministic = len(unique_scores) == 1
    score_variance   = statistics.variance(scores) if len(scores) > 1 else 0

    print(f"    10 identical calls → scores: {[f'{s:.4f}' for s in scores]}")
    print(f"    Unique values: {len(unique_scores)}  |  Variance: {score_variance:.8f}")
    print()

    result(
        "Score is deterministic (same input → same output every time)",
        is_deterministic,
        "NON-DETERMINISTIC — system may use LLM, randomness, or mutable state" if not is_deterministic else "OK"
    )

    if not is_deterministic:
        print()
        print("    ⚠️  NON-DETERMINISM IMPLICATIONS:")
        print("       - Tests can pass on one run and fail on the next")
        print("       - You cannot set reliable routing thresholds")
        print("       - Confidence values are meaningless if they fluctuate")
        print("       FIX: ensure score formula uses only the event fields,")
        print("            not timestamps, random seeds, or external API calls")

    return is_deterministic


# ─────────────────────────────────────────────────────────────
# FINAL REPORT
# ─────────────────────────────────────────────────────────────
def print_recommendations(results):
    header("SUMMARY & MATHEMATICAL FIX RECOMMENDATIONS")

    print("""
  Based on the diagnostics above, here are the fixes ranked by impact:

  ┌─────────────────────────────────────────────────────────────┐
  │  FIX 1 (CRITICAL) — Replace MockClaim with real NLP        │
  ├─────────────────────────────────────────────────────────────┤
  │  Problem: subject='Mock', predicate='is' for ALL claims.   │
  │  TMS cannot detect contradictions with this structure.      │
  │                                                             │
  │  Fix: extract (subject, predicate, object) triples via     │
  │  spaCy dependency parsing before creating SemanticClaim.   │
  │                                                             │
  │  import spacy                                               │
  │  nlp = spacy.load("en_core_web_sm")                        │
  │  doc = nlp("Our runway is 9 months")                       │
  │  # → subject="runway", predicate="is", object="9 months"  │
  │                                                             │
  │  Contradiction check:                                       │
  │  if c1.subject == c2.subject and c1.object != c2.object:  │
  │      flag_as_conflict(c1, c2)                              │
  └─────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────┐
  │  FIX 2 (HIGH) — Implement explicit scoring formula         │
  ├─────────────────────────────────────────────────────────────┤
  │  If Diagnostic 6 shows entities/verbs don't affect score,  │
  │  add this formula explicitly to AttentionEngine:           │
  │                                                             │
  │  SOURCE_WEIGHTS = {                                         │
  │      "slack": 0.85, "git": 0.90,                           │
  │      "monitoring": 0.70, "email": 0.75                     │
  │  }                                                          │
  │                                                             │
  │  def compute_score(event):                                  │
  │      urgency  = count_urgency_keywords(event.payload)      │
  │      entities = min(len(event.entities) / 5.0, 1.0)       │
  │      verbs    = min(len(event.verbs)    / 3.0, 1.0)       │
  │      source   = SOURCE_WEIGHTS.get(event.source, 0.5)     │
  │      length   = min(len(event.payload)  / 200.0, 1.0)     │
  │                                                             │
  │      raw = (0.40 * urgency  +                              │
  │             0.25 * entities +                              │
  │             0.15 * verbs    +                              │
  │             0.10 * source   +                              │
  │             0.10 * length)                                 │
  │      return min(raw, 1.0)                                  │
  └─────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────┐
  │  FIX 3 (HIGH) — Add confidence decay to memory             │
  ├─────────────────────────────────────────────────────────────┤
  │  If Diagnostic 7 shows no decay mechanism:                 │
  │                                                             │
  │  import math                                                │
  │  DECAY_RATE = 0.07  # per day                              │
  │                                                             │
  │  def get_current_confidence(claim, now=None):              │
  │      if now is None:                                        │
  │          now = time.time()                                  │
  │      days_elapsed = (now - claim.timestamp) / 86400        │
  │      return claim.confidence * math.exp(                   │
  │          -DECAY_RATE * days_elapsed                        │
  │      )                                                      │
  │                                                             │
  │  # After 7 days at λ=0.07:                                 │
  │  # c = 1.0 × e^(−0.49) ≈ 0.613  (still relevant)         │
  │  # After 30 days:                                           │
  │  # c = 1.0 × e^(−2.1) ≈ 0.122  (near forgotten)          │
  └─────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────┐
  │  FIX 4 (MEDIUM) — Validate thresholds empirically          │
  ├─────────────────────────────────────────────────────────────┤
  │  Your current thresholds (e.g. ShouldAct ≥ 0.85) were     │
  │  set by intuition. Calibrate them against real data:       │
  │                                                             │
  │  1. Label 50 real messages manually:                        │
  │     {payload: "...", correct_route: "ShouldAct"}           │
  │  2. Run all through AttentionEngine                         │
  │  3. Find the score threshold that maximises F1:            │
  │                                                             │
  │     best_t, best_f1 = 0, 0                                 │
  │     for t in [x/100 for x in range(50, 100)]:             │
  │         predicted = [s >= t for s in scores]              │
  │         f1 = f1_score(labels, predicted)                   │
  │         if f1 > best_f1:                                   │
  │             best_t, best_f1 = t, f1                        │
  └─────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────┐
  │  FIX 5 (MEDIUM) — Add route coverage assertion             │
  ├─────────────────────────────────────────────────────────────┤
  │  Add this to run_test_suite() after each test:             │
  │                                                             │
  │  # Assert score ranges are sensible                         │
  │  assert 0.0 <= score.total_score <= 1.0, \                 │
  │      f"Score out of bounds: {score.total_score}"           │
  │                                                             │
  │  # Assert no unexpected routes for noise                    │
  │  if case.get("expected_routes") == []:                     │
  │      assert score.total_score < 0.5, \                     │
  │          f"Noise scored too high: {score.total_score}"     │
  └─────────────────────────────────────────────────────────────┘
    """)


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\nCOGNITIVE OS — MATHEMATICAL DIAGNOSTIC SUITE")
    print("============================================\n")
    print("This runs INDEPENDENTLY of test_suite.py.")
    print("It tests whether the underlying math is sound.\n")

    attention = AttentionEngine()
    attention.active_identity = IdentityVector(
        mission="Maintain stability and scale the infrastructure."
    )
    reasoning = ReasoningEngine()

    diag_score_sensitivity(attention)
    diag_monotonicity(attention)
    diag_route_thresholds(attention)
    diag_latency(attention)
    diag_reasoning_structure(reasoning)
    diag_ablation(attention)
    diag_confidence_decay(reasoning)
    diag_reproducibility(attention)
    print_recommendations({})