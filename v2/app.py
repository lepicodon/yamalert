import os
import json
import re
import yaml
import requests
from flask import Flask, jsonify, request, render_template, Response
from typing import Dict, Any, List

app = Flask(__name__)
# Load SECRET_KEY from env, fallback to None
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', None)

rules_file_path = os.path.join(os.path.dirname(__file__), 'rules.json')

# =============================================================================
# VALIDATION LOGIC
# =============================================================================

def is_promql_syntax_valid(expr: str) -> (bool, str):
    if not expr or not expr.strip():
        return False, "Empty expression"
    
    # Reject control characters
    if re.search(r'[\x00-\x1f]', expr):
        return False, "Contains invalid control characters"

    # State tracking
    brace_balance = 0    # {}
    bracket_balance = 0  # []
    paren_balance = 0    # ()
    in_string = None     # ' or "
    escape = False
    
    # For checking balanced pairs
    last_char = ''
    
    for i, ch in enumerate(expr):
        if escape:
            escape = False
            continue
            
        if ch == '\\':
            escape = True
            continue
            
        # String handling
        if in_string:
            if ch == in_string:
                in_string = None
            continue
        elif ch == '"' or ch == "'":
            in_string = ch
            continue
        elif ch == '`':
            # Backticks can also be strings in some contexts or future promql, 
            # generally treat as string-like to be safe or reject? 
            # Standard PromQL uses " or ' for labels. 
            # We'll treat it as string delimiter to avoid parsing content inside.
            in_string = ch
            continue

        # Delimiters
        if ch == '{':
            if brace_balance > 0: # Nested braces usually invalid in selector, but valid in subquery templates? keeping simple check.
                pass 
            brace_balance += 1
        elif ch == '}':
            brace_balance -= 1
            if brace_balance < 0: return False, f"Unexpected closing brace '}}' at position {i}"
        
        elif ch == '[':
            bracket_balance += 1
        elif ch == ']':
            bracket_balance -= 1
            if bracket_balance < 0: return False, f"Unexpected closing bracket ']' at position {i}"
            
        elif ch == '(':
            paren_balance += 1
        elif ch == ')':
            paren_balance -= 1
            if paren_balance < 0: return False, f"Unexpected closing parenthesis ')' at position {i}"
    
    # Final checks
    if in_string:
        return False, "Unclosed string literal"
    if brace_balance != 0:
        return False, "Unclosed braces {}"
    if bracket_balance != 0:
        return False, "Unclosed brackets []"
    if paren_balance != 0:
        return False, "Unclosed parentheses ()"

    # Heuristics for common errors
    # 1. Empty selector: {} inside a metric name is valid, but strictly empty like `metric{}` is okay. 
    #    However `{}{...}` is invalid.
    # 2. Comparison operator at start/end
    stripped = expr.strip()
    if re.match(r'^[=<>!]', stripped):
        return False, "Expression cannot start with a comparison operator"
    if re.search(r'[=<>!]$', stripped):
        return False, "Expression cannot end with a comparison operator"
        
    return True, ""

def validate_prometheus_rules(doc: Dict[str, Any]) -> List[str]:
    errors = []
    if not isinstance(doc, dict):
        return ["Prometheus rules must be a dict"]
    if "groups" not in doc:
        errors.append("Missing 'groups' key")
        return errors
    if not isinstance(doc["groups"], list):
        errors.append("'groups' must be a list")
        return errors
    for i, g in enumerate(doc["groups"], start=1):
        if not isinstance(g, dict):
            errors.append(f"Group #{i} must be a dict")
            continue
        if "name" not in g:
            errors.append(f"Group #{i} missing 'name'")
        if "rules" not in g:
            errors.append(f"Group #{i} missing 'rules'")
            continue
        if not isinstance(g["rules"], list):
            errors.append(f"Group #{i} 'rules' must be a list")
            continue
        for j, r in enumerate(g["rules"], start=1):
            if not isinstance(r, dict):
                errors.append(f"Group #{i} Rule #{j} must be a dict")
                continue
            if "expr" not in r:
                errors.append(f"Group #{i} Rule #{j} missing 'expr'")
            else:
                expr = r.get("expr") or ""
                is_valid, err_msg = is_promql_syntax_valid(expr)
                if not is_valid:
                    errors.append(f"Group #{i} Rule #{j} invalid PromQL: {err_msg}")
    return errors


