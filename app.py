# -*- coding: utf-8 -*-
import os
import re
import time
from datetime import datetime, timedelta, timezone
from flask import (Flask, render_template, request, redirect, url_for,
                   jsonify, abort, session)
from werkzeug.middleware.proxy_fix import ProxyFix

import database as db
from auth import (login_user, logout_user, current_user,
                  login_required, admin_required)
from bot_engine import bot_manager

_BOOT_TIME = time.time()


def utcnow_iso():
    """Timezone-aware UTC timestamp in ISO format (no deprecation warning)."""
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat()


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(48).hex()
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("HTTPS_ONLY", "0") == "1",
    PERMANENT_SESSION_LIFETIME=timedelta(hours=12),
    MAX_CONTENT_LENGTH=8 * 1024 * 1024,
)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

REGION = "ME"


@app.after_request
def apply_headers(resp):
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "same-origin"
    resp.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com "
        "https://cdnjs.cloudflare.com; "
        "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com data:; "
        "script-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; base-uri 'self'; form-action 'self';"
    )
    return resp


def client_ip():
    return (request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            or request.remote_addr or "0.0.0.0")


def is_rate_limited(ip):
    return db.recent_failed_attempts(ip, minutes=15) >= 8


USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{3,32}$")


# ==================== PUBLIC ====================
@app.route("/")
def landing():
    stats = db.global_stats()
    return render_template("landing.html", stats=stats)


@app.route("/login", methods=["GET", "POST"])
def login_page():
    if current_user():
        return redirect(url_for("dashboard"))
    ip = client_ip()
    if request.method == "POST":
        if is_rate_limited(ip):
            return render_template("login.html",
                                   error="Too many failed attempts. Try again in 15 minutes.",
                                   next=request.args.get("next", ""))
        username = (request.form.get("username") or "").strip()
        password = (request.form.get("password") or "").strip()
        if not USERNAME_RE.match(username) or len(password) < 3:
            db.log_login_attempt(username, ip, False)
            return render_template("login.html", error="Invalid credentials.",
                                   next=request.args.get("next", ""))
        user = db.get_user(username)
        if not user or not user.get("is_active") or \
                not db.verify_password(password, user["password_hash"]):
            db.log_login_attempt(username, ip, False)
            return render_template("login.html", error="Invalid username or password.",
                                   next=request.args.get("next", ""))
        login_user(user["id"], ip, request.headers.get("User-Agent", ""))
        db.log_login_attempt(username, ip, True)
        try:
            conn = db.get_db()
            conn.execute("UPDATE users SET last_login=? WHERE id=?",
                         (utcnow_iso(), user["id"]))
            conn.commit()
            conn.close()
        except Exception:
            pass
        nxt = request.args.get("next")
        if nxt and nxt.startswith("/") and not nxt.startswith("//"):
            return redirect(nxt)
        return redirect(url_for("admin_panel" if user["role"] == "admin" else "dashboard"))
    return render_template("login.html", error=None, next=request.args.get("next", ""))


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("landing"))


# ==================== DASHBOARD ====================
@app.route("/dashboard")
@login_required
def dashboard():
    u = current_user()
    accounts = db.list_game_accounts(u["id"])
    return render_template(
        "dashboard.html",
        user=u,
        accounts=accounts,
        stats=db.global_stats(),
        quota_used=len(accounts),
        quota_max=u["max_accounts"],
    )


# ==================== ADD ACCOUNT ====================
@app.route("/add_account", methods=["GET", "POST"])
@login_required
def add_account():
    u = current_user()
    used = db.count_game_accounts(u["id"])
    max_allowed = u["max_accounts"]

    if request.method == "POST":
        mode = request.form.get("mode", "single")
        account_mode = (request.form.get("account_mode") or "admin").lower()
        if account_mode not in ("admin", "risk"):
            account_mode = "admin"
        max_matches = 500 if account_mode == "admin" else 999999999

        added = 0
        duplicates = 0
        invalid = 0

        if mode == "single":
            uid = (request.form.get("uid") or "").strip()
            password = (request.form.get("password") or "").strip()
            if not uid or not password:
                return jsonify({"ok": False, "error": "UID and password are required"}), 400
            if used + 1 > max_allowed:
                return jsonify({"ok": False, "error": "Account quota reached"}), 400
            aid = db.add_game_account(u["id"], uid, password, REGION, account_mode, max_matches)
            if aid:
                added += 1
            else:
                duplicates += 1

        elif mode == "bulk":
            file = request.files.get("file")
            if not file:
                return jsonify({"ok": False, "error": "No file uploaded"}), 400
            raw = file.read().decode("utf-8", errors="ignore")
            lines = [ln.strip() for ln in raw.splitlines() if ln.strip() and not ln.startswith("#")]
            parsed = []
            for ln in lines:
                if ":" not in ln:
                    invalid += 1
                    continue
                uid, pw = ln.split(":", 1)
                uid, pw = uid.strip(), pw.strip()
                if not uid or not pw:
                    invalid += 1
                    continue
                parsed.append((uid, pw))
            remaining = max_allowed - used
            for uid, pw in parsed[:remaining]:
                aid = db.add_game_account(u["id"], uid, pw, REGION, account_mode, max_matches)
                if aid:
                    added += 1
                else:
                    duplicates += 1
            if len(parsed) > remaining:
                invalid += len(parsed) - remaining

        return jsonify({"ok": True, "added": added, "duplicates": duplicates,
                        "invalid": invalid, "total": used + added})

    return render_template("add_account.html", user=u, quota_used=used, quota_max=max_allowed)


