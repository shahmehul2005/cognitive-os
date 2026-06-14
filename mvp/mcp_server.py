import sys
import json
import os
import traceback

sys.path.append(os.path.dirname(__file__))
from memory_engine import get_connection

def respond(message_id, result=None, error=None):
    response = {"jsonrpc": "2.0", "id": message_id}
    if error:
        response["error"] = error
    else:
        response["result"] = result
    print(json.dumps(response), flush=True)

def handle_request(req):
    method = req.get("method")
    params = req.get("params", {})
    req_id = req.get("id")

    if method == "initialize":
        respond(req_id, {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "cognitive-os-mcp",
                "version": "1.0.0"
            }
        })
    elif method == "notifications/initialized":
        pass
    elif method == "tools/list":
        respond(req_id, {
            "tools": [
                {
                    "name": "query_beliefs",
                    "description": "Query the cognitive organism's belief graph.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query_type": {
                                "type": "string",
                                "description": "Type of belief (e.g. SEMANTIC, EPISODIC, DECISION, TASK)"
                            },
                            "limit": {
                                "type": "integer",
                                "default": 50
                            }
                        }
                    }
                },
                {
                    "name": "get_recent_decisions",
                    "description": "Get recent decisions made by the cognitive OS.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "limit": {
                                "type": "integer",
                                "default": 10
                            }
                        }
                    }
                }
            ]
        })
    elif method == "tools/call":
        tool_name = params.get("name")
        tool_args = params.get("arguments", {})
        
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            if tool_name == "query_beliefs":
                query_type = tool_args.get("query_type")
                limit = tool_args.get("limit", 50)
                
                if query_type:
                    cursor.execute("SELECT id, content, confidence, type, status, created_at FROM beliefs WHERE type = ? ORDER BY created_at DESC LIMIT ?", (query_type, limit))
                else:
                    cursor.execute("SELECT id, content, confidence, type, status, created_at FROM beliefs ORDER BY created_at DESC LIMIT ?", (limit,))
                
                rows = cursor.fetchall()
                beliefs = [{"id": r[0], "content": r[1], "confidence": r[2], "type": r[3], "status": r[4], "created_at": r[5]} for r in rows]
                
                respond(req_id, {
                    "content": [{"type": "text", "text": json.dumps(beliefs, indent=2)}]
                })
                
            elif tool_name == "get_recent_decisions":
                limit = tool_args.get("limit", 10)
                cursor.execute("SELECT id, content, created_at FROM beliefs WHERE type = 'DECISION' ORDER BY created_at DESC LIMIT ?", (limit,))
                rows = cursor.fetchall()
                decisions = [{"id": r[0], "content": r[1], "timestamp": r[2]} for r in rows]
                
                respond(req_id, {
                    "content": [{"type": "text", "text": json.dumps(decisions, indent=2)}]
                })
            else:
                respond(req_id, error={"code": -32601, "message": "Method not found"})
                
            conn.close()
        except Exception as e:
            respond(req_id, error={"code": -32000, "message": str(e)})
            
    else:
        if req_id:
            respond(req_id, error={"code": -32601, "message": "Method not found"})

def main():
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            req = json.loads(line)
            handle_request(req)
        except json.JSONDecodeError:
            pass
        except Exception as e:
            print(json.dumps({"error": str(e)}), file=sys.stderr)

if __name__ == "__main__":
    main()