def load_yaml(content: str):
    try:
        return yaml.safe_load(content)
    except Exception as e:
        raise ValueError(f"Invalid YAML: {e}")

# =============================================================================
# DATA PERSISTENCE
# =============================================================================

def load_rules():
    if not os.path.exists(rules_file_path):
        return []
    try:
        with open(rules_file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading rules.json: {e}")
        return []



# =============================================================================
# ROUTES
# =============================================================================

@app.route("/")
def index():
    # Parse PROMETHEUS_URLS from env (comma-separated)
    env_urls = os.environ.get('PROMETHEUS_URLS', 'Local Prometheus|http://localhost:9090')
    raw_list = [u.strip() for u in env_urls.split(',') if u.strip()]
    prom_urls = []
    
    for item in raw_list:
        parts = item.split('|', 1)
        if len(parts) == 2:
            prom_urls.append({"name": parts[0].strip(), "url": parts[1].strip()})
        else:
            prom_urls.append({"name": item, "url": item})
            
    return render_template("index.html", prom_urls=prom_urls)

@app.get("/api/templates")
def api_templates():
    rules = load_rules()
    return jsonify(rules)



@app.post("/api/reload")
def api_reload():
    # Since we load on every request in this simple implementation,
    # this might just confirm access or be a no-op if caching was used.
    # For now, just return OK.
    _ = load_rules()
    return jsonify({"status": "reloaded"})

@app.post("/api/validate/yaml")
def api_validate_yaml():
    data = request.get_json(force=True, silent=True) or {}
    content = data.get("content", "")
    
    try:
        doc = load_yaml(content)
    except ValueError as ve:
        return jsonify({"valid": False, "errors": [str(ve)], "promql_checked": 0, "promql_invalid": 0})
        
    promql_checked = 0
    promql_invalid = 0
    
    # Always validate as Prometheus Rules now
    errs = validate_prometheus_rules(doc)
    
    # Scan for PromQL
    if isinstance(doc, dict) and "groups" in doc:
        for g in doc["groups"]:
            if isinstance(g, dict) and "rules" in g:
                for r in g["rules"]:
                    if isinstance(r, dict) and "expr" in r:
                        promql_checked += 1
                        is_valid, _ = is_promql_syntax_valid(r["expr"])
                        if not is_valid:
                            promql_invalid += 1
        
    return jsonify({
        "valid": len(errs) == 0 and promql_invalid == 0,
        "errors": errs,
        "promql_checked": promql_checked,
        "promql_invalid": promql_invalid
    })

@app.post("/api/proxy/promql")
def api_proxy_promql():
    data = request.get_json(force=True, silent=True) or {}
    prom_url = data.get("url", "").rstrip("/")
    query = data.get("query", "")
    
    if not prom_url or not query:
        return jsonify({"valid": False, "error": "Missing URL or Query"}), 400
        
    try:
        # Simple proxy to Prometheus API
        # Timeout set to 5s to avoid hanging
        resp = requests.get(f"{prom_url}/api/v1/query", params={"query": query}, timeout=5)
        resp.raise_for_status()
        return jsonify({"valid": True, "data": resp.json()})
    except requests.exceptions.RequestException as e:
        return jsonify({"valid": False, "error": str(e)}), 502

@app.post("/api/validate/promql")
def api_validate_promql():
    data = request.get_json(force=True, silent=True) or {}
    expr = data.get("expr", "")
    ok, msg = is_promql_syntax_valid(expr)
    return jsonify({"valid": ok, "error": msg})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