# ==================== ACCOUNT HELPERS ====================
def _own_account(u, aid):
    acc = db.get_game_account(aid)
    if not acc:
        return None
    if u["role"] != "admin" and acc["user_id"] != u["id"]:
        return None
    return acc


# ==================== ACCOUNT DETAIL PAGE ====================
@app.route("/account/<int:aid>")
@login_required
def account_detail(aid):
    u = current_user()
    acc = _own_account(u, aid)
    if not acc:
        abort(404)
    live = bot_manager.status(aid) or {}
    merged = dict(acc)
    merged.update({k: v for k, v in live.items() if v is not None})
    merged["active_matches"] = bot_manager.active_matches(aid)
    return render_template("account_detail.html", user=u, account=merged)


# ==================== ACCOUNT ACTIONS ====================
@app.route("/api/accounts/<int:aid>/start", methods=["POST"])
@login_required
def api_start_account(aid):
    u = current_user()
    acc = _own_account(u, aid)
    if not acc:
        return jsonify({"ok": False, "error": "Not found"}), 404
    bot_manager.start_account(acc)
    db.update_game_account(aid, status="starting",
                           started_at=utcnow_iso())
    return jsonify({"ok": True})


@app.route("/api/accounts/<int:aid>/stop", methods=["POST"])
@login_required
def api_stop_account(aid):
    u = current_user()
    acc = _own_account(u, aid)
    if not acc:
        return jsonify({"ok": False, "error": "Not found"}), 404
    bot_manager.stop_account(aid)
    db.update_game_account(aid, status="stopped",
                           stopped_at=utcnow_iso())
    return jsonify({"ok": True})


@app.route("/api/accounts/<int:aid>", methods=["DELETE"])
@login_required
def api_delete_account(aid):
    u = current_user()
    acc = _own_account(u, aid)
    if not acc:
        return jsonify({"ok": False, "error": "Not found"}), 404
    bot_manager.stop_account(aid)
    db.delete_game_account(aid)
    return jsonify({"ok": True})


@app.route("/api/accounts/<int:aid>/status")
@login_required
def api_account_status(aid):
    u = current_user()
    acc = _own_account(u, aid)
    if not acc:
        return jsonify({"ok": False, "error": "Not found"}), 404
    live = bot_manager.status(aid) or {}
    merged = dict(acc)
    merged.update({k: v for k, v in live.items() if v is not None})
    merged["active_matches"] = bot_manager.active_matches(aid)
    return jsonify({"ok": True, "account": merged})


@app.route("/api/accounts/<int:aid>/detail")
@login_required
def api_account_detail(aid):
    u = current_user()
    acc = _own_account(u, aid)
    if not acc:
        return jsonify({"ok": False, "error": "Not found"}), 404
    live = bot_manager.status(aid) or {}
    merged = dict(acc)
    merged.update({k: v for k, v in live.items() if v is not None})
    merged["active_matches"] = bot_manager.active_matches(aid)
    return jsonify({"ok": True, "account": merged})


@app.route("/api/accounts/start_all", methods=["POST"])
@login_required
def api_start_all():
    u = current_user()
    accounts = db.list_game_accounts(u["id"])
    started = 0
    for a in accounts:
        bot_manager.start_account(a)
        db.update_game_account(a["id"], status="starting",
                               started_at=utcnow_iso())
        started += 1
    return jsonify({"ok": True, "started": started})


