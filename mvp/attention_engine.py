import time
import math
import json
import os
import sys
from dataclasses import dataclass, field
from typing import List, Dict, Any

# Ensure local imports work
sys.path.append(os.path.dirname(__file__))

@dataclass
class PerceivedEvent:
    id: str
    source: str
    payload: str
    timestamp: float
    entities: List[str] = field(default_factory=list)
    structural_verbs: List[str] = field(default_factory=list)

@dataclass
class AttentionScore:
    total_score: float
    recency_val: float
    entropy_val: float
    identity_val: float
    routes: List[str]

@dataclass
class IdentityVector:
    mission: str
    embedding: List[float] = field(default_factory=list)

def load_identity() -> IdentityVector:
    identity_path = os.path.join(os.path.dirname(__file__), "workspace_identity.json")
    try:
        with open(identity_path, "r") as f:
            data = json.load(f)
            # For this MVP, we fake the embedding using keywords from mission
            return IdentityVector(mission=data.get("mission", ""))
    except Exception:
        return IdentityVector(mission="")

def mock_cosine_similarity(text: str, identity_mission: str) -> float:
    """Mock vector similarity using keyword overlap for the MVP crucible test."""
    if not identity_mission or not text:
        return 0.1
    mission_words = set(identity_mission.lower().split())
    text_words = set(text.lower().split())
    overlap = len(mission_words.intersection(text_words))
    # Simple overlap score between 0 and 1
    return min(1.0, 0.2 + (0.15 * overlap))

def CalculateAttentionScore(event: PerceivedEvent, active_identity: IdentityVector) -> AttentionScore:
    # 1. Recency
    time_delta_hours = max(0, (time.time() - event.timestamp)) / 3600
    recency_val = math.exp(-0.1 * time_delta_hours)
    
    # 2. Entropy / Structural Weight
    structural_weight = 0.0
    high_entropy_verbs = ["migrate", "deprecate", "launch", "fail", "switch"]
    low_entropy_verbs = ["fix", "update", "meeting", "ping"]
    
    if any(verb in event.structural_verbs for verb in high_entropy_verbs):
        structural_weight = 0.85
    elif any(verb in event.structural_verbs for verb in low_entropy_verbs):
        structural_weight = 0.30
        
    # 3. Identity Alignment
    identity_val = mock_cosine_similarity(event.payload, active_identity.mission)
    
    # 4. Final Calculation
    # Weights: w_r = 0.2, w_e = 0.5, w_i = 0.3
    total = (0.2 * recency_val) + (0.5 * structural_weight) + (0.3 * identity_val)
    
    # 5. Routing Gates
    routes = []
    if total > 0.70:
        routes.append("ShouldReason")
    if total > 0.40 or "fact" in event.entities:
        routes.append("ShouldRemember")
        
    return AttentionScore(
        total_score=total,
        recency_val=recency_val,
        entropy_val=structural_weight,
        identity_val=identity_val,
        routes=routes
    )

class AttentionEngine:
    def __init__(self):
        self.active_identity = load_identity()
        self.dropped_events_queue: List[PerceivedEvent] = []
        
    def process(self, event: PerceivedEvent) -> AttentionScore:
        score = CalculateAttentionScore(event, self.active_identity)
        
        # Failure Mode 1: False Negative (The Dropped Ball) Recovery Check
        if not score.routes:
            self.dropped_events_queue.append(event)
            # Check resonance
            if len(self.dropped_events_queue) > 3:
                # If we get flooded with dropped events (e.g. system is down), elevate the latest
                score.routes.append("ShouldReason")
                score.total_score = 0.99
                # clear queue after escalating
                self.dropped_events_queue.clear()
                
        # Failure Mode 2: False Positive (Panic Attack) is handled downstream by Reasoning
        return score
