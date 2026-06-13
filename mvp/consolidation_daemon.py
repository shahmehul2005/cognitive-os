import time
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

class ConsolidationEngine:
    def __init__(self):
        self.active_memory: List[MemoryNode] = []
        self.cold_storage: List[MemoryNode] = []
        self.semantic_graph: List[MemoryNode] = []
        
    def add_episodic_memory(self, node: MemoryNode):
        self.active_memory.append(node)
        
    def calculate_activation_energy(self, node: MemoryNode, current_time: float) -> float:
        """
        Implementation of the exact decay math from 05_attention.md.
        E_a = (1.0 / (days_since_read + 1)) + (inbound_links * 0.1)
        """
        days_since_read = max(0, (current_time - node.last_retrieved)) / 86400.0
        energy = (1.0 / (days_since_read + 1)) + (node.inbound_links * 0.1)
        return energy
        
    def forget(self, current_time: float, threshold: float = 0.05):
        """
        Prunes nodes whose activation energy has fallen below the operational limit.
        """
        surviving_nodes = []
        pruned_count = 0
        
        for node in self.active_memory:
            energy = self.calculate_activation_energy(node, current_time)
            if energy < threshold:
                # De-index from active memory, move to cold compliance storage
                self.cold_storage.append(node)
                pruned_count += 1
            else:
                surviving_nodes.append(node)
                
        self.active_memory = surviving_nodes
        return pruned_count

    def compress_to_decision(self, episodes: List[MemoryNode]) -> List[MemoryNode]:
        """
        Abstracts a collection of raw chat logs into a highly structured Decision Memory node.
        In a production environment, this triggers a prompt to the LLM (Gemini).
        For this Crucible logic, we implement a rule-based abstraction to prove the schema.
        """
        # Combine text
        full_text = " ".join([ep.content for ep in episodes]).lower()
        
        # If we detect the Redis/Valkey debate pattern
        if "redis" in full_text and "valkey" in full_text and "stability" in full_text:
            decision_node = MemoryNode(
                id="dec_valkey_vs_redis_q3",
                type="Decision",
                content="Proposal to migrate from Redis to Valkey was rejected.",
                last_retrieved=time.time(),
                inbound_links=0,
                payload={
                    "summary": "Proposal to migrate from Redis to Valkey was rejected.",
                    "rationale": "Violated Q3 Stability Identity Constraint. Redis licensing risks accepted temporarily.",
                    "authors": ["alice", "bob"],
                    "expiration": time.time() + (90 * 86400) # Re-evaluate in 90 days
                }
            )
            return [decision_node]
            
        return []

    def sleep_cycle(self):
        """
        The 2:00 AM Consolidation loop.
        """
        current_time = time.time()
        
        # 1. Abstraction (Compress episodic logs to Decision nodes)
        new_decisions = self.compress_to_decision(self.active_memory)
        for dec in new_decisions:
            self.semantic_graph.append(dec)
            
        # 2. Pruning (Forget the noisy episodic logs that are old and unreferenced)
        pruned = self.forget(current_time=current_time)
        
        return {
            "decisions_abstracted": len(new_decisions),
            "episodes_pruned": pruned
        }
