import os
import json
import re
import yaml
import requests
import sqlite3
from flask import Flask, jsonify, request, render_template, session
from typing import Any
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Load SECRET_KEY from env, fallback
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-yamalert-secret-key')

# Database initialization
db_path = os.path.join(os.path.dirname(__file__), 'data', 'rules.db')
defaults_json_path = os.path.join(os.path.dirname(__file__), 'data', 'defaults.json')

def get_db():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db_exists = os.path.exists(db_path)
    
    if not os.path.exists(os.path.dirname(db_path)):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS rules (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            job TEXT NOT NULL,
            description TEXT,
            alert_types TEXT, -- JSON string of list
            rules_json TEXT   -- JSON string of list of rule objects
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    ''')
    
    # Seeding logic: only if the DB file did not exist before
    if not db_exists and os.path.exists(defaults_json_path):
        print("Seeding database with default rules from defaults.json...")
        try:
            with open(defaults_json_path, 'r') as f:
                seed_data = json.load(f)
                for item in seed_data:
                    # Standardize on Group format for DB consistency
                    group_data = {
                        "name": item.get('name'),
                        "rules": item.get('rules', [])
                    }
                    conn.execute('''
                        INSERT INTO rules (id, name, job, description, alert_types, rules_json)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        item.get('id'),
                        item.get('name'),
                        item.get('job'),
                        item.get('description', ''),
                        json.dumps(item.get('alert_types', [])),
                        json.dumps(group_data)
                    ))
            conn.commit()
        except Exception as e:
            print(f"Seeding failed: {e}")
    conn.close()

init_db()

# Auth Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated_function


# =============================================================================
# VALIDATION LOGIC
# =============================================================================

def is_promql_syntax_valid(expr: str) -> tuple[bool, str]:
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

def validate_prometheus_rules(doc: dict[str, Any]) -> list[str]:
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
    conn = get_db()
    rows = conn.execute('SELECT * FROM rules ORDER BY name ASC').fetchall()
    conn.close()
    
    rules = []
    for r in rows:
        rules_json = json.loads(r['rules_json'] or '{}')
        
        # Everything is a group in v3
        group_meta = {k: v for k, v in rules_json.items() if k != 'rules'}
        actual_rules = rules_json.get('rules', [])
            
        rules.append({
            "id": r['id'],
            "name": r['name'],
            "job": r['job'],
            "description": r['description'],
            "alert_types": json.loads(r['alert_types'] or '[]'),
            "rules": actual_rules,
            "group_meta": group_meta
        })
    return rules



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
    return jsonify(load_rules())

# =============================================================================
# ADMIN ROUTES
# =============================================================================

@app.get("/api/admin/setup-required")
def api_admin_setup_required():
    conn = get_db()
    res = conn.execute("SELECT value FROM settings WHERE key='admin_password'").fetchone()
    conn.close()
    return jsonify({"setup_required": res is None})

@app.post("/api/admin/setup")
def api_admin_setup():
    conn = get_db()
    existing = conn.execute("SELECT value FROM settings WHERE key='admin_password'").fetchone()
    if existing:
        conn.close()
        return jsonify({"error": "Admin already configured"}), 400
        
    data = request.get_json(force=True, silent=True) or {}
    password = data.get("password")
    if not password or len(password) < 4:
        conn.close()
        return jsonify({"error": "Password too short (min 4 chars)"}), 400
        
    hashed = generate_password_hash(password)
    conn.execute("INSERT INTO settings (key, value) VALUES (?, ?)", ("admin_password", hashed))
    conn.commit()
    conn.close()
    
    session['admin_logged_in'] = True
    return jsonify({"status": "ok"})

@app.post("/api/admin/login")
def api_admin_login():
    data = request.get_json(force=True, silent=True) or {}
    password = data.get("password")
    
    conn = get_db()
    res = conn.execute("SELECT value FROM settings WHERE key='admin_password'").fetchone()
    conn.close()
    
    if res and check_password_hash(res['value'], password):
        session['admin_logged_in'] = True
        return jsonify({"status": "ok"})
        
    return jsonify({"error": "Invalid password"}), 401

@app.post("/api/admin/logout")
def api_admin_logout():
    session.pop('admin_logged_in', None)
    return jsonify({"status": "ok"})

@app.get("/api/admin/status")
def api_admin_status():
    return jsonify({"logged_in": bool(session.get('admin_logged_in'))})

@app.post("/api/admin/rules")
@login_required
def api_admin_create_rule():
    data = request.get_json(force=True, silent=True) or {}
    
    # 1. Server-side Validation
    rules_data = data.get("rules_logic") # Full group object
    if not isinstance(rules_data, dict):
        return jsonify({"error": "Invalid data format. Expected a group object."}), 400
    
    doc = {"groups": [rules_data]}
    
    errs = validate_prometheus_rules(doc)
    
    if errs:
        return jsonify({"valid": False, "errors": errs}), 400

    # 2. Prepare entry
    name = data.get("name", "New Rule")
    job = data.get("job", "job-name")
    desc = data.get("description", "")
    alert_types = data.get("alert_types", ["email","interlink"])
    
    tid = name.lower().replace(" ", "_").replace("/", "_")
    
    conn = get_db()
    # Check uniqueness
    existing = conn.execute('SELECT id FROM rules WHERE id = ?', (tid,)).fetchone()
    if existing:
        tid = f"{tid}_{int(os.urandom(2).hex(), 16)}"

    try:
        conn.execute('''
            INSERT INTO rules (id, name, job, description, alert_types, rules_json)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (tid, name, job, desc, json.dumps(alert_types), json.dumps(rules_data)))
        conn.commit()
        return jsonify({"status": "ok", "id": tid})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.put("/api/admin/rules/<tid>")
@login_required
def api_admin_update_rule(tid):
    data = request.get_json(force=True, silent=True) or {}
    
    # 1. Validation
    rules_data = data.get("rules_logic")
    if not isinstance(rules_data, dict):
        return jsonify({"error": "Invalid data format. Expected a group object."}), 400
        
    doc = {"groups": [rules_data]}
        
    errs = validate_prometheus_rules(doc)
    
    if errs:
        return jsonify({"valid": False, "errors": errs}), 400

    conn = get_db()
    try:
        conn.execute('''
            UPDATE rules SET name=?, job=?, description=?, alert_types=?, rules_json=?
            WHERE id=?
        ''', (
            data.get("name"), 
            data.get("job"), 
            data.get("description"), 
            json.dumps(data.get("alert_types", [])),
            json.dumps(rules_data),
            tid
        ))
        conn.commit()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.delete("/api/admin/rules/<tid>")
@login_required
def api_admin_delete_rule(tid):
    conn = get_db()
    try:
        conn.execute('DELETE FROM rules WHERE id = ?', (tid,))
        conn.commit()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()



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

if __name__ == "__main__":
    app.run(debug=True, port=5000)
