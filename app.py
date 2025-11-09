# app.py
import os
import re
import json
import yaml
import bleach
from io import BytesIO
from typing import List, Optional, Dict, Any
from functools import wraps

from flask import Flask, jsonify, request, render_template, Response, redirect, url_for, flash
from flask_wtf.csrf import CSRFProtect, generate_csrf
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# Models
from models import Template, Admin, Base

# -----------------------------------------------------------------------------
# Database engine & session
# -----------------------------------------------------------------------------
DB_URL = os.environ.get("DATABASE_URL", "sqlite:///data/yamalert.db")

engine = create_engine(
    DB_URL,
    connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {},
    future=True,
)
SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False))
Base = None  # declarative base lives in models.py (not used directly)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-please-change-in-production')
app.config['WTF_CSRF_CHECK_DEFAULT'] = True
app.config['WTF_CSRF_ENABLED'] = True
csrf = CSRFProtect(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    db = SessionLocal()
    try:
        return db.query(Admin).get(int(user_id))
    finally:
        db.close()

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({"error": "Login required"}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.after_request
def after_request(response):
    # Ensure CSRF token is available
    if 'text/html' in response.headers.get('Content-Type', ''):
        response.set_cookie('csrf_token', generate_csrf())
    print("Response Headers:", dict(response.headers))
    return response


def sanitize_input(text: str, max_length: int = None) -> str:
    """Sanitize user input by removing HTML tags and limiting length."""
    if not text:
        return ""
    # Remove HTML tags and escape special characters
    cleaned = bleach.clean(text, tags=[], strip=True)
    # Optionally truncate
    if max_length and len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    return cleaned


# -----------------------------------------------------------------------------
# Utility helpers (PromQL / YAML validation, etc.) – unchanged
# -----------------------------------------------------------------------------
def load_yaml(content: str):
    try:
        return yaml.safe_load(content)
    except Exception as e:
        raise ValueError(f"Invalid YAML: {e}")


def is_promql_syntax_valid(expr: str) -> bool:
    # Basic sanity checks for PromQL-like expressions. We don't have a full
    # PromQL parser here, so be permissive but check for common structural
    # problems: control characters, unbalanced delimiters, and unclosed strings.
    if not expr or not expr.strip():
        return False

    # Reject control characters
    if re.search(r'[\x00-\x1f]', expr):
        return False

    brace = 0
    bracket = 0
    paren = 0
    in_string = None
    escape = False

    for ch in expr:
        if escape:
            escape = False
            continue
        if ch == '\\':
            escape = True
            continue
        if in_string:
            if ch == in_string:
                in_string = None
            continue
        if ch == '"' or ch == "'":
            in_string = ch
            continue
        if ch == '{':
            brace += 1
        elif ch == '}':
            brace -= 1
        elif ch == '[':
            bracket += 1
        elif ch == ']':
            bracket -= 1
        elif ch == '(':
            paren += 1
        elif ch == ')':
            paren -= 1
        if brace < 0 or bracket < 0 or paren < 0:
            return False

    if in_string is not None:
        return False
    if brace != 0 or bracket != 0 or paren != 0:
        return False

    # Minimal token check: must contain letters, digits, underscore, or colon
    if not re.search(r'[a-zA-Z0-9_:]', expr):
        return False

    return True


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
                if not is_promql_syntax_valid(expr):
                    errors.append(f"Group #{i} Rule #{j} has invalid PromQL: {expr}")
            if "alert" in r and not isinstance(r.get("alert"), str):
                errors.append(f"Group #{i} Rule #{j} 'alert' must be a string")
            if "record" in r and not isinstance(r.get("record"), str):
                errors.append(f"Group #{i} Rule #{j} 'record' must be a string")
            if "for" in r and not isinstance(r.get("for"), str):
                errors.append(f"Group #{i} Rule #{j} 'for' must be a string")
            if "labels" in r and not isinstance(r.get("labels"), dict):
                errors.append(f"Group #{i} Rule #{j} 'labels' must be a dict")
            if "annotations" in r and not isinstance(r.get("annotations"), dict):
                errors.append(f"Group #{i} Rule #{j} 'annotations' must be a dict")
    return errors


def validate_alertmanager_config(doc: Dict[str, Any]) -> List[str]:
    errors = []
    if not isinstance(doc, dict):
        return ["Alertmanager config must be a dict"]
    if "route" not in doc:
        errors.append("Missing 'route'")
    else:
        route = doc.get("route") or {}
        if not isinstance(route, dict):
            errors.append("'route' must be a dict")
        else:
            if "receiver" not in route:
                errors.append("Route missing 'receiver'")
    if "receivers" not in doc:
        errors.append("Missing 'receivers'")
    else:
        rcvs = doc.get("receivers") or []
        if not isinstance(rcvs, list):
            errors.append("'receivers' must be a list")
        else:
            names = set()
            for idx, r in enumerate(rcvs, start=1):
                if not isinstance(r, dict):
                    errors.append(f"Receiver #{idx} must be a dict")
                    continue
                if "name" not in r:
                    errors.append(f"Receiver #{idx} missing 'name'")
                else:
                    name = r.get("name")
                    if name in names:
                        errors.append(f"Duplicate receiver name '{name}'")
                    names.add(name)
            if "route" in doc and doc["route"].get("receiver"):
                if doc["route"]["receiver"] not in names:
                    errors.append(f"Route references unknown receiver '{doc['route']['receiver']}'")
    if "inhibit_rules" in doc:
        inh = doc.get("inhibit_rules")
        if not isinstance(inh, list):
            errors.append("'inhibit_rules' must be a list")
    return errors


def now_editor_state() -> Dict[str, Any]:
    return {
        "id": None,
        "name": "",
        "type": "rule",
        "job_category": "",
        "sensor_type": "",
        "description": "",
        "content": "groups: []",
    }


# -----------------------------------------------------------------------------
# Authentication routes
# -----------------------------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        db = SessionLocal()
        try:
            user = db.query(Admin).filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user)
                return redirect(url_for('index'))
            else:
                flash("Invalid username or password")
        finally:
            db.close()
    
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route("/setup-admin", methods=["GET", "POST"])
def setup_admin():
    db = SessionLocal()
    try:
        # Check if any admin exists
        if db.query(Admin).first():
            return "Admin already exists", 403
        
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")
            
            if not username or not password:
                return "Username and password required", 400
                
            admin = Admin(username=username)
            admin.set_password(password)
            db.add(admin)
            db.commit()
            return redirect(url_for('login'))
        
        return render_template("setup_admin.html")
    finally:
        db.close()

# -----------------------------------------------------------------------------
# Main routes
# -----------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.get("/api/templates")
def api_templates():
    db = SessionLocal()
    try:
        t = db.query(Template).order_by(
            Template.type.asc(),
            Template.job_category.asc(),
            Template.sensor_type.asc(),
            Template.name.asc(),
        ).all()
        result = []
        for x in t:
            has_alerts = False
            has_recordings = False
            alert_count = 0
            record_count = 0
            try:
                doc = yaml.safe_load(x.content or "")
                groups = doc.get("groups") if isinstance(doc, dict) else []
                if isinstance(groups, list):
                    for g in groups:
                        rules = g.get("rules") if isinstance(g, dict) else []
                        if isinstance(rules, list):
                            for r in rules:
                                if isinstance(r, dict):
                                    if "alert" in r:
                                        has_alerts = True
                                        alert_count += 1
                                    if "record" in r:
                                        has_recordings = True
                                        record_count += 1
            except Exception:
                # If parsing fails, default to False for both flags
                has_alerts = False
                has_recordings = False
                alert_count = 0
                record_count = 0

            result.append(
                {
                    "id": x.id,
                    "name": x.name,
                    "type": x.type,
                    "job_category": x.job_category,
                    "sensor_type": x.sensor_type,
                    "description": x.description or "",
                    "has_alerts": bool(has_alerts),
                    "has_recordings": bool(has_recordings),
                    "alert_count": alert_count,
                    "record_count": record_count,
                    "created_at": x.created_at.isoformat() if x.created_at else None,
                    "updated_at": x.updated_at.isoformat() if x.updated_at else None
                }
            )
        return jsonify(result)
    finally:
        db.close()


@app.delete("/api/template/<int:tid>")
@admin_required
def api_template_delete(tid: int):
    db = SessionLocal()
    try:
        t = db.query(Template).get(tid)
        if not t:
            return jsonify({"error": "not found"}), 404
        db.delete(t)
        db.commit()
        return jsonify({"status": "ok"})
    finally:
        db.close()

@app.get("/api/template/<int:tid>")
def api_template_get(tid: int):
    db = SessionLocal()
    try:
        t = db.query(Template).get(tid)
        if not t:
            return jsonify({"error": "not found"}), 404
        return jsonify(
            {
                "id": t.id,
                "name": t.name,
                "type": t.type,
                "job_category": t.job_category,
                "sensor_type": t.sensor_type,
                "description": t.description or "",
                "content": t.content,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "updated_at": t.updated_at.isoformat() if t.updated_at else None
            }
        )
    finally:
        db.close()


@app.post("/api/template")
@admin_required
def api_template_create():
    print("Received template creation request")
    try:
        data = request.get_json(force=True, silent=True) or {}
        print("Request data:", data)
    except Exception as e:
        print("Error parsing JSON:", str(e))
        return jsonify({"error": "Invalid JSON data"}), 400
    tid = data.get('id')
    name = sanitize_input(data.get("name", "").strip(), max_length=120)
    ttype = data.get("type", "rule")
    job_category = sanitize_input(data.get("job_category", ""), max_length=100)
    sensor_type = sanitize_input(data.get("sensor_type", ""), max_length=100)
    description = sanitize_input(data.get("description", ""))
    content = data.get("content", "")

    if not name:
        return jsonify({"error": "name is required"}), 400
    if ttype not in ("rule", "alertmanager"):
        return jsonify({"error": "invalid type"}), 400
    if not content:
        return jsonify({"error": "content is required"}), 400

    try:
        load_yaml(content)
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400

    db = SessionLocal()
    try:
        # If an id is provided, update the existing template instead of creating a new one
        if tid is not None:
            existing = db.query(Template).get(tid)
            if not existing:
                return jsonify({"error": "template not found"}), 404
            existing.name = name
            existing.type = ttype
            existing.job_category = job_category or None
            existing.sensor_type = sensor_type or None
            existing.description = description or None
            existing.content = content
            db.add(existing)
            db.commit()
            db.refresh(existing)
            return jsonify({"id": existing.id, "content_saved": bool(existing.content), "content_length": len(existing.content)})

        # Otherwise create a new template
        from datetime import datetime
        now = datetime.utcnow()
        t = Template(
            name=name,
            type=ttype,
            job_category=job_category or None,
            sensor_type=sensor_type or None,
            description=description or None,
            content=content,
            created_at=now,
            updated_at=now,
        )
        db.add(t)
        db.commit()
        db.refresh(t)
        return jsonify({"id": t.id, "content_saved": bool(t.content), "content_length": len(t.content)})
    finally:
        db.close()


@app.get("/api/state")
def api_state():
    if not hasattr(app, "_editor"):
        app._editor = now_editor_state()
    return jsonify(app._editor)


@app.post("/api/state")
def api_state_save():
    data = request.get_json(force=True, silent=True) or {}
    app._editor = {
        "id": data.get("id"),
        "name": data.get("name", ""),
        "type": data.get("type", "rule"),
        "job_category": data.get("job_category", ""),
        "sensor_type": data.get("sensor_type", ""),
        "description": data.get("description", ""),
        "content": data.get("content", "groups: []"),
    }
    return jsonify({"ok": True})


@app.post("/api/validate/yaml")
def api_validate_yaml():
    data = request.get_json(force=True, silent=True) or {}
    content = data.get("content", "")
    ttype = data.get("type", "rule")
    try:
        doc = load_yaml(content)
    except ValueError as ve:
        # YAML couldn't be parsed; return error plus promql summary zeros so the UI
        # can still show feedback.
        return jsonify({"valid": False, "errors": [str(ve)], "promql_checked": 0, "promql_invalid": 0})
    promql_checked = 0
    promql_invalid = 0
    if ttype == "rule":
        errs = validate_prometheus_rules(doc)
        # Scan rules for PromQL checks
        try:
            for g in (doc.get("groups") or []):
                for r in (g.get("rules") or []):
                    expr = r.get("expr") if isinstance(r, dict) else None
                    if expr:
                        promql_checked += 1
                        if not is_promql_syntax_valid(expr):
                            promql_invalid += 1
        except Exception:
            pass
    else:
        errs = validate_alertmanager_config(doc)
    return jsonify({"valid": len(errs) == 0, "errors": errs, "promql_checked": promql_checked, "promql_invalid": promql_invalid})


@app.post("/api/validate/promql")
def api_validate_promql():
    data = request.get_json(force=True, silent=True) or {}
    expr = data.get("expr", "")
    ok = is_promql_syntax_valid(expr)
    return jsonify({"valid": bool(ok)})


@app.get("/api/download")
def api_download():
    if not hasattr(app, "_editor"):
        app._editor = now_editor_state()
    st = app._editor
    name = st.get("name", "config")
    ttype = st.get("type", "rule")
    content = st.get("content", "")

    if ttype == "rule":
        ext = "rules.yml"
        ctype = "application/x-yaml"
    else:
        ext = "alertmanager.yml"
        ctype = "application/x-yaml"

    filename = f"{name}.{ext}".replace(" ", "_")
    return Response(
        content,
        mimetype=ctype,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": "text/plain; charset=utf-8",
        },
    )


# -----------------------------------------------------------------------------
# Startup
# -----------------------------------------------------------------------------
@app.teardown_appcontext
def remove_session(exc=None):
    SessionLocal.remove()


if __name__ == "__main__":
    # Create tables (models are defined in models.py)
    from models import Base
    Base.metadata.create_all(bind=engine)

    # Seed the default template library
    from seed_templates import seed_default_templates
    seed_default_templates()

    app.run(debug=True)
