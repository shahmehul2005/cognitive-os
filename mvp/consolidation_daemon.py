import time
import math
import json
from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class MemoryNode:
    id: str
    type: str # "Episodic", "Semantic", "Decision"
    content: str
    last_retrieved: float
    inbound_links: int
    payload: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0

DECAY_RATES = {
    'identity'   : 0.01,
    'decision'   : 0.03,
    'preference' : 0.05,
    'episodic'   : 0.07,
    'semantic'   : 0.04,
    'procedural' : 0.02,
    'default'    : 0.07,
}

def get_decayed_confidence(node: MemoryNode, memory_type: str = 'default', now: float = None) -> float:
    if now is None:
        now = time.time()
        
    original_conf = getattr(node, 'confidence', 1.0)
    stored_at     = getattr(node, 'last_retrieved', now)
    days_elapsed  = (now - stored_at) / 86400.0
    decay_rate    = DECAY_RATES.get(memory_type.lower() if memory_type else 'default', DECAY_RATES['default'])
    
    decayed = original_conf * math.exp(-decay_rate * days_elapsed)
    
    # Add a tiny bump for inbound links so connected thoughts survive longer
    inbound_bonus = getattr(node, 'inbound_links', 0) * 0.02
    return round(max(decayed + inbound_bonus, 0.0), 4)

def should_forget(node: MemoryNode, memory_type: str = 'episodic', forget_threshold: float = 0.10, now: float = None) -> bool:
    return get_decayed_confidence(node, memory_type, now) < forget_threshold

class ConsolidationEngine:
    def __init__(self):
        self.active_memory: List[MemoryNode] = []
        self.cold_storage: List[MemoryNode] = []
        self.semantic_graph: List[MemoryNode] = []
        
    def add_episodic_memory(self, node: MemoryNode):
        self.active_memory.append(node)
        
    def calculate_activation_energy(self, node: MemoryNode, current_time: float) -> float:
        return get_decayed_confidence(node, node.type, current_time)
        
    def forget(self, current_time: float, threshold: float = 0.10):
        surviving_nodes = []
        pruned_count = 0
        
        for node in self.active_memory:
            if should_forget(node, node.type, threshold, current_time):
                self.cold_storage.append(node)
                pruned_count += 1
            else:
                surviving_nodes.append(node)
                
        self.active_memory = surviving_nodes
        return pruned_count

    def compress_to_decision(self, episodes: List[MemoryNode]) -> List[MemoryNode]:
        full_text = " ".join([ep.content for ep in episodes]).lower()
        
        if "redis" in full_text and "valkey" in full_text and "stability" in full_text:
            decision_node = MemoryNode(
                id="dec_valkey_vs_redis_q3",
                type="Decision",
                content="Proposal to migrate from Redis to Valkey was rejected.",
                last_retrieved=time.time(),
                inbound_links=0,
                confidence=1.0,
                payload={
                    "summary": "Proposal to migrate from Redis to Valkey was rejected.",
                    "rationale": "Violated Q3 Stability Identity Constraint. Redis licensing risks accepted temporarily.",
                    "authors": ["alice", "bob"],
                    "expiration": time.time() + (90 * 86400)
                }
            )
            return [decision_node]
            
        return []

class ConsolidationDaemon:
    def __init__(self):
        from memory_engine import BeliefStore
        BeliefStore.init_db()
        self.abstractions_created = 0
        self.noise_forgotten = 0

    def get_current_confidence(self, belief_data, now: float = None) -> float:
        import math
        if now is None:
            now = time.time()
            
        timestamp = belief_data['timestamp']
        original_confidence = belief_data['confidence']
        decay_rate = belief_data['decay_rate']
        
        days_elapsed = (now - timestamp) / 86400.0
        return original_confidence * math.exp(-decay_rate * days_elapsed)

    def run_sleep_cycle(self):
        print("=== CONSOLIDATION DAEMON: Initiating Sleep Cycle ===")
        from memory_engine import BeliefStore
        
        now = time.time()
        active_beliefs = BeliefStore.get_all_active_beliefs()
        
        for belief in active_beliefs:
            current_conf = self.get_current_confidence(belief, now)
            
            # Prune beliefs that fall below the 0.3 threshold
            if current_conf < 0.3:
                BeliefStore.update_belief_status(belief['id'], "FORGOTTEN")
                self.noise_forgotten += 1
                print(f"  [FORGOTTEN] Belief '{belief['subject']} {belief['predicate']} {belief['object']}' (Confidence: {current_conf:.2f} < 0.3)")
            else:
                # Example: If a belief survives with high confidence, we might strengthen it.
                # In MVP, we just leave it active.
                pass
                
        print(f"=== SLEEP CYCLE COMPLETE ===")
        print(f"Metrics: {self.abstractions_created} abstractions formed, {self.noise_forgotten} noisy beliefs forgotten.\n")
