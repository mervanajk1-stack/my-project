# -*- coding: utf-8 -*-
import sqlite3
import os
import hashlib
import secrets
from datetime import datetime, timedelta

DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.db"))


def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            max_accounts INTEGER NOT NULL DEFAULT 5,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            last_login TEXT
        );

        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            ip TEXT,
            user_agent TEXT,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS game_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            uid TEXT NOT NULL,
            password TEXT NOT NULL,
            region TEXT NOT NULL DEFAULT 'ME',
            mode TEXT NOT NULL DEFAULT 'admin',
            max_matches INTEGER NOT NULL DEFAULT 500,
            game_id TEXT,
            level INTEGER DEFAULT 1,
            exp INTEGER DEFAULT 0,
            last_exp INTEGER DEFAULT 0,
            nickname TEXT,
            status TEXT NOT NULL DEFAULT 'stopped',
            matches_played INTEGER DEFAULT 0,
            exp_gained INTEGER DEFAULT 0,
            last_match_at TEXT,
            created_at TEXT NOT NULL,
            started_at TEXT,
            stopped_at TEXT,
            UNIQUE(user_id, uid),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS login_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            ip TEXT,
            success INTEGER,
            created_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token);
        CREATE INDEX IF NOT EXISTS idx_accounts_user ON game_accounts(user_id);
        CREATE INDEX IF NOT EXISTS idx_attempts_ip ON login_attempts(ip, created_at);
    """)
    conn.commit()

    admin = c.execute("SELECT id FROM users WHERE username = ?", ("JAGWARxADMIN",)).fetchone()
    if not admin:
        pw_hash = hash_password("JAGWAR123")
        c.execute(
            "INSERT INTO users (username, password_hash, role, max_accounts, created_at) "
            "VALUES (?, ?, 'admin', 999999, ?)",
            ("JAGWARxADMIN", pw_hash, datetime.utcnow().isoformat())
        )
        conn.commit()
    conn.close()


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 200_000)
    return f"pbkdf2${salt}${h.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, salt, h = stored.split("$", 2)
        calc = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 200_000)
        return secrets.compare_digest(calc.hex(), h)
    except Exception:
        return False


def create_user(username, password, role='user', max_accounts=5):
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (username, password_hash, role, max_accounts, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (username, hash_password(password), role, max_accounts, datetime.utcnow().isoformat())
        )
        conn.commit()
        return True, "OK"
    except sqlite3.IntegrityError:
        return False, "Username already exists"
    finally:
        conn.close()


def get_user(username):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(uid):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (uid,)).fetchone()
    conn.close()
    return dict(row) if row else None


def list_users():
    conn = get_db()
    rows = conn.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_user(user_id):
    conn = get_db()
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()


def update_user(user_id, **kwargs):
    allowed = {'password_hash', 'max_accounts', 'is_active', 'role'}
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return
    sets = ", ".join(f"{k}=?" for k in fields)
    conn = get_db()
    conn.execute(f"UPDATE users SET {sets} WHERE id=?", (*fields.values(), user_id))
    conn.commit()
    conn.close()


def set_user_password(user_id, new_password):
    conn = get_db()
    conn.execute("UPDATE users SET password_hash=? WHERE id=?",
                 (hash_password(new_password), user_id))
    conn.commit()
    conn.close()


def create_session(user_id, token, ip, ua, expires_at):
    conn = get_db()
    conn.execute(
        "INSERT INTO sessions (user_id, token, ip, user_agent, created_at, expires_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, token, ip, ua, datetime.utcnow().isoformat(), expires_at)
    )
    conn.commit()
    conn.close()


def get_session(token):
    conn = get_db()
    row = conn.execute("SELECT * FROM sessions WHERE token = ?", (token,)).fetchone()
    conn.close()
    if not row:
        return None
    s = dict(row)
    if s['expires_at'] < datetime.utcnow().isoformat():
        delete_session(token)
        return None
    return s


def delete_session(token):
    conn = get_db()
    conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
    conn.commit()
    conn.close()


def delete_user_sessions(user_id):
    conn = get_db()
    conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def add_game_account(user_id, uid, password, region='ME', mode='admin', max_matches=500):
    conn = get_db()
    try:
        cur = conn.execute(
            "INSERT INTO game_accounts (user_id, uid, password, region, mode, max_matches, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, uid, password, region, mode, max_matches, datetime.utcnow().isoformat())
        )
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def list_game_accounts(user_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM game_accounts WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def count_game_accounts(user_id):
    conn = get_db()
    n = conn.execute("SELECT COUNT(*) FROM game_accounts WHERE user_id = ?", (user_id,)).fetchone()[0]
    conn.close()
    return n


def update_game_account(acc_id, **kwargs):
    allowed = {'status', 'level', 'exp', 'last_exp', 'nickname', 'matches_played',
               'exp_gained', 'last_match_at', 'started_at', 'stopped_at',
               'game_id', 'mode', 'max_matches'}
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return
    sets = ", ".join(f"{k}=?" for k in fields)
    conn = get_db()
    conn.execute(f"UPDATE game_accounts SET {sets} WHERE id=?", (*fields.values(), acc_id))
    conn.commit()
    conn.close()


def delete_game_account(acc_id):
    conn = get_db()
    conn.execute("DELETE FROM game_accounts WHERE id = ?", (acc_id,))
    conn.commit()
    conn.close()


def get_game_account(acc_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM game_accounts WHERE id = ?", (acc_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def reset_all_stopped():
    """عند إعادة تشغيل الموقع: كل الحسابات تصبح stopped"""
    conn = get_db()
    conn.execute("UPDATE game_accounts SET status='stopped'")
    conn.commit()
    conn.close()


def log_login_attempt(username, ip, success):
    conn = get_db()
    conn.execute(
        "INSERT INTO login_attempts (username, ip, success, created_at) VALUES (?, ?, ?, ?)",
        (username, ip, 1 if success else 0, datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()


def recent_failed_attempts(ip, minutes=15):
    since = (datetime.utcnow() - timedelta(minutes=minutes)).isoformat()
    conn = get_db()
    n = conn.execute(
        "SELECT COUNT(*) FROM login_attempts WHERE ip=? AND success=0 AND created_at > ?",
        (ip, since)
    ).fetchone()[0]
    conn.close()
    return n


def global_stats():
    conn = get_db()
    users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    accounts = conn.execute("SELECT COUNT(*) FROM game_accounts").fetchone()[0]
    running = conn.execute(
        "SELECT COUNT(*) FROM game_accounts WHERE status IN ('online','starting','reconnecting')"
    ).fetchone()[0]
    total_exp = conn.execute("SELECT COALESCE(SUM(exp_gained),0) FROM game_accounts").fetchone()[0]
    total_matches = conn.execute("SELECT COALESCE(SUM(matches_played),0) FROM game_accounts").fetchone()[0]
    conn.close()
    return {
        "users": users,
        "accounts": accounts,
        "running": running,
        "total_exp": total_exp,
        "total_matches": total_matches,
    }