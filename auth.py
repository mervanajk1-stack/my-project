# -*- coding: utf-8 -*-
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import session, redirect, url_for, request, abort, g
from database import get_session, create_session, delete_session, get_user_by_id

SESSION_COOKIE = "ego_session"
SESSION_LIFETIME_HOURS = 12


def login_user(user_id, ip, ua):
    token = secrets.token_urlsafe(48)
    expires = (datetime.utcnow() + timedelta(hours=SESSION_LIFETIME_HOURS)).isoformat()
    create_session(user_id, token, ip, ua, expires)
    session[SESSION_COOKIE] = token
    session.permanent = True
    return token


def logout_user():
    token = session.get(SESSION_COOKIE)
    if token:
        delete_session(token)
    session.clear()


def current_user():
    if hasattr(g, "_current_user"):
        return g._current_user
    token = session.get(SESSION_COOKIE)
    if not token:
        g._current_user = None
        return None
    s = get_session(token)
    if not s:
        g._current_user = None
        return None
    user = get_user_by_id(s['user_id'])
    if not user or not user.get('is_active'):
        g._current_user = None
        return None
    g._current_user = user
    return user


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user():
            return redirect(url_for('login_page', next=request.path))
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        u = current_user()
        if not u:
            return redirect(url_for('login_page', next=request.path))
        if u.get('role') != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return wrapper