@app.route("/api/accounts/stop_all", methods=["POST"])
@login_required
def api_stop_all():
    u = current_user()
    accounts = db.list_game_accounts(u["id"])
    ids = [a["id"] for a in accounts]
    bot_manager.stop_all(ids)
    for aid in ids:
        db.update_game_account(aid, status="stopped",
                               stopped_at=utcnow_iso())
    return jsonify({"ok": True, "stopped": len(ids)})


# ==================== STATS JSON API ====================
@app.route("/api/stats")
def api_stats():
    """إحصائيات الموقع كاملة بصيغة JSON"""
    stats = db.global_stats()
    return jsonify({
        "ok": True,
        "users": stats.get("users", 0),
        "accounts": stats.get("accounts", 0),
        "running": stats.get("running", 0),
        "total_exp": stats.get("total_exp", 0),
        "total_matches": stats.get("total_matches", 0),
        "uptime_seconds": int(time.time() - _BOOT_TIME),
    })


# ==================== ADMIN ====================
@app.route("/admin")
@admin_required
def admin_panel():
    u = current_user()
    users = db.list_users()
    conn = db.get_db()
    counts = dict(conn.execute(
        "SELECT user_id, COUNT(*) FROM game_accounts GROUP BY user_id"
    ).fetchall())
    conn.close()
    for usr in users:
        usr["account_count"] = counts.get(usr["id"], 0)
    return render_template("admin.html", user=u, users=users,
                           stats=db.global_stats())


@app.route("/api/admin/users", methods=["POST"])
@admin_required
def api_create_user():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()
    max_acc = data.get("max_accounts", 5)
    role = data.get("role", "user")
    if not USERNAME_RE.match(username):
        return jsonify({"ok": False, "error": "Invalid username (3-32 letters/digits)"}), 400
    if len(password) < 4:
        return jsonify({"ok": False, "error": "Password must be at least 4 characters"}), 400
    if role not in ("user", "admin"):
        role = "user"
    try:
        max_acc = max(1, min(int(max_acc), 999999))
    except Exception:
        max_acc = 5
    ok, msg = db.create_user(username, password, role=role, max_accounts=max_acc)
    if not ok:
        return jsonify({"ok": False, "error": msg}), 400
    return jsonify({"ok": True})


@app.route("/api/admin/users/<int:uid>", methods=["DELETE"])
@admin_required
def api_delete_user(uid):
    me = current_user()
    if uid == me["id"]:
        return jsonify({"ok": False, "error": "Cannot delete yourself"}), 400
    accounts = db.list_game_accounts(uid)
    bot_manager.stop_all([a["id"] for a in accounts])
    db.delete_user_sessions(uid)
    db.delete_user(uid)
    return jsonify({"ok": True})


@app.route("/api/admin/users/<int:uid>/password", methods=["POST"])
@admin_required
def api_reset_password(uid):
    data = request.get_json(silent=True) or {}
    pw = (data.get("password") or "").strip()
    if len(pw) < 4:
        return jsonify({"ok": False, "error": "Password too short"}), 400
    db.set_user_password(uid, pw)
    db.delete_user_sessions(uid)
    return jsonify({"ok": True})


@app.route("/api/admin/users/<int:uid>/quota", methods=["POST"])
@admin_required
def api_set_quota(uid):
    data = request.get_json(silent=True) or {}
    try:
        q = max(1, min(int(data.get("max_accounts", 5)), 999999))
    except Exception:
        return jsonify({"ok": False, "error": "Invalid number"}), 400
    db.update_user(uid, max_accounts=q)
    return jsonify({"ok": True})


@app.route("/api/admin/users/<int:uid>/toggle", methods=["POST"])
@admin_required
def api_toggle_user(uid):
    u = db.get_user_by_id(uid)
    if not u:
        return jsonify({"ok": False, "error": "Not found"}), 404
    new_state = 0 if u["is_active"] else 1
    db.update_user(uid, is_active=new_state)
    if not new_state:
        db.delete_user_sessions(uid)
        accounts = db.list_game_accounts(uid)
        bot_manager.stop_all([a["id"] for a in accounts])
    return jsonify({"ok": True, "is_active": bool(new_state)})


# ==================== ERROR HANDLERS ====================
@app.errorhandler(403)
def _403(e):
    return render_template("login.html", error="Access denied.", next=""), 403


@app.errorhandler(404)
def _404(e):
    return redirect(url_for("landing"))


# ==================== BOOT ====================
db.init_db()

# عند إعادة تشغيل الموقع: كل الحسابات تصبح stopped
try:
    db.reset_all_stopped()
    print("[BOOT] All account statuses reset to 'stopped'")
except Exception as e:
    print(f"[BOOT] Reset failed: {e}")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")),
            debug=False, threaded=True)
