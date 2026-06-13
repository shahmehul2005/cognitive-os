import json
import os
import time
import sqlite3
from memory_engine import get_connection

IDENTITY_FILE = os.path.join(os.path.dirname(__file__), "workspace_identity.json")

def load_identity():
    with open(IDENTITY_FILE, "r") as f:
        return json.load(f)

def Predict(current_state, action):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Query failures table
    cursor.execute("SELECT impact_severity FROM failures WHERE action_type = ?", (action["type"],))
    failures = cursor.fetchall()
    conn.close()
    
    total_failures = len(failures)
    
    # Simple transition prediction
    if total_failures == 0:
        success_probability = 0.95
        risk_index = 0.05
    else:
        success_probability = max(0.1, 1.0 - (total_failures / 10.0)) # scale down probability
        total_severity = sum(f[0] for f in failures)
        risk_index = min(1.0, total_severity / 10.0)
        
    next_state = current_state + f" -> executed({action['type']})"
    return {
        "next_state": next_state,
        "probability": success_probability,
        "risk": risk_index
    }

def SatisfiesConstraints(action, constraints):
    # Hard constraint check: security boundaries
    security = constraints.get("security", {})
    if action.get("requires_external_exec") and not security.get("allow_external_execution_without_approval"):
        return False
    return True

def CalculateEffectiveUtility(option, values):
    raw_utility = option["probability_of_success"] - option["risk_analysis"]["severity_score"]
    
    # Adjust by matching values
    multiplier = 1.0
    for val in values:
        # Simple string-match simulation
        if val["name"].lower() in str(option["steps"]).lower():
            multiplier += val.get("weight", 0.1)
            
    return raw_utility * multiplier

def Plan(target_state):
    identity = load_identity()
    constraints = identity["constraints"]
    current_state = "workspace_init"
    
    # Simulated options (Option A: slow/safe vs. Option B: fast/risky/bypassing checks)
    simulated_paths = [
        {
            "id": "option_A",
            "steps": [
                {"type": "create_local_branch", "requires_external_exec": False},
                {"type": "run_regression_tests", "requires_external_exec": False},
                {"type": "commit_changes", "requires_external_exec": False}
            ]
        },
        {
            "id": "option_B",
            "steps": [
                {"type": "direct_push_to_main", "requires_external_exec": True}, # requires external shell push bypass
                {"type": "hotfix_live_server", "requires_external_exec": True}
            ]
        }
    ]
    
    simulations = []
    
    for path in simulated_paths:
        path_probability = 1.0
        total_risk = 0.0
        is_valid = True
        
        for action in path["steps"]:
            # Hard constraint audit check
            if not SatisfiesConstraints(action, constraints):
                is_valid = False
                break
                
            prediction = Predict(current_state, action)
            path_probability *= prediction["probability"]
            total_risk += prediction["risk"]
            
        if is_valid:
            simulations.append({
                "option_id": path["id"],
                "steps": [s["type"] for s in path["steps"]],
                "probability_of_success": path_probability,
                "risk_analysis": {
                    "severity_score": total_risk,
                    "severity": "high" if total_risk > 0.4 else "low",
                    "description": f"Cumulative path risk is {total_risk:.2f}"
                }
            })
            
    # Calculate utilities
    for opt in simulations:
        opt["utility"] = CalculateEffectiveUtility(opt, identity["values"])
        
    simulations.sort(key=lambda x: x["utility"], reverse=True)
    recommendation = simulations[0]["option_id"] if simulations else None
    
    result = {
        "goal_id": target_state.get("goal_id", "goal_01"),
        "current_state": current_state,
        "target_state": target_state["description"],
        "simulations": simulations,
        "recommendation": recommendation
    }
    
    # Log committed decision
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO decision (decision_id, content, timestamp) VALUES (?, ?, ?)",
                   (str(uuid_uuid_ref := os.urandom(8).hex()), json.dumps(result), time.time()))
    conn.commit()
    conn.close()
    
    return result
