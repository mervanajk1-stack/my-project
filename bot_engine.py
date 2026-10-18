# -*- coding: utf-8 -*-
import sys
import os
os.environ['PYTHONUNBUFFERED'] = '1'
os.environ.setdefault('PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION', 'python')
try:
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
except Exception:
    pass

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import asyncio
import httpx
import random
import json
import socket
import struct
import time
import uuid
import itertools
import threading
from urllib.parse import urlsplit, urlunsplit
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

from google_play_scraper import app as play_scraper
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from message_ids import MESSAGE_ID_TO_NAME
import thunderFF_pb2

# ==================== CONFIGURATION ====================
START_MATCH_INTERVAL = 3.0
NEW_MATCH_DELAY = 3.0
MAX_MATCH_DURATION = 700
MATCH_IDLE_TIMEOUT = 8.0
NON_MATCH_RECONNECT_DELAY = 0.5
MAX_START_MATCH_ATTEMPTS = 30

BR_MODE_ID = 1
BR_MAP_ID = 1
LW_MODE_ID = 43
LW_MAP_ID = 11
LONE_WOLF_MIN_LEVEL = 3

ACCOUNT_REGION = "ME"

AES_KEY = b'Yg&tc%DEuh6%Zc^8'
AES_IV = b'6oyZDr22E3ychjM%'

REGION_SERVERS = {
    "IND": "https://clientbp.ppmainecoonghj.com/",
    "ID": "https://clientbp.ppmainecoonghj.com/",
    "BR": "https://clientbp.ppmainecoonghj.com/",
    "ME": "https://clientbp.ppmainecoonghj.com/",
    "VN": "https://clientbp.ppmainecoonghj.com/",
    "TH": "https://clientbp.ppmainecoonghj.com/",
    "CIS": "https://clientbp.ppmainecoonghj.com/",
    "BD": "https://clientbp.ppmainecoonghj.com/",
    "PK": "https://clientbp.ppmainecoonghj.com/",
    "SG": "https://clientbp.ppmainecoonghj.com/",
    "NA": "https://clientbp.ppmainecoonghj.com/",
    "SAC": "https://clientbp.ppmainecoonghj.com/",
    "EUROPE": "https://clientbp.ppmainecoonghj.com/",
    "TW": "https://clientbp.ppmainecoonghj.com/",
}

REGION_LANG = {
    "BD": "bn", "IND": "hi", "PK": "ur", "SG": "en", "ID": "id",
    "ME": "ar", "VN": "vi", "TW": "zh", "CIS": "ru", "TH": "th",
    "EU": "en", "US": "en", "SAC": "es", "LK": "en", "BR": "pt",
}

REGION_PREFIX = {
    "ME": "031900", "IND": "031400", "BD": "031400",
    "SG": "031500", "TH": "031500", "PH": "031500", "VN": "031500",
    "MY": "031500", "ID": "031500", "HK": "031500", "TW": "031500",
    "PK": "031500", "CIS": "031500", "BR": "031500", "NA": "031500",
    "SAC": "031500", "EUROPE": "031500",
}

CRC7_TABLE = bytes([
    0, 9, 18, 27, 36, 45, 54, 63, 72, 65, 90, 83, 108, 101, 126, 119,
    25, 16, 11, 2, 61, 52, 47, 38, 81, 88, 67, 74, 117, 124, 103, 110,
    50, 59, 32, 41, 22, 31, 4, 13, 122, 115, 104, 97, 94, 87, 76, 69,
    43, 34, 57, 48, 15, 6, 29, 20, 99, 106, 113, 120, 71, 78, 85, 92,
    100, 109, 118, 127, 64, 73, 82, 91, 44, 37, 62, 55, 8, 1, 26, 19,
    125, 116, 111, 102, 89, 80, 75, 66, 53, 60, 39, 46, 17, 24, 3, 10,
    86, 95, 68, 77, 114, 123, 96, 105, 30, 23, 12, 5, 58, 51, 40, 33,
    79, 70, 93, 84, 107, 98, 121, 112, 7, 14, 21, 28, 35, 42, 49, 56,
    65, 72, 83, 90, 101, 108, 119, 126, 9, 0, 27, 18, 45, 36, 63, 54,
    88, 81, 74, 67, 124, 117, 110, 103, 16, 25, 2, 11, 52, 61, 38, 47,
    115, 122, 97, 104, 87, 94, 69, 76, 59, 50, 41, 32, 31, 22, 13, 4,
    106, 99, 120, 113, 78, 71, 92, 85, 34, 43, 48, 57, 6, 15, 20, 29,
    37, 44, 55, 62, 1, 8, 19, 26, 109, 100, 127, 118, 73, 64, 91, 82,
    60, 53, 46, 39, 24, 17, 10, 3, 116, 125, 102, 111, 80, 89, 66, 75,
    23, 30, 5, 12, 51, 58, 33, 40, 95, 86, 77, 68, 123, 114, 105, 96,
    14, 7, 28, 21, 42, 35, 56, 49, 70, 79, 84, 93, 98, 107, 112, 121,
])

_DELTA = 0x9E3779B9
_ROUNDS = 16
_FIELD_SIZES = {0: 1, 1: 2, 2: 2, 3: 1, 4: 2}
_FIELD_NAMES = {0: "sendOption", 1: "cmd", 2: "orderId", 3: "flags", 4: "length"}

CLOUDFLARE_PRIMARY_DNS = "1.1.1.1"
CLOUDFLARE_SECONDARY_DNS = "1.0.0.1"
_DNS_CACHE: Dict[str, Tuple[str, float]] = {}
_DNS_CACHE_TTL = 300.0

client = httpx.AsyncClient(
    verify=False,
    timeout=15.0,
    limits=httpx.Limits(max_connections=300, max_keepalive_connections=150)
)
_LOGIN_SEMAPHORE = asyncio.Semaphore(max(1, int(os.getenv("REX_LOGIN_CONCURRENCY", "64"))))

headers = {
    'User-Agent': 'UnityPlayer/2018.4.12f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)',
    'Connection': 'Keep-Alive',
    'Accept-Encoding': 'gzip',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Expect': '100-continue',
    'X-Unity-Version': '2018.4.12f1',
    'X-GA-SV': '1789535859',
    'X-GA': 'v1 1',
    'ReleaseVersion': 'OB55'
}


class Colors:
    HEADER = '\033[95m'
    GREEN = '\033[92m'
    FAIL = '\033[91m'
    WARNING = '\033[93m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    WHITE = '\033[97m'
    ENDC = '\033[0m'


def print_colored(text, color=Colors.WHITE):
    try:
        print(f"{color}{text}{Colors.ENDC}", flush=True)
    except Exception:
        try:
            print(f"{color}{text.encode('ascii', errors='replace').decode('ascii')}{Colors.ENDC}", flush=True)
        except Exception:
            pass


def print_success(text): print_colored(f"[+] {text}", Colors.GREEN)
def print_error(text): print_colored(f"[-] {text}", Colors.FAIL)
def print_warning(text): print_colored(f"[!] {text}", Colors.WARNING)
def print_info(text): print_colored(f"[i] {text}", Colors.CYAN)
def log(msg): print(msg, flush=True)


# ==================== ACCOUNT CONTROLS ====================
CONTROL_FILE = os.environ.get(
    "ACCOUNT_CONTROLS_FILE",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "account_controls.json")
)
WORKER_PROFILES_FILE = os.environ.get(
    "WORKER_PROFILES_FILE",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "worker_profiles.json")
)
_CONTROL_CACHE = {}
_CONTROL_CACHE_SIGNATURE = None


def _account_controls_snapshot():
    global _CONTROL_CACHE, _CONTROL_CACHE_SIGNATURE
    try:
        st = os.stat(CONTROL_FILE)
        signature = (getattr(st, "st_mtime_ns", int(st.st_mtime * 1_000_000_000)), st.st_size)
        if signature != _CONTROL_CACHE_SIGNATURE:
            with open(CONTROL_FILE, "r", encoding="utf-8") as f:
                value = json.load(f)
            _CONTROL_CACHE = value if isinstance(value, dict) else {}
            _CONTROL_CACHE_SIGNATURE = signature
    except FileNotFoundError:
        _CONTROL_CACHE = {}
        _CONTROL_CACHE_SIGNATURE = None
    except Exception as exc:
        log(f"[CONTROL] Could not reload account controls: {type(exc).__name__}")
    return _CONTROL_CACHE


def account_control_state(uid):
    raw = _account_controls_snapshot().get(str(uid), {})
    return raw if isinstance(raw, dict) else {}


def account_is_paused(uid):
    return bool(account_control_state(uid).get("paused", False))


def account_is_deleted(uid):
    return bool(account_control_state(uid).get("deleted", False))


def account_restart_generation(uid):
    try:
        return int(account_control_state(uid).get("restart_generation", 0) or 0)
    except Exception:
        return 0


def persist_worker_profile(account_data):
    if not isinstance(account_data, dict):
        return
    uid = str(account_data.get("auth_uid") or "").strip()
    if not uid or account_is_deleted(uid):
        return
    try:
        try:
            with open(WORKER_PROFILES_FILE, "r", encoding="utf-8") as f:
                profiles = json.load(f)
            if not isinstance(profiles, dict): profiles = {}
        except Exception:
            profiles = {}
        previous = profiles.get(uid, {})
        if not isinstance(previous, dict): previous = {}
        history = previous.get("level_history", [])
        if not isinstance(history, list): history = []
        now = time.time()
        level = max(1, int(account_data.get("level", 1) or 1))
        exp = max(0, int(account_data.get("exp", 0) or 0))
        point = {"level": level, "exp": exp, "t": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now))}
        if not history or int(history[-1].get("level", -1)) != level or int(history[-1].get("exp", -1)) != exp:
            history.append(point)
            history = history[-60:]
        profile = {
            "uid": uid,
            "nickname": str(account_data.get("nickname") or previous.get("nickname") or "Unknown"),
            "level": level,
            "exp": exp,
            "likes": max(0, int(account_data.get("likes", previous.get("likes", 0)) or 0)),
            "region": str(account_data.get("region") or previous.get("region") or ACCOUNT_REGION),
            "updated_at": int(now),
            "level_history": history[-60:],
        }
        profiles[uid] = profile
        temp_path = WORKER_PROFILES_FILE + f".{os.getpid()}.tmp"
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(profiles, f, ensure_ascii=False, indent=2)
        try: os.chmod(temp_path, 0o600)
        except Exception: pass
        os.replace(temp_path, WORKER_PROFILES_FILE)
        try: os.chmod(WORKER_PROFILES_FILE, 0o600)
        except Exception: pass
    except Exception as exc:
        log(f"[PROFILE] Could not save dashboard snapshot for UID {uid}: {type(exc).__name__}")


# ==================== PROTOBUF HELPERS ====================
def get_proto_field(d, key, default=None):
    if not d or not isinstance(d, dict):
        return default
    if key in d:
        val = d[key].get('data')
        return val if val is not None else default
    if str(key) in d:
        val = d[str(key)].get('data')
        return val if val is not None else default
    return default


def _pb_varint(n):
    if n < 0:
        n = (1 << 64) + n
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            b |= 0x80
        out.append(b)
        if not n:
            break
    return bytes(out)


def _pb_tag(f, w):
    return _pb_varint((f << 3) | w)


def _pb_field(f, v):
    if isinstance(v, bool):
        v = int(v)
    if isinstance(v, int):
        return _pb_tag(f, 0) + _pb_varint(v)
    if isinstance(v, str):
        d = v.encode('utf-8')
        return _pb_tag(f, 2) + _pb_varint(len(d)) + d
    if isinstance(v, (bytes, bytearray)):
        d = bytes(v)
        return _pb_tag(f, 2) + _pb_varint(len(d)) + d
    return b""


def _generate_new_device() -> dict:
    device_list = [
        ("Samsung", "SM-G998B", "Adreno (TM) 660", "Android OS 12 / API-31"),
        ("Xiaomi", "2201122G", "Adreno (TM) 730", "Android OS 13 / API-33"),
        ("Realme", "RMX3700", "Mali-G710", "Android OS 14 / API-34"),
        ("OnePlus", "CPH2451", "Adreno (TM) 740", "Android OS 13 / API-33"),
        ("OPPO", "CPH2611", "Adreno (TM) 720", "Android OS 14 / API-34"),
        ("Vivo", "V2203", "Mali-G710", "Android OS 12 / API-31"),
        ("Poco", "M2102J20SG", "Adreno (TM) 660", "Android OS 13 / API-33"),
    ]
    brand, model, gpu, os_ver = random.choice(device_list)
    return {
        "unique_device_id": f"Google|{str(uuid.uuid4())}",
        "brand": brand, "model": model, "gpu_renderer": gpu, "system_software": os_ver,
        "screen_width": random.choice([1080, 1440, 720, 1280]),
        "screen_height": random.choice([2400, 3200, 1600, 2400]),
        "screen_dpi": str(random.randint(300, 420)),
        "memory": random.randint(2800, 6500),
        "processor_details": f"ARM64 FP ASIMD AES VMH | {random.randint(2200, 3200)} | {random.randint(6, 12)}",
        "client_ip": f"{random.randint(103, 223)}.{random.randint(10, 250)}.{random.randint(10, 250)}.{random.randint(10, 250)}"
    }


def get_device_for_account(account_identifier: str) -> dict:
    return _generate_new_device()


# ==================== DNS & SOCKET ====================
async def resolve_host_cloudflare(hostname: str) -> str:
    if not hostname:
        return hostname
    parts = hostname.split('.')
    if len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
        return hostname
    now = time.time()
    if hostname in _DNS_CACHE:
        ip, exp = _DNS_CACHE[hostname]
        if now < exp:
            return ip

    def _query_cloudflare(server_ip: str) -> Optional[str]:
        s = None
        try:
            tx_id = random.randint(1000, 65535)
            header = struct.pack(">HHHHHH", tx_id, 0x0100, 1, 0, 0, 0)
            qname = b"".join(bytes([len(part)]) + part.encode('ascii') for part in hostname.split('.')) + b"\x00"
            query_pkt = header + qname + struct.pack(">HH", 1, 1)
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(1.2)
            s.sendto(query_pkt, (server_ip, 53))
            resp, _ = s.recvfrom(1024)
            if len(resp) >= 12:
                ancount = struct.unpack(">H", resp[6:8])[0]
                if ancount > 0:
                    offset = 12 + len(qname) + 4
                    for _ in range(ancount):
                        if offset >= len(resp):
                            break
                        if (resp[offset] & 0xC0) == 0xC0:
                            offset += 2
                        else:
                            while offset < len(resp) and resp[offset] != 0:
                                offset += 1 + resp[offset]
                            offset += 1
                        if offset + 10 > len(resp):
                            break
                        rtype, rclass, ttl, rdlen = struct.unpack(">HHIH", resp[offset:offset + 10])
                        offset += 10
                        if rtype == 1 and rdlen == 4 and offset + 4 <= len(resp):
                            return socket.inet_ntoa(resp[offset:offset + 4])
                        offset += rdlen
        except Exception:
            pass
        finally:
            if s:
                try: s.close()
                except Exception: pass
        return None

    loop = asyncio.get_running_loop()
    ip = await loop.run_in_executor(None, _query_cloudflare, CLOUDFLARE_PRIMARY_DNS)
    if not ip:
        ip = await loop.run_in_executor(None, _query_cloudflare, CLOUDFLARE_SECONDARY_DNS)
    if not ip:
        try:
            ip_info = await loop.getaddrinfo(hostname, None, family=socket.AF_INET)
            if ip_info:
                ip = ip_info[0][4][0]
        except Exception:
            ip = hostname
    if ip:
        _DNS_CACHE[hostname] = (ip, now + _DNS_CACHE_TTL)
    return ip or hostname


def optimize_tcp_socket(sock: socket.socket):
    try:
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        if hasattr(socket, "SIO_KEEPALIVE_VALS") and os.name == 'nt':
            try: sock.ioctl(socket.SIO_KEEPALIVE_VALS, (1, 10000, 2000))
            except Exception: pass
        elif hasattr(socket, "TCP_KEEPIDLE"):
            try:
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 10)
                if hasattr(socket, "TCP_KEEPINTVL"):
                    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 2)
                if hasattr(socket, "TCP_KEEPCNT"):
                    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 5)
            except Exception: pass
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 131072)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 131072)
    except Exception:
        pass


def optimize_udp_socket(sock: socket.socket):
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 131072)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 131072)
        if hasattr(socket, 'SIO_UDP_CONNRESET') and os.name == 'nt':
            try: sock.ioctl(socket.SIO_UDP_CONNRESET, False)
            except Exception: pass
    except Exception:
        pass


# ==================== NETWORK/CRYPTO ====================
async def aes_encrypt(payload, key, iv):
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return cipher.encrypt(pad(payload, AES.block_size))


async def get_playstore_version():
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(
            None, lambda: play_scraper('com.dts.freefireth', lang='hi', country='id')
        )
        return result.get("version")
    except Exception:
        return "1.132.8"


async def version_config(region=None):
    app_version = await get_playstore_version()
    region = str(region or ACCOUNT_REGION or "ME").strip().upper()
    if region not in REGION_PREFIX:
        region = "ME"
    lang = REGION_LANG.get(region, "en")
    api_url = (
        "https://version.ggwhitehawk.com/live/ver.php"
        f"?version={app_version}"
        f"&lang={lang}&device=android&channel=android"
        f"&appstore=googleplay&region={region}"
        "&whitelist_version=1.3.0&whitelist_sp_version=1.0.0"
    )
    try:
        response = await client.get(api_url)
        response.raise_for_status()
        data = response.json()
        server_url = data.get("server_url")
        remote_version = data.get("remote_version")
        latest_release_version = data.get("latest_release_version")
        if not server_url or not remote_version or not latest_release_version:
            log(f"[LOGIN] Version config missing required fields for region {region}")
            return None
        return latest_release_version, remote_version, server_url
    except Exception as exc:
        log(f"[LOGIN] Version config failed for region {region}: {type(exc).__name__}: {exc}")
        return None


async def get_access_token(uid, password):
    url = "https://100067.connect.garena.com/oauth/guest/token/grant"
    hdrs = {
        "Host": "100067.connect.garena.com",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 12; SM-G998B Build/SP1A.210812.016)",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "close"
    }
    data = {
        "uid": uid, "password": password,
        "response_type": "token", "client_type": "2",
        "client_secret": "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3",
        "client_id": "100067"
    }
    for attempt in range(5):
        try:
            response = await client.post(url, headers=hdrs, data=data)
            if response.status_code == 200:
                response_data = response.json()
                open_id = response_data.get("open_id")
                access_token = response_data.get("access_token")
                platform = response_data.get("platform", 4)
                if open_id and access_token:
                    return open_id, access_token, platform
            if response.status_code == 429:
                await asyncio.sleep(1)
                continue
        except Exception:
            pass
        await asyncio.sleep(0.5)
    return None


# ======================================================================
# ⚡ ROBUST PROTOBUF DECODER — يدعم كل wire types (0,1,2,5)
# ======================================================================
async def _read_varint(buf, pos):
    result = 0
    shift = 0
    while pos < len(buf):
        b = buf[pos]
        pos += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            return result, pos
        shift += 7
        if shift > 70:
            raise ValueError("varint too long")
    raise ValueError("truncated varint")


async def _parse_protobuf_fields(buf, depth=0, max_depth=10):
    if depth > max_depth:
        return {}
    result = {}
    pos = 0
    n = len(buf)
    while pos < n:
        try:
            key, pos = await _read_varint(buf, pos)
        except Exception:
            break
        field_num = key >> 3
        wire_type = key & 0x07
        if field_num == 0:
            break
        try:
            if wire_type == 0:
                value, pos = await _read_varint(buf, pos)
                result[str(field_num)] = {"wire_type": "varint", "data": value}

            elif wire_type == 1:
                if pos + 8 > n:
                    break
                raw = buf[pos:pos + 8]
                pos += 8
                int_val = struct.unpack("<Q", raw)[0]
                entry = {"wire_type": "fixed64", "data": int_val, "raw_hex": raw.hex()}
                try:
                    txt = raw.rstrip(b'\x00').decode('utf-8', 'ignore')
                    if txt and all(32 <= ord(c) < 127 or c in '\r\n\t' for c in txt):
                        entry["string"] = txt
                except Exception:
                    pass
                result[str(field_num)] = entry

            elif wire_type == 2:
                length, pos = await _read_varint(buf, pos)
                if length < 0 or pos + length > n:
                    break
                raw = buf[pos:pos + length]
                pos += length
                nested = {}
                if length > 0:
                    try:
                        nested = await _parse_protobuf_fields(raw, depth + 1, max_depth)
                    except Exception:
                        nested = {}
                entry = {
                    "wire_type": "length_delimited",
                    "data": nested if nested else raw.hex(),
                    "length": length,
                    "raw_hex": raw.hex(),
                }
                try:
                    txt = raw.decode('utf-8')
                    if txt and all(32 <= ord(c) < 127 or c in '\r\n\t' for c in txt):
                        entry["string"] = txt
                except Exception:
                    pass
                result[str(field_num)] = entry

            elif wire_type == 5:
                if pos + 4 > n:
                    break
                raw = buf[pos:pos + 4]
                pos += 4
                int_val = struct.unpack("<I", raw)[0]
                entry = {"wire_type": "fixed32", "data": int_val, "raw_hex": raw.hex()}
                try:
                    txt = raw.rstrip(b'\x00').decode('utf-8', 'ignore')
                    if txt and all(32 <= ord(c) < 127 or c in '\r\n\t' for c in txt):
                        entry["string"] = txt
                except Exception:
                    pass
                result[str(field_num)] = entry

            elif wire_type == 3:
                depth_grp = 1
                while pos < n and depth_grp > 0:
                    k2, pos = await _read_varint(buf, pos)
                    w2 = k2 & 0x07
                    if w2 == 3:
                        depth_grp += 1
                    elif w2 == 4:
                        depth_grp -= 1
                        if depth_grp == 0:
                            break
                    elif w2 == 0:
                        _, pos = await _read_varint(buf, pos)
                    elif w2 == 1:
                        pos += 8
                    elif w2 == 2:
                        ln, pos = await _read_varint(buf, pos)
                        pos += ln
                    elif w2 == 5:
                        pos += 4
                    else:
                        break
                continue

            elif wire_type == 4:
                break
            else:
                break
        except Exception:
            break
    return result


async def decode_protobuf(data):
    """⚡ فك protobuf يدوي متين يدعم كل wire types (0,1,2,5)"""
    try:
        if isinstance(data, str):
            raw = bytes.fromhex(data)
        else:
            raw = bytes(data)
    except Exception as e:
        print_error(f"decode_protobuf hex error: {e}")
        return "{}"
    try:
        fields = await _parse_protobuf_fields(raw, 0, 10)
        return json.dumps(fields, ensure_ascii=False, default=str)
    except Exception as e:
        print_error(f"decode_protobuf parse error: {e}")
        return "{}"


# ======================================================================
# ⚡ NORMALIZATION HELPERS
# ======================================================================
def _normalize_value(value):
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (bytes, bytearray)):
        try:
            return bytes(value).decode('utf-8', 'ignore')
        except Exception:
            return bytes(value).hex()
    if isinstance(value, dict):
        rh = value.get('raw_hex')
        if isinstance(rh, str) and rh:
            try:
                decoded = bytes.fromhex(rh).decode('utf-8', 'ignore')
                if decoded and all(32 <= ord(c) < 127 or c in '\r\n\t' for c in decoded):
                    return decoded
            except Exception:
                pass
            return rh
        s = value.get('string')
        if isinstance(s, str) and s:
            return s
        d = value.get('data')
        if isinstance(d, str):
            return d
        if isinstance(d, (int, float)):
            return str(d)
        if isinstance(d, (bytes, bytearray)):
            try:
                return bytes(d).decode('utf-8', 'ignore')
            except Exception:
                return bytes(d).hex()
        if isinstance(d, dict):
            return _normalize_value(d)
        for v in value.values():
            if isinstance(v, (str, int, float)):
                return str(v) if not isinstance(v, str) else v
            if isinstance(v, (bytes, bytearray)):
                try:
                    return bytes(v).decode('utf-8', 'ignore')
                except Exception:
                    return bytes(v).hex()
            if isinstance(v, dict):
                result = _normalize_value(v)
                if result:
                    return result
    return None


def _normalize_hex(value):
    s = _normalize_value(value)
    if not s or not isinstance(s, str):
        return None
    cleaned = ''.join(c for c in s if c in '0123456789abcdefABCDEF')
    if len(cleaned) % 2 != 0:
        cleaned = cleaned[:-1]
    return cleaned if len(cleaned) >= 16 else None


def _normalize_digits(value):
    s = _normalize_value(value)
    if not s or not isinstance(s, str):
        return None
    cleaned = ''.join(c for c in s if c.isdigit())
    return cleaned if cleaned else None


def _normalize_addr(value):
    s = _normalize_value(value)
    if not s or not isinstance(s, str):
        return None
    cleaned = ''.join(c for c in s if c.isdigit() or c in '.:')
    return cleaned if cleaned and ':' in cleaned else None


def _deep_get_string(node):
    """
    ⚡ استخراج recursive لـ string من أي dict/str/nested من الفك اليدوي
    يحل مشكلة wire_type length_delimited الذي data فيه dict nested
    """
    if node is None:
        return None
    if isinstance(node, str):
        return node
    if isinstance(node, (int, float)):
        return str(node)
    if isinstance(node, (bytes, bytearray)):
        try:
            return bytes(node).decode('utf-8', 'ignore')
        except Exception:
            return bytes(node).hex()
    if isinstance(node, dict):
        # جرّب string مباشرة
        if 'string' in node and isinstance(node['string'], str) and node['string']:
            return node['string']
        # جرّب raw_hex → UTF-8
        if 'raw_hex' in node and isinstance(node['raw_hex'], str) and node['raw_hex']:
            try:
                txt = bytes.fromhex(node['raw_hex']).decode('utf-8', 'ignore')
                if txt and all(32 <= ord(c) < 127 or c in '\r\n\t' for c in txt):
                    return txt
            except Exception:
                pass
        # جرّب data
        d = node.get('data')
        if d is not None:
            result = _deep_get_string(d)
            if result:
                return result
        # جرّب أي حقل nested
        for k in ('1', '2', '3', '4'):
            if k in node:
                result = _deep_get_string(node[k])
                if result:
                    return result
        return None
    return None


async def build_majorlogin_payload(open_id, access_token, platform, client_version, device_info, verr=None):
    try:
        if verr is None:
            verr = client_version
        proto = thunderFF_pb2.MajorLoginReq()
        proto.event_time = str(datetime.now())[:-7]
        proto.game_name = "free fire"
        proto.platform_id = 1
        proto.client_version = str(verr)
        proto.client_version_code = "2019121229"
        proto.system_software = "Android OS 15 / API-35 (AP3A.240905.015.A2/185014)"
        proto.system_hardware = "Handheld"
        proto.device_type = "Handheld"
        proto.screen_width = 1600
        proto.screen_height = 719
        proto.screen_dpi = "234"
        proto.processor_details = "ARM64 FP ASIMD AES | 1820 | 8"
        proto.memory = 2798
        proto.gpu_renderer = "Mali-G57"
        proto.gpu_version = "OpenGL ES 3.2 v1.r49p1-04eac0.2848c17a2fd4e9340e06555168eaa3c9"
        proto.unique_device_id = "Google|f744e396-5694-4e65-995d-97a958f2bd1f"
        proto.client_ip = "197.0.137.129"
        proto.language = "pt-br"
        proto.open_id = str(open_id)
        proto.open_id_type = "4"
        proto.login_open_id_type = 4
        proto.access_token = str(access_token)
        proto.login_by = 2
        proto.platform_sdk_id = 1
        proto.origin_platform_type = "4"
        proto.primary_platform_type = "4"
        proto.reg_avatar = 1
        proto.channel_type = 3
        proto.telecom_operator = "TUNTEL"
        proto.network_operator_a = "TUNTEL"
        proto.network_type = "WIFI"
        proto.network_type_a = "WIFI"
        proto.cpu_type = 2
        proto.cpu_architecture = "64"
        proto.graphics_api = "OpenGLES2"
        proto.supported_astc_bitset = 8191
        proto.client_using_version = "7428b253defc164018c604a1ebbfebdf"
        proto.loading_time = 15078
        proto.release_channel = "android"
        proto.extra_info = "KqsHTx3+QOmBRR1WKvaWewlcpqJBfjki+PPHQoQG8+0yV+Uos7gUFFjHMQ/e7u6han6Fl77r7c3vMN3p8UbKgN+nfycQCgwBmWgBzomx2gj84c+p"
        proto.android_engine_init_flag = 111207
        proto.if_push = 1
        proto.is_vpn = 0

        memory_available = proto.memory_available
        memory_available.version = 55
        memory_available.hidden_value = 81

        proto.external_storage_total = 49973
        proto.external_storage_available = 11338
        proto.internal_storage_total = 854
        proto.internal_storage_available = 11466
        proto.game_disk_storage_total = 49973
        proto.game_disk_storage_available = 11466
        proto.external_sdcard_total_storage = 49973
        proto.external_sdcard_avail_storage = 11466

        proto.library_path = "/data/app/~~lHFxTCCbupG2QVJmsURtZw==/com.dts.freefireth-N3aCHpHNXpdxjD80uIIbww==/lib/arm64"
        proto.library_token = "b8e0cd5e295eee42f5860d3c86e483dd|/data/app/~~lHFxTCCbupG2QVJmsURtZw==/com.dts.freefireth-N3aCHpHNXpdxjD80uIIbww==/base.apk"

        base_payload = proto.SerializeToString()
        extra = b""
        extra += _pb_field(96, '{"cur_rate":[90,60,120],"support_etc2":false}')
        extra += _pb_field(97, 1)
        extra += _pb_field(99, "4")
        extra += _pb_field(100, "4")
        extra += _pb_field(102, b"\x17]ENWU\x0eR5")
        extra += _pb_field(104, 52882)
        extra += _pb_field(105, 1)
        extra += _pb_field(106, "https://dl.ak.freefiremobile.com/live/ABHotUpdates/|https://core-ak.freefiremobile.com/live/ABHotUpdates/|6b2078db9d22dd98f8e9386a39af8462")
        extra += _pb_field(107, "c8e41b7a93f02d56e1a94c7b8203f5d1")

        full_payload = base_payload + extra
        return await aes_encrypt(full_payload, AES_KEY, AES_IV)
    except Exception as e:
        print_error(f"build_majorlogin_payload error: {e}")
        return None


async def send_majorlogin(data, release_version, server_url):
    try:
        url = f"{server_url}MajorLogin" if server_url.endswith('/') else f"{server_url}/MajorLogin"
        req_headers = headers.copy()
        req_headers["ReleaseVersion"] = str(release_version)
        response = await client.post(url, headers=req_headers, data=data)
        if response.status_code != 200:
            print_error(f"MajorLogin HTTP {response.status_code}")
            return None
        response_content = response.content
        if len(response_content) < 40:
            print_error("MajorLogin: response too short")
            return None

        res_proto = thunderFF_pb2.MajorLoginRes()
        try:
            res_proto.ParseFromString(response_content)
        except Exception:
            pass

        dict_res = {}
        try:
            dict_res = await _parse_protobuf_fields(response_content, 0, 10)
        except Exception:
            pass

        key_val = get_proto_field(dict_res, 22)
        iv_val = get_proto_field(dict_res, 23)
        if not key_val:
            key_val = res_proto.aes_ak
        if not iv_val:
            iv_val = res_proto.iv_i

        if isinstance(key_val, str):
            try: key_val = bytes.fromhex(key_val)
            except Exception: pass
        if isinstance(iv_val, str):
            try: iv_val = bytes.fromhex(iv_val)
            except Exception: pass

        if not key_val or not iv_val:
            for offset in range(min(128, len(response_content))):
                try:
                    candidate = thunderFF_pb2.MajorLoginRes()
                    candidate.ParseFromString(response_content[offset:])
                    if candidate.region and candidate.token:
                        res_proto = candidate
                        break
                except Exception:
                    pass

        if key_val:
            try: res_proto.aes_ak = key_val
            except Exception: pass
        if iv_val:
            try: res_proto.iv_i = iv_val
            except Exception: pass

        return res_proto
    except Exception as e:
        print_error(f"send_majorlogin error: {e}")
        return None


async def send_getlogin(data, base_url, token, release_version, fallback_base_url=None):
    def _endpoint(raw):
        raw = str(raw or "").strip()
        if not raw:
            return None
        if not raw.lower().startswith(("http://", "https://")):
            raw = "https://" + raw.lstrip("/")
        try:
            parts = urlsplit(raw)
            if not parts.scheme or not parts.netloc:
                return None
            path = (parts.path or "").rstrip("/")
            low_path = path.lower()
            if low_path.endswith("/getlogindata"):
                endpoint_path = path
            else:
                if low_path.endswith("/majorlogin"):
                    path = path[:-len("/MajorLogin")]
                endpoint_path = (path.rstrip("/") + "/GetLoginData") if path.rstrip("/") else "/GetLoginData"
            return urlunsplit((parts.scheme, parts.netloc, endpoint_path, "", ""))
        except Exception:
            return None

    def _extract_addr(raw_bytes, field_no):
        try:
            pos = 0
            n = len(raw_bytes)
            def read_varint(buf, p):
                result = 0
                shift = 0
                while p < len(buf):
                    byte = buf[p]
                    p += 1
                    result |= (byte & 0x7F) << shift
                    if not (byte & 0x80):
                        return result, p
                    shift += 7
                    if shift > 70:
                        raise ValueError("invalid varint")
                raise ValueError("truncated varint")
            fields = {}
            while pos < n:
                key, pos = read_varint(raw_bytes, pos)
                field_number = key >> 3
                wire_type = key & 0x07
                if field_number <= 0:
                    break
                if wire_type == 0:
                    value, pos = read_varint(raw_bytes, pos)
                elif wire_type == 2:
                    length, pos = read_varint(raw_bytes, pos)
                    if length < 0 or pos + length > n:
                        break
                    value = raw_bytes[pos:pos + length]
                    pos += length
                elif wire_type == 5:
                    if pos + 4 > n: break
                    value = raw_bytes[pos:pos + 4]
                    pos += 4
                elif wire_type == 1:
                    if pos + 8 > n: break
                    value = raw_bytes[pos:pos + 8]
                    pos += 8
                else:
                    break
                fields.setdefault(field_number, []).append(value)
            if field_no in fields:
                value = fields[field_no][0]
                return value.decode("utf-8", "ignore") if isinstance(value, bytes) else str(value)
        except Exception:
            return None
        return None

    async def _parse_response(content):
        proto = thunderFF_pb2.GetLoginDataRes()
        try:
            proto.ParseFromString(content)
        except Exception as exc:
            log(f"[LOGIN] GetLoginData protobuf parse warning: {type(exc).__name__}")
        try:
            for offset in range(0, min(80, len(content))):
                if not proto.functional_addrs or ":" not in proto.functional_addrs:
                    addr = _extract_addr(content[offset:], 14)
                    if addr and ":" in addr:
                        proto.functional_addrs = addr
                if not proto.informational_addrs or ":" not in proto.informational_addrs:
                    addr = _extract_addr(content[offset:], 32)
                    if addr and ":" in addr:
                        proto.informational_addrs = addr
                if proto.functional_addrs and ":" in proto.functional_addrs and proto.informational_addrs and ":" in proto.informational_addrs:
                    break
        except Exception:
            pass
        decoded = {}
        try:
            decoded = await _parse_protobuf_fields(content, 0, 10)
            if decoded:
                log(f"[LOGIN] GetLoginData decoded fields: {list(decoded.keys())[:20]}")
        except Exception as exc:
            log(f"[LOGIN] GetLoginData decoded-fields warning: {type(exc).__name__}: {exc}")
        return proto, decoded

    candidates = []
    for raw in (base_url, fallback_base_url, REGION_SERVERS.get(ACCOUNT_REGION)):
        endpoint = _endpoint(raw)
        if endpoint and endpoint not in candidates:
            candidates.append(endpoint)
    if not candidates:
        log("[LOGIN] GetLoginData skipped: no valid endpoint from MajorLogin or version config")
        return None

    req_headers = headers.copy()
    req_headers["ReleaseVersion"] = str(release_version)
    req_headers["Authorization"] = f"Bearer {token}"
    req_headers["Host"] = "clientbp.ppmainecoonghj.com"

    last_error = None
    total_attempts = 0
    saw_http_200_without_address = False
    for endpoint in candidates:
        for attempt in range(1, 3):
            total_attempts += 1
            try:
                response = await client.post(endpoint, headers=req_headers, data=data, timeout=20.0)
                content = response.content or b""
                if response.status_code != 200 or not content:
                    log(
                        f"[LOGIN] GetLoginData rejected | HTTP {response.status_code} | bytes={len(content)} "
                        f"| attempt={attempt}/2 | endpoint={urlsplit(endpoint).netloc}{urlsplit(endpoint).path}"
                    )
                    if 400 <= response.status_code < 500 and response.status_code != 429:
                        break
                    if attempt < 2:
                        await asyncio.sleep(0.35 * attempt)
                    continue

                parsed_result = await _parse_response(content)
                res_proto, dict_res = parsed_result
                functional_addr = str(getattr(res_proto, "functional_addrs", "") or "")
                if functional_addr and ":" in functional_addr:
                    log(f"[LOGIN] GetLoginData OK | HTTP 200 | bytes={len(content)} | endpoint={urlsplit(endpoint).netloc}{urlsplit(endpoint).path}")
                    return res_proto, dict_res

                saw_http_200_without_address = True
                log(
                    f"[LOGIN] GetLoginData returned HTTP 200 but no functional_addrs | bytes={len(content)} "
                    f"| attempt={attempt}/2 | trying fallback if available"
                )
                if attempt < 2:
                    await asyncio.sleep(0.35 * attempt)
            except Exception as exc:
                last_error = exc
                log(
                    f"[LOGIN] GetLoginData request error | {type(exc).__name__}: {exc} "
                    f"| attempt={attempt}/2 | endpoint={urlsplit(endpoint).netloc}{urlsplit(endpoint).path}"
                )
                if attempt < 2:
                    await asyncio.sleep(0.35 * attempt)

    if saw_http_200_without_address:
        log(f"[-] GetLoginData did not provide a usable functional address after {total_attempts} attempts")
    elif last_error:
        log(f"[-] GetLoginData failed after {total_attempts} attempts: {type(last_error).__name__}: {last_error}")
    else:
        log(f"[-] GetLoginData failed after {total_attempts} attempts; all endpoints rejected the request")
    return None


async def build_tcp_startup_packet(account_id, token, server_time, key, iv, region="ME", typ='OnLine'):
    uid_hex = f"{int(account_id):016x}"
    timestamp_hex = f"{int(server_time):08x}"
    encode_token = token.encode()
    encrypted_packet = (await aes_encrypt(encode_token, key, iv)).hex()
    encrypted_packet_length = f"{len(encrypted_packet) // 2:08x}"
    if typ == 'OnLine':
        return f"9015{uid_hex}{timestamp_hex}00000000{encrypted_packet_length}{encrypted_packet}"
    else:
        return f"9015{uid_hex}{timestamp_hex}{encrypted_packet_length}{encrypted_packet}"


async def send_keep_alive(region="ME"):
    try:
        reg = str(region).upper() if region else "ME"
        ka_hex = "0219" if reg == "ME" else ("0214" if reg == "IND" else "0215")
        return bytes.fromhex(ka_hex)
    except Exception:
        return bytes.fromhex("0219")


# ======================== StartMatch — BR ========================
async def start_game_battle_royale(region, client_version, writer, key, iv):
    packet = bytes.fromhex("080112800a0a010110013a110a044944433110aa011a064555524f50453a100a044944433210311a064555524f504540014a0801090a0b1219202758016291090a8001303838463832424630324139363736373032303130313030303030303030303030303136303030313030313530303032323246393745454530463030303030303436373632353134303030303030303030303030303030303030303030303030303030303030303030303030303066663030303030303030636163666131366410241afb02735d5e571400024a775d45414d1a041b1c001f11010449715f4243481a001e1d071c1703004b1a4066785c524570735c51486775421b5c5a4c07504042685a63610816054e19025e75196001477c015165406370195f5547404e4550640103020f1304064863754268676c755f65576e40467e5f0a417a4701026d675d6e73670b1108495a4c6a0b78470b740065645e525a057258425f584a447d4e6759440c11044e7c596d7f4b625f7d04055a47505c4e1d6b5b4107447d7201057d7f0f14084e430457674f7e517d72015172415d027473577c4d615f79535256780911030f4d5e027a797f614165067806505d53777750475e75064257076500460817014e741e7e5078487e7a7c465e7669767153497064605a7376677773550d160148037e18675966787f4c42607a645f577e7b441b460776026b18685d0b110205490060020f70676175654674706671797f41067346677c4e06585e780f15074c57047b40517075415f6364027259674b5b0166407f7340600407770a22047a5d5c52300b3a0a167305067162727516134208312e3133302e3232480350015ae90403626253513635686e556f4e36416456324b796f566c636f477776484f624e56526c4d727073504b4f43654177616848494176795556497273743752737149734a7a786b3247525268377a2f637664626d504f6a73552f79626d38547a4c69586d2f474351696d494b53486833447955726f39515152756c34545350626d6d624b7949565937545671577059455372323646572f59624578507338514f706d317372785455736c30796a434144444d4f34616a654b615753366361496c554b4963797a494e396d52516f715277687939797257476d337a644345337a6a61436f492f5a585233656f65365a42647a64677654636b6b665733356e4d4c6a6a565072564b6433523172756174394e50514150724a5546627859696c4c5a3859707336654d5447666b6649793574666a526c314d4648706b51774c6373374439656378566c41636f374e664f6d2b30654756466c4434744478706771385533595973587645384842502f70666c767a737138316a32524f4d7857437556445442492f684735625462773166456e4249725162762b636144775147696f74554e316d4c4b77734379456f4766706746614251457645672b736a764c4c78704743334c304a5344532f74526169504354553344374e6249306547516651622f5a466f4c36455630775a324d6f583932414c572f5049752f56634663584e70596b356f7966326151416a536971486a2f363276354843644f525551303578754e6171795251625653704654303137655237675255636b4966366c6f447476342b514e4a4670766d74757077707774396a5a5974437a4b56743657726d6e36785837706658456251555434684f3758a201050803108703a201050804108103a20105080510c001a20105081d10cc01a2010408161078a20105080e10af01a201020815")
    proto = thunderFF_pb2.StartMatch()
    proto.ParseFromString(packet)
    if hasattr(proto.main, 'region_list') and len(proto.main.region_list) > 0:
        proto.main.region_list[0].region = region
        if len(proto.main.region_list) > 1:
            proto.main.region_list[1].region = region
    if hasattr(proto.main, 'client_version'):
        proto.main.client_version.remote_version = client_version
    packet = proto.SerializeToString()
    encrypted_packet = (await aes_encrypt(packet, key, iv)).hex()
    packet_length = len(encrypted_packet) // 2
    hex_length = hex(packet_length)[2:]
    hex_length = hex_length if len(hex_length) > 1 else "0" + hex_length
    reg = str(region).upper() if region else "ME"
    reg_prefix = "031900" if reg == "ME" else ("031400" if reg == "IND" else "031500")
    final_packet = reg_prefix + "0" * (6 - len(hex_length)) + hex_length + encrypted_packet
    writer.write(bytes.fromhex(final_packet))
    await writer.drain()


# ======================== StartMatch — Lone Wolf ========================
async def start_game_lone_wolf(region, client_version, writer, key, iv):
    packet = bytes.fromhex("080112800a0a010b102b3a110a044944433110aa011a064555524f50453a100a044944433210311a064555524f504540014a0801090a0b1219202758016291090a8001303838463832424630324139363736373032303130313030303030303030303030303136303030313030313530303032323246393745454530463030303030303436373632353134303030303030303030303030303030303030303030303030303030303030303030303030303066663030303030303030636163666131366410241afb02735d5e571400024a775d45414d1a041b1c001f11010449715f4243481a001e1d071c1703004b1a4066785c524570735c51486775421b5c5a4c07504042685a63610816054e19025e75196001477c015165406370195f5547404e4550640103020f1304064863754268676c755f65576e40467e5f0a417a4701026d675d6e73670b1108495a4c6a0b78470b740065645e525a057258425f584a447d4e6759440c11044e7c596d7f4b625f7d04055a47505c4e1d6b5b4107447d7201057d7f0f14084e430457674f7e517d72015172415d027473577c4d615f79535256780911030f4d5e027a797f614165067806505d53777750475e75064257076500460817014e741e7e5078487e7a7c465e7669767153497064605a7376677773550d160148037e18675966787f4c42607a645f577e7b441b460776026b18685d0b110205490060020f70676175654674706671797f41067346677c4e06585e780f15074c57047b40517075415f6364027259674b5b0166407f7340600407770a22047a5d5c52300b3a0a167305067162727516134208312e3133302e3232480350015ae90403626253513635686e556f4e36416456324b796f566c636f477776484f624e56526c4d727073504b4f43654177616848494176795556497273743752737149734a7a786b3247525268377a2f637664626d504f6a73552f79626d38547a4c69586d2f474351696d494b53486833447955726f39515152756c34545350626d6d624b7949565937545671577059455372323646572f59624578507338514f706d317372785455736c30796a434144444d4f34616a654b615753366361496c554b4963797a494e396d52516f715277687939797257476d337a644345337a6a61436f492f5a585233656f65365a42647a64677654636b6b665733356e4d4c6a6a565072564b6433523172756174394e50514150724a5546627859696c4c5a3859707336654d5447666b6649793574666a526c314d4648706b51774c6373374439656378566c41636f374e664f6d2b30654756466c4434744478706771385533595973587645384842502f70666c767a737138316a32524f4d7857437556445442492f684735625462773166456e4249725162762b636144775147696f74554e316d4c4b77734379456f4766706746614251457645672b736a764c4c78704743334c304a5344532f74526169504354553344374e6249306547516651622f5a466f4c36455630775a324d6f583932414c572f5049752f56634663584e70596b356f7966326151416a536971486a2f363276354843644f525551303578754e6171795251625653704654303137655237675255636b4966366c6f447476342b514e4a4670766d74757077707774396a5a5974437a4b56743657726d6e36785837706658456251555434684f3758a201050803108703a201050804108103a20105080510c001a20105081d10cc01a2010408161078a20105080e10af01a201020815")
    proto = thunderFF_pb2.StartMatch()
    proto.ParseFromString(packet)
    if hasattr(proto.main, 'region_list') and len(proto.main.region_list) > 0:
        proto.main.region_list[0].region = region
        if len(proto.main.region_list) > 1:
            proto.main.region_list[1].region = region
    if hasattr(proto.main, 'client_version'):
        proto.main.client_version.remote_version = client_version
    packet = proto.SerializeToString()
    encrypted_packet = (await aes_encrypt(packet, key, iv)).hex()
    packet_length = len(encrypted_packet) // 2
    hex_length = hex(packet_length)[2:]
    hex_length = hex_length if len(hex_length) > 1 else "0" + hex_length
    reg = str(region).upper() if region else "ME"
    reg_prefix = "031900" if reg == "ME" else ("031400" if reg == "IND" else "031500")
    final_packet = reg_prefix + "0" * (6 - len(hex_length)) + hex_length + encrypted_packet
    writer.write(bytes.fromhex(final_packet))
    await writer.drain()


# ==================== UDP CRYPTO ====================
def has_ssan_zig(n):
    z = (n << 1) & 0xFFFFFFFFFFFFFFFF
    out = bytearray()
    while z >= 0x80:
        out.append((z & 0x7F) | 0x80)
        z >>= 7
    out.append(z)
    return bytes(out)


def uleb_encode(n):
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            b |= 0x80
        out.append(b)
        if not n:
            break
    return bytes(out)


async def tea_enc(v0, v1, k0, k1, k2, k3):
    s = 0
    for _ in range(_ROUNDS):
        s = (s + _DELTA) & 0xFFFFFFFF
        v0 = (v0 + (((((v1 << 4) & 0xFFFFFFFF) + k0) & 0xFFFFFFFF ^
                      ((v1 + s) & 0xFFFFFFFF) ^
                      (((v1 >> 5) + k1) & 0xFFFFFFFF)))) & 0xFFFFFFFF
        v1 = (v1 + (((((v0 << 4) & 0xFFFFFFFF) + k2) & 0xFFFFFFFF ^
                      ((v0 + s) & 0xFFFFFFFF) ^
                      (((v0 >> 5) + k3) & 0xFFFFFFFF)))) & 0xFFFFFFFF
    return v0, v1


async def tea_dec(v0, v1, k0, k1, k2, k3):
    s = (_DELTA * _ROUNDS) & 0xFFFFFFFF
    for _ in range(_ROUNDS):
        v1 = (v1 - (((((v0 << 4) & 0xFFFFFFFF) + k2) & 0xFFFFFFFF ^
                      ((v0 + s) & 0xFFFFFFFF) ^
                      (((v0 >> 5) + k3) & 0xFFFFFFFF)))) & 0xFFFFFFFF
        v0 = (v0 - (((((v1 << 4) & 0xFFFFFFFF) + k0) & 0xFFFFFFFF ^
                      ((v1 + s) & 0xFFFFFFFF) ^
                      (((v1 >> 5) + k1) & 0xFFFFFFFF)))) & 0xFFFFFFFF
        s = (s - _DELTA) & 0xFFFFFFFF
    return v0, v1


async def tea_cbc_encrypt(padded, key_bytes):
    k0, k1, k2, k3 = (struct.unpack_from("<I", key_bytes, o)[0] for o in (0, 4, 8, 12))
    out = bytearray(len(padded))
    prev_cipher = bytearray(8)
    prev_intermediate = bytearray(8)
    for i in range(0, len(padded), 8):
        xored = bytearray(8)
        for j in range(8):
            xored[j] = padded[i + j] ^ prev_cipher[j]
        e0, e1 = await tea_enc(
            struct.unpack_from("<I", xored, 0)[0],
            struct.unpack_from("<I", xored, 4)[0],
            k0, k1, k2, k3,
        )
        enc = bytearray(8)
        struct.pack_into("<I", enc, 0, e0)
        struct.pack_into("<I", enc, 4, e1)
        for j in range(8):
            out[i + j] = enc[j] ^ prev_intermediate[j]
        prev_cipher[:] = out[i:i + 8]
        prev_intermediate[:] = xored
    return bytes(out)


async def build_padded(content):
    pad_len = (8 - (len(content) + 10) % 8) % 8
    return bytes([pad_len, 0, 0]) + b"\x00" * pad_len + content + b"\x00" * 7


async def encode_header(layout, send_option, cmd, order_id, flags, length, k, v80):
    out = bytearray()
    for code in layout:
        value = {0: send_option, 1: cmd, 2: order_id, 3: flags, 4: length}[code]
        if _FIELD_SIZES[code] == 1:
            out.append((value & 0xFF) ^ k)
        else:
            v = ((value & 0xFFFF) ^ v80) & 0xFFFF
            out.append(v & 0xFF)
            out.append((v >> 8) & 0xFF)
    return bytes(out)


async def crc7_buff(crc, buf):
    c = crc & 0x7F
    for b in buf:
        c = CRC7_TABLE[((2 * (c & 0xFF)) ^ (b & 0xFF)) & 0xFF] & 0x7F
    return c & 0x7F


async def sv_frame(msg_key, layout, send_option, cmd, order_id, flags, content, key, encrypted=True):
    k = key[0]
    v80 = ((k << 8) | k) & 0xFFFF
    body = await tea_cbc_encrypt(await build_padded(content), key) if encrypted else content
    hdr = bytearray([msg_key, 0]) + await encode_header(layout, send_option, cmd, order_id, flags, len(body), k, v80)
    packet = bytearray(hdr + body)
    packet[1] = await crc7_buff(0, bytes(packet[2:])) & 0x7F
    return bytes(packet)


async def build_match_startup_packets(token, udp_key, match_code, account_id, block_val,
                                      server_ip="", region="ME", client_version="1.132.8",
                                      client_version_code="2019121229", access_token="",
                                      mode_id=BR_MODE_ID, map_id=BR_MAP_ID):
    token = _normalize_value(token)
    udp_key = _normalize_hex(udp_key)
    match_code = _normalize_digits(match_code)
    server_ip = _normalize_value(server_ip) or ""
    access_token = _normalize_value(access_token) or ""

    if not token:
        raise ValueError("build_match_startup_packets: token is empty")
    if not udp_key:
        raise ValueError("build_match_startup_packets: udp_key is invalid hex")
    if not match_code:
        raise ValueError("build_match_startup_packets: match_code has no digits")

    token = token.strip()
    server_ip = server_ip.strip() if isinstance(server_ip, str) else ""
    access_token = access_token.strip() if isinstance(access_token, str) else ""

    udp_key = bytes.fromhex(udp_key)
    match_code = [int(ch) for ch in match_code]

    thunder_jwt = token[:660] if len(token) > 660 else token
    sharma_jwt = token[660:] if len(token) > 660 else ""
    encoded_thunder_jwt = thunder_jwt.encode() if isinstance(thunder_jwt, str) else thunder_jwt
    encoded_sharma_jwt = sharma_jwt.encode() if isinstance(sharma_jwt, str) else sharma_jwt

    garena420 = has_ssan_zig(len(encoded_thunder_jwt)) + encoded_thunder_jwt
    reg = str(region).upper() if region else "ME"
    csoversea_block = bytes.fromhex(
        "ca0163736f7665727365612e7374726f6e67686f6c642e66726565666972656d6f62696c652e636f6d"
        "3b302e302e302e303b33342e3132362e37362e34353b33342e38372e3137372e31343b33342e38372e"
        "3137302e3233303b33352e3138352e3138332e35370000000000000100000000000000000000000001"
        "00000800000100000000000100a8a2d7bebd8d8bdf110200"
    )

    mid = bytes.fromhex('0000000001000102030101') + has_ssan_zig(len(reg)) + reg.encode()
    mid += bytes.fromhex('0001030003000004')
    mid += has_ssan_zig(len(client_version)) + client_version.encode()
    mid += has_ssan_zig(len(client_version_code)) + client_version_code.encode()
    mid += csoversea_block

    clean_ip = server_ip.split(':')[0] if server_ip else "0.0.0.0"
    mid += has_ssan_zig(len(clean_ip)) + clean_ip.encode()

    clean_acc_tok = access_token.strip() if access_token else ""
    if clean_acc_tok:
        mid += has_ssan_zig(len(clean_acc_tok)) + clean_acc_tok.encode()

    mid += has_ssan_zig(len(encoded_sharma_jwt)) + encoded_sharma_jwt

    tg_garena420 = (
        uleb_encode(int(account_id)) +
        uleb_encode(int(block_val)) +
        uleb_encode(1) +
        uleb_encode(int(mode_id)) +
        uleb_encode(int(block_val)) +
        uleb_encode(int(map_id)) +
        mid
    )

    process = await sv_frame(0x5E, match_code, 2, 447, 0, 1, garena420, udp_key)
    loading = await sv_frame(0x5A, match_code, 2, 448, 1, 1, tg_garena420, udp_key)
    return process.hex(), loading.hex()


async def produce_xor_key(secret_key):
    k = secret_key[0] if secret_key and len(secret_key) > 0 else 10
    return k, ((k << 8) | k) & 0xFFFF


async def parse_layout(layout):
    if isinstance(layout, str):
        return [int(ch) for ch in layout.strip()]
    return list(layout)


async def tea_cbc_decrypt(body, key_bytes):
    k0, k1, k2, k3 = (struct.unpack_from("<I", key_bytes, o)[0] for o in (0, 4, 8, 12))
    out = bytearray(len(body))
    prev_intermediate = bytearray(8)
    prev_cipher = bytearray(8)
    xored = bytearray(8)
    dec = bytearray(8)
    for i in range(0, len(body), 8):
        for j in range(8):
            xored[j] = body[i + j] ^ prev_intermediate[j]
        d0, d1 = await tea_dec(
            struct.unpack_from("<I", xored, 0)[0],
            struct.unpack_from("<I", xored, 4)[0],
            k0, k1, k2, k3
        )
        struct.pack_into("<I", dec, 0, d0)
        struct.pack_into("<I", dec, 4, d1)
        for j in range(8):
            out[i + j] = dec[j] ^ prev_cipher[j]
        prev_cipher[:] = body[i:i + 8]
        prev_intermediate[:] = dec
    return bytes(out)


async def build_hello_packet(text, key, layout):
    data = text.encode("utf-8")
    if len(data) > 25:
        raise ValueError(f"Text is too long ({len(data)} bytes)")
    content = b"\x10\x00\x00\x00" + data + b"\x00" * (29 - 4 - len(data))
    k, v80 = await produce_xor_key(key)
    layout = await parse_layout(layout)
    padded = await build_padded(content)
    enc_body = await tea_cbc_encrypt(padded, key)
    header_bytes = await encode_header(layout, 1, 1, 0, 1, len(enc_body), k, v80)
    packet = bytearray([0x63, 0x00]) + header_bytes + enc_body
    packet[1] = await crc7_buff(0, packet[2:]) & 0x7F
    return bytes(packet).hex()


async def classify(frame):
    cmd = frame["cmd"]
    msg_name = MESSAGE_ID_TO_NAME.get(cmd, f"UNKNOWN_{cmd}")
    if msg_name == "UDP_HELLO":
        return "HELLO"
    if msg_name == "UDP_ACK":
        return "ACK"
    if msg_name == "UDP_PING":
        return "PING"
    if msg_name == "RUDP_JOIN_MATCH":
        return "JOIN_MATCH"
    if msg_name.startswith("RUDP_"):
        return msg_name
    if msg_name.startswith("UDP_"):
        return msg_name
    return "DATA"


async def build_packet(msg_key, layout, send_option, cmd, order_id, flags, content, key, encrypted=True):
    k = key[0]
    v80 = ((k << 8) | k) & 0xFFFF
    body = await tea_cbc_encrypt(await build_padded(content), key) if encrypted else content
    hdr = bytearray([msg_key, 0])
    for code in layout:
        value = {0: send_option, 1: cmd, 2: order_id, 3: flags, 4: len(body)}[code]
        if _FIELD_SIZES[code] == 1:
            hdr.append((value & 0xFF) ^ k)
        else:
            v = ((value & 0xFFFF) ^ v80) & 0xFFFF
            hdr.append(v & 0xFF)
            hdr.append((v >> 8) & 0xFF)
    packet = bytearray(hdr + body)
    packet[1] = await crc7_buff(0, bytes(packet[2:])) & 0x7F
    return bytes(packet)


async def layouts_from_mask(mask):
    ru = [int(c) for c in str(mask).strip()]
    nr = [c for c in ru if c != 2]
    return ru, nr


async def reply_for(frame, key, mask, ack_key=0x68, ping_key=0x6D, hello_key=0x5B, ack_style="short"):
    ru, nr = await layouts_from_mask(mask)
    typ = await classify(frame)
    if typ == "HELLO":
        if ack_style == "echo":
            content = frame["content"] if frame["content"] else b"\x10\x00\x00\x00"
            return typ, await build_packet(hello_key, nr, 1, 1, None, 1, content, key)
        return typ, await build_packet(ack_key, nr, 0, 2, None, 1, b"\x01\x00", key)
    if typ == "ACK":
        content = frame["content"] if frame["content"] else b"\x01\x00"
        return typ, await build_packet(ack_key, nr, 0, 2, None, 1, content, key)
    if typ == "PING":
        c = frame["content"]
        counter = c[:4] if len(c) >= 4 else c
        return typ, await build_packet(ping_key, nr, 0, 3, None, 0, counter + b"\x00\x00\x00", key, encrypted=False)
    if typ == "JOIN_MATCH":
        return typ, await build_packet(ack_key, nr, 0, 2, None, 1, b"\x02\x00", key)
    return typ, None


async def keepalive_ping(sock, ip, port, key_bytes, mask, stop_event):
    nr = (await layouts_from_mask(mask))[1]
    ping_keys = [0x66, 0x6D, 0x69, 0x6C, 0x6B, 0x6E, 0x6F, 0x70]
    loop = asyncio.get_event_loop()
    i = 0
    while not stop_event.is_set():
        pk = ping_keys[i % len(ping_keys)]
        counter = int(time.time() * 1000) & 0xFFFFFFFF
        pkt = await build_packet(pk, nr, 0, 3, None, 0, struct.pack("<I", counter) + b"\x00\x00\x00", key_bytes, encrypted=False)
        try:
            await loop.sock_sendto(sock, pkt, (ip, port))
        except Exception:
            pass
        i += 1
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=3.0)
        except asyncio.TimeoutError:
            pass


async def try_header(buf, layout, k, v80):
    off = 2
    out = {}
    for code in layout:
        size = _FIELD_SIZES[code]
        if off + size > len(buf):
            return None
        out[_FIELD_NAMES[code]] = (buf[off] ^ k) if size == 1 else ((buf[off] | (buf[off + 1] << 8)) ^ v80) & 0xFFFF
        off += size
    out["headerLen"] = off
    return out


async def oicq_unpad(padded):
    if not padded or len(padded) < 8:
        return None
    if not all(padded[-1 - i] == 0 for i in range(7)):
        return None
    pad_len = padded[0] & 0x07
    s = 3 + pad_len
    e = len(padded) - 7
    return padded[s:e] if s < e else b""


async def decode_packet(packet, key, mask=None):
    data = bytes(packet) if isinstance(packet, bytes) else bytes.fromhex(packet)
    if len(data) < 8:
        return None
    k = key[0]
    v80 = ((k << 8) | k) & 0xFFFF
    crc_ok = (data[1] & 0x7F) == await crc7_buff(0, data[2:])
    candidates = []
    if mask:
        ru, nr = await layouts_from_mask(mask)
        layouts = [("RUDP", ru), ("nonRUDP", nr)]
    else:
        layouts = [("RUDP", list(p)) for p in itertools.permutations([0, 1, 2, 3, 4])]
        layouts += [("nonRUDP", list(p)) for p in itertools.permutations([0, 1, 3, 4])]
    for kind, layout in layouts:
        f = await try_header(data, layout, k, v80)
        if not f:
            continue
        if f["flags"] > 7 or f["sendOption"] > 7:
            continue
        if f["length"] != len(data) - f["headerLen"]:
            continue
        body = data[f["headerLen"]:f["headerLen"] + f["length"]]
        content = None
        padded = None
        if f["flags"] & 1:
            if len(body) < 8 or len(body) % 8 != 0:
                continue
            padded = await tea_cbc_decrypt(body, key)
            content = await oicq_unpad(padded)
            if content is None:
                continue
        else:
            content = body
        score = (1 if crc_ok else 0) + (1 if content is not None else 0)
        candidates.append({
            "kind": kind, "layout": layout, "headerLen": f["headerLen"],
            "msgKey": data[0], "cmd": f["cmd"], "flags": f["flags"],
            "sendOption": f["sendOption"], "orderId": f.get("orderId"),
            "length": f["length"], "content": content, "crcOk": crc_ok,
            "padded": padded, "score": score, "total": len(data),
        })
    if not candidates:
        return None
    candidates.sort(key=lambda c: (c["kind"] == "RUDP" or c["kind"] == "nonRUDP", c["score"]), reverse=True)
    return candidates[0]


# ================================================================
# play_game — نفس الكود المرجعي
# ================================================================
async def play_game(server_ip_port, thunder, sharma, udp_key, match_code,
                    account_id, player_region, client_version, key, iv,
                    match_index: int):
    match_start_time = time.time()
    ping_task = None
    sock = None
    ping_stop = asyncio.Event()
    completed_cleanly = False

    try:
        server_ip_port = _normalize_value(server_ip_port)
        udp_key = _normalize_hex(udp_key)
        match_code = _normalize_digits(match_code)

        ip, port = server_ip_port.split(":")
        port = int(port)
        resolved_ip = await resolve_host_cloudflare(ip)

        loop = asyncio.get_event_loop()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        optimize_udp_socket(sock)
        sock.setblocking(False)

        udp_key_bytes = bytes.fromhex(udp_key)
        hello_packet = await build_hello_packet(f"{account_id}_2585", udp_key_bytes, match_code)
        await loop.sock_sendto(sock, bytes.fromhex(hello_packet), (resolved_ip, port))

        ack_state = "waiting_for_hello_reply"
        thunder_sent = False
        sharma_sent = False
        join_match_received = False
        local_closed = False
        send_lock = asyncio.Lock()

        ping_task = asyncio.create_task(
            keepalive_ping(sock, resolved_ip, port, udp_key_bytes, match_code, ping_stop)
        )
        last_activity = time.time()
        MAX_IDLE_BEFORE_HELLO_RESEND = 7.0

        print_colored(
            f"🎮 [MATCH #{match_index}] UDP started → {server_ip_port} (DNS: {resolved_ip})",
            Colors.MAGENTA
        )

        async def send_thunder_sharma_inline():
            nonlocal ack_state, thunder_sent, sharma_sent
            if thunder_sent:
                return
            async with send_lock:
                if thunder_sent:
                    return
                try:
                    await loop.sock_sendto(sock, bytes.fromhex(thunder), (resolved_ip, port))
                    thunder_sent = True
                    await asyncio.sleep(0.1)
                    prepare_ack = await build_packet(
                        0x68, (await layouts_from_mask(match_code))[1],
                        0, 2, None, 1, b"\x01\x00", udp_key_bytes
                    )
                    await loop.sock_sendto(sock, prepare_ack, (resolved_ip, port))
                    await asyncio.sleep(0.2)
                    await loop.sock_sendto(sock, bytes.fromhex(sharma), (resolved_ip, port))
                    sharma_sent = True
                    ack_state = "thunder_sharma_sent"
                    print_success(f"[MATCH #{match_index}] Thunder+Sharma sent!")
                except Exception as e:
                    print_error(f"[MATCH #{match_index}] send error: {e}")

        while not local_closed:
            if time.time() - match_start_time > MAX_MATCH_DURATION:
                break
            try:
                response, server_addr = await asyncio.wait_for(
                    loop.sock_recvfrom(sock, 65535), timeout=1.5
                )
                if response:
                    last_activity = time.time()
                    frame = await decode_packet(response, udp_key_bytes, match_code)
                    if frame:
                        ptype = await classify(frame)

                        if frame['cmd'] in [103, 107]:
                            print_success(
                                f"[MATCH #{match_index}] Completed (cmd {frame['cmd']})"
                            )
                            completed_cleanly = True
                            local_closed = True
                            continue

                        if frame['cmd'] == 101:
                            try:
                                ack_pkt = await build_packet(
                                    0x68, (await layouts_from_mask(match_code))[1],
                                    0, 2, None, 1, b"\x01\x00", udp_key_bytes
                                )
                                await loop.sock_sendto(sock, ack_pkt, server_addr)
                            except Exception:
                                pass
                            continue

                        if ptype in ["ACK", "PING", "HELLO", "JOIN_MATCH"]:
                            if ptype == "HELLO" and ack_state == "waiting_for_hello_reply":
                                typ, reply = await reply_for(
                                    frame, udp_key_bytes, match_code, ack_style="short"
                                )
                                if reply:
                                    await loop.sock_sendto(sock, reply, server_addr)
                                ack_state = "ack_sent_waiting"
                            elif ptype == "ACK":
                                if ack_state == "waiting_for_hello_reply":
                                    typ, reply = await reply_for(frame, udp_key_bytes, match_code)
                                    if reply:
                                        await loop.sock_sendto(sock, reply, server_addr)
                                    ack_state = "ready_to_send_thunder"
                                elif ack_state == "ack_sent_waiting":
                                    ack_state = "ready_to_send_thunder"
                                else:
                                    typ, reply = await reply_for(frame, udp_key_bytes, match_code)
                                    if reply:
                                        await loop.sock_sendto(sock, reply, server_addr)
                            elif ptype == "PING":
                                typ, reply = await reply_for(frame, udp_key_bytes, match_code)
                                if reply:
                                    await loop.sock_sendto(sock, reply, server_addr)
                            elif ptype == "JOIN_MATCH" and not join_match_received:
                                typ, reply = await reply_for(frame, udp_key_bytes, match_code)
                                if reply:
                                    await loop.sock_sendto(sock, reply, server_addr)
                                    join_match_received = True
            except asyncio.TimeoutError:
                if ack_state == "ready_to_send_thunder" and not thunder_sent:
                    await send_thunder_sharma_inline()
                elif ack_state == "waiting_for_hello_reply":
                    if (time.time() - last_activity) > MAX_IDLE_BEFORE_HELLO_RESEND:
                        try:
                            pkt = await build_hello_packet(
                                f"{account_id}_2585", udp_key_bytes, match_code
                            )
                            await loop.sock_sendto(sock, bytes.fromhex(pkt), (resolved_ip, port))
                        except Exception:
                            pass
                        last_activity = time.time()
                    if (time.time() - match_start_time) > 25.0:
                        print_warning(f"[MATCH #{match_index}] Handshake timeout")
                        break
                elif ack_state == "thunder_sharma_sent":
                    if (time.time() - last_activity) > MATCH_IDLE_TIMEOUT:
                        print_success(f"[MATCH #{match_index}] Finished naturally")
                        completed_cleanly = True
                        break
                continue
            except BlockingIOError:
                await asyncio.sleep(0.05)
            except OSError:
                await asyncio.sleep(0.5)
                continue
            except Exception:
                await asyncio.sleep(0.5)
                continue

            if ack_state == "ready_to_send_thunder" and not thunder_sent:
                await send_thunder_sharma_inline()

        return f"match #{match_index} finished"
    except Exception as e:
        print_error(f"[MATCH #{match_index}] error: {e}")
        return f"match #{match_index} error"
    finally:
        ping_stop.set()
        if ping_task:
            ping_task.cancel()
            try:
                await ping_task
            except asyncio.CancelledError:
                pass
        if sock:
            try:
                sock.close()
            except Exception:
                pass
        print_info(f"[MATCH #{match_index}] Closed.")


# ================================================================
# functional_br — موحّدة BR + LW مع استخراج recursive
# ================================================================
async def functional_br(addrs, starter_packet, account_region, client_version,
                        key, iv, account_id="", account_data=None,
                        max_reconnects=10):
    reconnects = 0
    ip, port = addrs.split(":")
    play_matches: List[asyncio.Task] = []
    no_response_count = 0
    search_attempts = 0
    last_start_time = 0.0
    uid_str = str(account_id)
    control_uid = str((account_data or {}).get("auth_uid") or uid_str)
    restart_generation_at_start = account_restart_generation(control_uid)

    current_token = starter_packet
    current_key = key
    current_iv = iv
    current_account_data = account_data

    consecutive_parse_failures = 0
    MAX_CONSECUTIVE_PARSE_FAILURES = 5

    def _get_level():
        try:
            return max(1, int((current_account_data or {}).get("level", 1) or 1))
        except Exception:
            return 1

    def _pick_mode():
        lvl = _get_level()
        if lvl >= LONE_WOLF_MIN_LEVEL:
            return "LW", LW_MODE_ID, LW_MAP_ID
        return "BR", BR_MODE_ID, BR_MAP_ID

    current_mode = _pick_mode()[0]
    log(f"[MODE] UID {uid_str} | Level {_get_level()} → {current_mode} mode")

    try:
        while True:
            if account_is_deleted(control_uid):
                log(f"[CONTROL] UID {control_uid} deleted; ending after any active match.")
                return
            if account_restart_generation(control_uid) != restart_generation_at_start:
                log(f"[CONTROL] Restart requested for UID {control_uid}; reconnecting this account.")
                return
            while account_is_paused(control_uid) and not account_is_deleted(control_uid) \
                    and account_restart_generation(control_uid) == restart_generation_at_start:
                await asyncio.sleep(0.5)
            if account_is_deleted(control_uid):
                log(f"[CONTROL] UID {control_uid} deleted; worker stopped.")
                return
            if account_restart_generation(control_uid) != restart_generation_at_start:
                log(f"[CONTROL] Restart requested for UID {control_uid}; reconnecting this account.")
                return

            writer = None
            try:
                resolved_ip = await resolve_host_cloudflare(ip)
                reader, writer = await asyncio.open_connection(resolved_ip, int(port))

                raw_sock = writer.get_extra_info('socket')
                if raw_sock:
                    optimize_tcp_socket(raw_sock)

                writer.write(bytes.fromhex(current_token))
                await writer.drain()

                try:
                    init_ka = await send_keep_alive(account_region)
                    if init_ka and writer and not writer.is_closing():
                        writer.write(init_ka)
                        await asyncio.wait_for(writer.drain(), timeout=3)
                except Exception:
                    pass

                print_success(f"[FUNCTIONAL] TCP Gateway Connected for UID: {uid_str} (DNS: {resolved_ip})")
                reconnects = 0
                no_response_count = 0
                last_start_time = 0.0

                async def send_start_match():
                    nonlocal search_attempts, last_start_time, current_mode
                    if account_is_deleted(control_uid):
                        return False
                    if account_is_paused(control_uid):
                        return False
                    if account_restart_generation(control_uid) != restart_generation_at_start:
                        return False

                    mode, mode_id, map_id = _pick_mode()
                    if mode != current_mode:
                        log(f"[MODE] UID {uid_str} switched: {current_mode} → {mode} (Level {_get_level()})")
                        current_mode = mode

                    search_attempts += 1
                    current_region = account_region or "ME"

                    if search_attempts > MAX_START_MATCH_ATTEMPTS:
                        print_warning(f"[FUNCTIONAL] Too many StartMatch attempts ({search_attempts}); forcing reconnect")
                        raise ConnectionError("Too many StartMatch attempts")

                    if mode == "LW":
                        print_info(f"[LONE WOLF] Sending StartMatch #{search_attempts} region: {current_region}")
                        try:
                            await asyncio.sleep(random.uniform(0.3, 0.6))
                            await start_game_lone_wolf(
                                current_region, client_version, writer,
                                current_key, current_iv
                            )
                            print_success("[LONE WOLF] StartMatch packet sent")
                        except Exception as e:
                            print_error(f"start_game_lone_wolf error: {e}")
                    else:
                        print_info(f"[BATTLE ROYALE] Sending StartMatch #{search_attempts} region: {current_region}")
                        try:
                            await asyncio.sleep(random.uniform(0.3, 0.6))
                            await start_game_battle_royale(
                                current_region, client_version, writer,
                                current_key, current_iv
                            )
                            print_success("[BATTLE ROYALE] StartMatch packet sent")
                        except Exception as e:
                            print_error(f"start_game_battle_royale error: {e}")

                    last_start_time = asyncio.get_running_loop().time()
                    return True

                await send_start_match()

                while True:
                    play_matches[:] = [m for m in play_matches if not m.done()]

                    if account_is_deleted(control_uid):
                        log(f"[CONTROL] UID {control_uid} deleted; closing idle gateway after active match.")
                        return
                    if account_restart_generation(control_uid) != restart_generation_at_start and not play_matches:
                        log(f"[CONTROL] Restarting UID {control_uid} after active match finished.")
                        return

                    now = asyncio.get_running_loop().time()
                    if (not account_is_paused(control_uid) and not account_is_deleted(control_uid)
                            and account_restart_generation(control_uid) == restart_generation_at_start
                            and len(play_matches) == 0
                            and (now - last_start_time >= START_MATCH_INTERVAL)):
                        await send_start_match()

                    try:
                        data = await asyncio.wait_for(reader.read(8192), timeout=0.5)
                    except asyncio.TimeoutError:
                        no_response_count += 1
                        if no_response_count > 80:
                            print_warning(f"[FUNCTIONAL] Gateway silent ({uid_str}). Reconnecting...")
                            raise ConnectionError("Gateway idle timeout")
                        continue

                    if not data:
                        raise ConnectionError("Connection closed by server")

                    hex_data = data.hex()
                    packet_length = len(data)
                    no_response_count = 0

                    if hex_data.startswith("0300") and 10 < packet_length < 30:
                        print_info("Match starting, please wait...")
                        continue

                    if hex_data.startswith("0300") and packet_length >= 300:
                        print_colored("=" * 60, Colors.GREEN)
                        print_colored(f"MATCH FOUND! Loading...", Colors.GREEN)
                        print_colored("=" * 60, Colors.GREEN)

                        try:
                            res = json.loads(await decode_protobuf(hex_data[10:]))

                            token = None
                            udp_key = None
                            match_code = None
                            server_ip_port = None
                            match_account_id = None
                            block_val = None

                            def _get_field_entry(res_dict, field_num):
                                if not isinstance(res_dict, dict):
                                    return None
                                return res_dict.get(str(field_num))

                            # field 42 (match_code)
                            mc_entry = _get_field_entry(res, 42)
                            if mc_entry:
                                match_code = _deep_get_string(mc_entry) or match_code

                            # field 1 (match_account_id)
                            mai_entry = _get_field_entry(res, 1)
                            if mai_entry:
                                match_account_id = _deep_get_string(mai_entry) or match_account_id

                            # field 5 (nested)
                            f5_entry = _get_field_entry(res, 5)
                            sub5 = None
                            if f5_entry and isinstance(f5_entry, dict):
                                d5 = f5_entry.get('data')
                                if isinstance(d5, dict):
                                    sub5 = d5
                                elif isinstance(d5, str):
                                    try:
                                        sub5 = await _parse_protobuf_fields(bytes.fromhex(d5), 0, 10)
                                    except Exception:
                                        sub5 = None

                            if isinstance(sub5, dict):
                                sp_entry = _get_field_entry(sub5, 2)
                                if sp_entry:
                                    server_ip_port = _deep_get_string(sp_entry) or server_ip_port
                                uk_entry = _get_field_entry(sub5, 3)
                                if uk_entry:
                                    udp_key = _deep_get_string(uk_entry) or udp_key
                                tk_entry = _get_field_entry(sub5, 4)
                                if tk_entry:
                                    token = _deep_get_string(tk_entry) or token
                                mc5_entry = _get_field_entry(sub5, 42)
                                if mc5_entry:
                                    mc_inner = _deep_get_string(mc5_entry)
                                    if mc_inner:
                                        match_code = mc_inner
                                bv_entry = _get_field_entry(sub5, 1)
                                if bv_entry:
                                    bv = bv_entry.get('data') if isinstance(bv_entry, dict) else bv_entry
                                    if bv is not None and not isinstance(bv, dict):
                                        try:
                                            block_val = int(bv)
                                        except (ValueError, TypeError):
                                            pass

                            token = _normalize_value(token)
                            udp_key = _normalize_hex(udp_key)
                            match_code = _normalize_digits(match_code)
                            server_ip_port = _normalize_addr(server_ip_port)
                            if isinstance(match_account_id, str):
                                match_account_id = ''.join(c for c in match_account_id if c.isdigit()) or None

                            log(f"[FUNCTIONAL] Extracted | token={bool(token)} | udp_key={bool(udp_key)} | "
                                f"match_code={bool(match_code)} | server={bool(server_ip_port)} | "
                                f"acc_id={match_account_id} | block={block_val}")

                            effective_acc_id = match_account_id or account_id or "ME_BOT"

                            if token and udp_key and match_code and server_ip_port:
                                log(f"[FUNCTIONAL] Cleaned | token[:30]={token[:30]} | "
                                    f"udp_key[:30]={udp_key[:30]} | match_code={match_code} | "
                                    f"server={server_ip_port}")

                                acc_tok = ""
                                if current_account_data:
                                    acc_tok = current_account_data.get('access_token', '') or ""
                                    if not isinstance(acc_tok, str):
                                        acc_tok = _normalize_value(acc_tok) or ""

                                _, mode_id, map_id = _pick_mode()
                                current_mode = "LW" if mode_id == LW_MODE_ID else "BR"

                                thunder, sharma = await build_match_startup_packets(
                                    token, udp_key, match_code, effective_acc_id, block_val or 0,
                                    server_ip=server_ip_port,
                                    region=account_region,
                                    client_version=client_version,
                                    access_token=acc_tok,
                                    mode_id=mode_id,
                                    map_id=map_id
                                )

                                match_index = len(play_matches) + 1
                                print_colored(
                                    f"🚀 [MATCH #{match_index}] UDP starting → {server_ip_port} (background)",
                                    Colors.CYAN
                                )
                                print_success(
                                    f"[FUNCTIONAL] UDP task started. Mode: {current_mode}"
                                )

                                new_match = asyncio.create_task(
                                    play_game(
                                        server_ip_port,
                                        thunder,
                                        sharma,
                                        udp_key,
                                        match_code,
                                        effective_acc_id,
                                        account_region,
                                        client_version,
                                        current_key,
                                        current_iv,
                                        match_index=match_index
                                    )
                                )
                                play_matches.append(new_match)

                                consecutive_parse_failures = 0

                                try:
                                    writer.close()
                                    await writer.wait_closed()
                                except Exception:
                                    pass
                                writer = None

                                print_info(
                                    f"[OFFLINE] {NEW_MATCH_DELAY}s offline → "
                                    f"reload token → new StartMatch"
                                )
                                await asyncio.sleep(NEW_MATCH_DELAY)
                                reconnects = 0
                                search_attempts = 0

                                break

                            else:
                                consecutive_parse_failures += 1
                                print_warning(
                                    f"[FUNCTIONAL] Non-match big packet "
                                    f"(#{consecutive_parse_failures}/{MAX_CONSECUTIVE_PARSE_FAILURES}) "
                                    f"| token={bool(token)} | udp_key={bool(udp_key)} "
                                    f"| code={bool(match_code)} | server={bool(server_ip_port)} "
                                    f"→ reconnecting"
                                )
                                try:
                                    writer.close()
                                    await writer.wait_closed()
                                except Exception:
                                    pass
                                writer = None
                                await asyncio.sleep(NON_MATCH_RECONNECT_DELAY)
                                break

                        except Exception as e:
                            print_error(f"[FUNCTIONAL] Match packet error: {e}")
                            import traceback
                            traceback.print_exc()
                            consecutive_parse_failures += 1
                            try:
                                writer.close()
                                await writer.wait_closed()
                            except Exception:
                                pass
                            writer = None
                            await asyncio.sleep(NON_MATCH_RECONNECT_DELAY)
                            break

                    if 30 <= packet_length <= 40:
                        continue

            except asyncio.CancelledError:
                print_warning(f"[FUNCTIONAL] Cancelled — cancelling {len(play_matches)} UDP matches")
                for m in play_matches:
                    if not m.done():
                        m.cancel()
                if play_matches:
                    await asyncio.gather(*play_matches, return_exceptions=True)
                play_matches.clear()
                raise
            except Exception as e:
                print_error(f"[FUNCTIONAL] TCP state ({uid_str}): {e}")
                play_matches[:] = [m for m in play_matches if not m.done()]

                if "Cache expired" in str(e):
                    print_warning(f"[FUNCTIONAL] Triggering re-login for {uid_str}")
                    break

                if writer:
                    try:
                        writer.close()
                        await writer.wait_closed()
                    except Exception:
                        pass

                # إعادة الاتصال الفوري مع تصفير العدادات
                search_attempts = 0
                reconnects += 1
                if reconnects > max_reconnects:
                    print_error("[FUNCTIONAL] Max reconnects reached, retrying...")
                    reconnects = 0
                    await asyncio.sleep(3)
                    continue

                await asyncio.sleep(min(reconnects, 2))

    except asyncio.CancelledError:
        print_warning(f"[FUNCTIONAL] Outer cancelled. {len(play_matches)} UDP matches still running.")
        for m in play_matches:
            if not m.done():
                m.cancel()
        if play_matches:
            await asyncio.gather(*play_matches, return_exceptions=True)
        play_matches.clear()
        raise


async def informational(addrs, starter_packet, key, iv, region="ME", max_reconnects=3):
    reconnects = 0
    ip, port = addrs.split(":")
    while True:
        writer = None
        ping_task = None
        try:
            resolved_ip = await resolve_host_cloudflare(ip)
            reader, writer = await asyncio.open_connection(resolved_ip, int(port))

            raw_sock = writer.get_extra_info('socket')
            if raw_sock:
                optimize_tcp_socket(raw_sock)

            writer.write(bytes.fromhex(starter_packet))
            await writer.drain()
            reconnects = 0

            try:
                init_ka = await send_keep_alive(region)
                if init_ka and writer and not writer.is_closing():
                    writer.write(init_ka)
                    await asyncio.wait_for(writer.drain(), timeout=3)
            except Exception:
                pass

            async def info_keepalive():
                ka_bytes = await send_keep_alive(region)
                while True:
                    await asyncio.sleep(5)
                    try:
                        if writer and not writer.is_closing():
                            writer.write(ka_bytes)
                            await writer.drain()
                    except Exception:
                        break

            ping_task = asyncio.create_task(info_keepalive())

            while True:
                data = await reader.read(8192)
                if not data:
                    raise ConnectionError("Connection closed")
        except asyncio.CancelledError:
            if ping_task:
                ping_task.cancel()
            if writer:
                try:
                    writer.close()
                    await writer.wait_closed()
                except Exception:
                    pass
            raise
        except Exception:
            if ping_task:
                ping_task.cancel()
            if writer:
                try:
                    writer.close()
                    await writer.wait_closed()
                except Exception:
                    pass
            reconnects += 1
            if reconnects > max_reconnects:
                await asyncio.sleep(3)
                reconnects = 0
            else:
                await asyncio.sleep(1)


# ==================== ACCOUNT PROCESSORS ====================
def _extract_int_field(dict_res, field_num, default):
    v = get_proto_field(dict_res, field_num, None)
    if v is None and isinstance(dict_res, dict):
        entry = dict_res.get(str(field_num))
        if isinstance(entry, dict):
            v = entry.get('data')
            if isinstance(v, dict):
                v = None
    if v is None:
        return default
    try:
        return int(v)
    except (ValueError, TypeError):
        s = ''.join(c for c in str(v) if c.isdigit())
        return int(s) if s else default


async def refresh_account_profile(account_data_or_uid: Any):
    try:
        if isinstance(account_data_or_uid, str):
            return None
        account_data = account_data_or_uid
        if not account_data:
            return None

        url = account_data.get('server_url')
        token = account_data.get('token')
        release_version = account_data.get('release_version')
        payload = account_data.get('login_payload_data')

        if not (url and token and release_version and payload):
            return None

        res = await send_getlogin(payload, url, token, release_version,
                                  fallback_base_url=account_data.get("config_server_url"))
        if res:
            res_proto, dict_res = res
            level = _extract_int_field(dict_res, 6, 1)
            exp = _extract_int_field(dict_res, 7, 0)
            likes = _extract_int_field(dict_res, 8, 0)

            nickname = None
            try:
                nickname = res_proto.nickname
            except Exception:
                pass
            if not nickname and isinstance(dict_res, dict):
                entry4 = dict_res.get('4')
                if entry4:
                    nickname = _deep_get_string(entry4) or ""

            if level <= 0: level = 1
            if exp < 0: exp = 0
            account_data['level'] = level
            account_data['exp'] = exp
            account_data['likes'] = max(0, likes)
            if nickname:
                account_data['nickname'] = nickname
            persist_worker_profile(account_data)
            print_info(f"[EXP-REFRESH] UID {account_data.get('account_id')} -> Level: {level}, EXP: {exp}")
            return level
    except Exception as e:
        print_error(f"refresh_account_profile error: {e}")
        return None


async def process_account_uid_pass(uid: str, password: str) -> Optional[Dict]:
    print_info(f"[LOGIN] Full login for UID {uid}...")
    try:
        async with _LOGIN_SEMAPHORE:
            print_info(f"[STEP 1] Fetching version config...")
            verconfig_res = await version_config()
            if verconfig_res is None:
                print_error("[STEP 1] FAILED: version_config returned None")
                return None
            release_version, client_version, server_url = verconfig_res
            print_success(f"[STEP 1] OK | release={release_version} | client={client_version}")

            print_info(f"[STEP 2] Getting access token via OAuth...")
            tokengrant_response = await get_access_token(uid, password)
            if tokengrant_response is None:
                print_error(f"[STEP 2] FAILED: OAuth failed (wrong UID/password?)")
                return None
            open_id, access_token, platform = tokengrant_response
            print_success(f"[STEP 2] OK | open_id={open_id[:12]}... | platform={platform}")

            print_info(f"[STEP 3] Building MajorLogin payload...")
            device_info = get_device_for_account(uid)
            login_payload_data = await build_majorlogin_payload(open_id, access_token, platform, client_version, device_info)
            if login_payload_data is None:
                print_error("[STEP 3] FAILED: build_majorlogin_payload returned None")
                return None
            print_success(f"[STEP 3] OK | payload size = {len(login_payload_data)} bytes")

            print_info(f"[STEP 4] Sending MajorLogin...")
            majorlogin_response = await send_majorlogin(login_payload_data, release_version, server_url)
            if majorlogin_response is None:
                print_error("[STEP 4] FAILED: send_majorlogin returned None")
                return None

            acc_id = str(majorlogin_response.account_id)
            print_success(
                f"[STEP 4] OK | account_id={acc_id} | region={majorlogin_response.region} | "
                f"has_token={bool(majorlogin_response.token)}"
            )

            if acc_id == "0" or not acc_id or acc_id == "None":
                print_error(f"[STEP 4] REJECTED: account_id=0 → server refused login")
                return None

            print_info(f"[STEP 5] Sending GetLoginData...")
            getlogin_result = await send_getlogin(
                login_payload_data,
                majorlogin_response.url or server_url,
                majorlogin_response.token,
                release_version,
                fallback_base_url=server_url
            )
            if getlogin_result is None:
                print_error("[STEP 5] FAILED: send_getlogin returned None")
                return None

            res_proto, dict_res = getlogin_result
            fa = getattr(res_proto, 'functional_addrs', None)
            ia = getattr(res_proto, 'informational_addrs', None)
            print_success(f"[STEP 5] OK | functional={fa} | informational={ia}")

        if not fa or not isinstance(fa, str) or ":" not in fa:
            print_error(f"[STEP 5] REJECTED: invalid functional_addrs = {fa}")
            return None

        level = _extract_int_field(dict_res, 6, 1)
        exp = _extract_int_field(dict_res, 7, 0)
        likes = _extract_int_field(dict_res, 8, 0)

        nickname = None
        try:
            nickname = res_proto.nickname
        except Exception:
            pass
        if not nickname and isinstance(dict_res, dict):
            entry4 = dict_res.get('4')
            if entry4:
                nickname = _deep_get_string(entry4)
        if not nickname:
            nickname = f"Player_{acc_id}"

        region = None
        try:
            region = majorlogin_response.region
        except Exception:
            pass
        if not region and isinstance(dict_res, dict):
            entry3 = dict_res.get('3')
            if entry3:
                region = _deep_get_string(entry3)
        if not region:
            region = "ME"

        if level <= 0: level = 1
        if exp < 0: exp = 0

        key_val = majorlogin_response.aes_ak
        iv_val = majorlogin_response.iv_i
        if not isinstance(key_val, (bytes, bytearray)) or len(key_val) < 16:
            key_val = AES_KEY
        if not isinstance(iv_val, (bytes, bytearray)) or len(iv_val) < 16:
            iv_val = AES_IV

        print_success(f"[STEP 6] OK | nickname={nickname} | level={level} | exp={exp} | region={region}")
        print_success(f"[STEP 7] OK | key={len(key_val)}B | iv={len(iv_val)}B")

        initial_mode = "LW" if level >= LONE_WOLF_MIN_LEVEL else "BR"
        print_success(f"[LOGIN OK] UID {acc_id} | {nickname} | Lvl {level} | Mode: {initial_mode}")

        account_data = {
            'account_id': majorlogin_response.account_id,
            'nickname': nickname,
            'region': region,
            'level': level,
            'exp': exp,
            'likes': max(0, likes),
            'open_id': open_id,
            'access_token': access_token,
            'platform': str(platform),
            'token': majorlogin_response.token,
            'server_time': majorlogin_response.server_time,
            'aes_ak': key_val,
            'iv_i': iv_val,
            'functional_addrs': fa,
            'informational_addrs': ia,
            'release_version': release_version,
            'client_version': client_version,
            'server_url': majorlogin_response.url or server_url,
            'config_server_url': server_url,
            'login_payload_data': login_payload_data,
            'auth_type': 'guest',
            'auth_uid': uid,
            'auth_password': password
        }
        persist_worker_profile(account_data)
        return account_data
    except Exception as e:
        print_error(f"process_account_uid_pass error: {e}")
        import traceback
        traceback.print_exc()
        return None


async def run_account_worker(account_data: Dict, label: str):
    acc_id = str(account_data['account_id'])
    informational_task = None
    exp_task = None
    functional_task = None
    try:
        reg = account_data.get('region', 'ME')
        func_addr = account_data.get('functional_addrs')
        info_addr = account_data.get('informational_addrs')

        if not func_addr or not isinstance(func_addr, str) or ":" not in func_addr:
            print_warning(f"[!] No functional_addrs for {acc_id} — worker idle")
            while True:
                await asyncio.sleep(60)
            return

        tcp_packet_online = await build_tcp_startup_packet(
            account_data['account_id'],
            account_data['token'],
            account_data['server_time'],
            account_data['aes_ak'],
            account_data['iv_i'],
            region=reg,
            typ='OnLine'
        )

        tcp_packet_chat = await build_tcp_startup_packet(
            account_data['account_id'],
            account_data['token'],
            account_data['server_time'],
            account_data['aes_ak'],
            account_data['iv_i'],
            region=reg,
            typ='ChaT'
        )

        if info_addr and isinstance(info_addr, str) and ":" in info_addr:
            informational_task = asyncio.create_task(
                informational(
                    info_addr,
                    tcp_packet_chat,
                    account_data['aes_ak'],
                    account_data['iv_i'],
                    region=reg
                )
            )

        async def exp_refresher():
            while True:
                await asyncio.sleep(90)
                try:
                    await refresh_account_profile(account_data)
                except Exception:
                    pass

        exp_task = asyncio.create_task(exp_refresher())

        functional_task = asyncio.create_task(
            functional_br(
                func_addr,
                tcp_packet_online,
                account_data['region'],
                account_data['client_version'],
                account_data['aes_ak'],
                account_data['iv_i'],
                account_id=acc_id,
                account_data=account_data
            )
        )

        await functional_task

    except asyncio.CancelledError:
        raise
    except Exception as e:
        print_error(f"run_account_worker error for {label}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        for t in (informational_task, exp_task, functional_task):
            if t and not t.done():
                t.cancel()
        for t in (informational_task, exp_task, functional_task):
            if t:
                try:
                    await t
                except (asyncio.CancelledError, Exception):
                    pass


async def account_loop_guest(uid: str, password: str):
    uid_str = str(uid)
    while True:
        try:
            if account_is_deleted(uid_str):
                log(f"[CONTROL] UID {uid_str} has been deleted; account loop stopped.")
                return
            while account_is_paused(uid_str) and not account_is_deleted(uid_str):
                await asyncio.sleep(1.0)
            if account_is_deleted(uid_str):
                log(f"[CONTROL] UID {uid_str} has been deleted; account loop stopped.")
                return
            if os.environ.get("WEB_MODE") == "1":
                for saved_account in await _read_web_accounts_live():
                    if str(saved_account.get("uid")) == uid_str:
                        password = str(saved_account.get("password") or password)
                        break
            print_info(f"[LOGIN] Starting login for Guest UID: {uid_str}...")
            generation_before_login = account_restart_generation(uid_str)
            account_data = await process_account_uid_pass(uid_str, password)
            if account_is_deleted(uid_str):
                log(f"[CONTROL] UID {uid_str} deleted during login; account loop stopped.")
                return
            if account_restart_generation(uid_str) != generation_before_login:
                log(f"[CONTROL] Restart requested during login for UID {uid_str}; repeating authentication.")
                continue
            if not account_data:
                print_error(f"Login failed for UID: {uid_str}. Retrying in 15 seconds...")
                await asyncio.sleep(15)
                continue
            await run_account_worker(account_data, uid_str)
            print_warning(f"Session finished for {uid_str}. Reconnecting in 3s...")
            await asyncio.sleep(3)
        except asyncio.CancelledError:
            print_warning(f"Worker for {uid_str} stopped.")
            break
        except Exception as e:
            print_error(f"Error for UID {uid_str}: {e}. Retrying in 10s...")
            await asyncio.sleep(10)


# ======================================================================
# ========== BotWorker + BotManager ====================================
# ======================================================================
try:
    from database import update_game_account
except Exception:
    def update_game_account(*args, **kwargs):
        pass


class BotWorker:
    def __init__(self, account_id: int, uid: str, password: str,
                 mode: str = "admin", max_matches: int = 500, on_update=None):
        self.account_id = account_id
        self.uid = str(uid)
        self.password = str(password)
        self.region = ACCOUNT_REGION
        self.mode = mode
        self.max_matches = max_matches
        self.on_update = on_update
        self._stop_event: Optional[asyncio.Event] = None
        self._task: Optional[asyncio.Task] = None

        self.status = "idle"
        self.level = 1
        self.exp = 0
        self.last_exp = 0
        self.nickname = None
        self.game_id = None
        self.matches_played = 0
        self.exp_gained = 0
        self.active_matches = 0
        self.message = ""

    def _ensure_loop_primitives(self):
        if self._stop_event is None:
            self._stop_event = asyncio.Event()

    def spawn(self):
        self._ensure_loop_primitives()
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._account_loop())
        return self._task

    def request_stop(self):
        if self._stop_event is not None:
            self._stop_event.set()

    def is_alive(self) -> bool:
        return self._task is not None and not self._task.done()

    def snapshot(self):
        return {
            "account_id": self.account_id, "uid": self.uid, "status": self.status,
            "level": self.level, "exp": self.exp, "last_exp": self.last_exp,
            "nickname": self.nickname, "game_id": self.game_id,
            "matches_played": self.matches_played, "exp_gained": self.exp_gained,
            "active_matches": self.active_matches, "message": self.message,
        }

    def _emit(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        if self.on_update:
            try: self.on_update(self.snapshot())
            except Exception: pass

    async def _account_loop(self):
        self._emit(status="starting", message="Authenticating...")
        backoff = 10
        while not self._stop_event.is_set():
            try:
                account_data = await process_account_uid_pass(self.uid, self.password)
                if self._stop_event.is_set():
                    break
                if not account_data:
                    self._emit(status="error", message="Login failed, retrying")
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 1.5, 120)
                    continue

                backoff = 10
                self.level = int(account_data.get("level", 1) or 1)
                self.exp = int(account_data.get("exp", 0) or 0)
                self.last_exp = self.exp
                self.nickname = account_data.get("nickname") or f"Player_{self.uid}"
                self.game_id = str(account_data.get("account_id") or "")

                if self.matches_played == 0:
                    self.matches_played = 1
                    self.exp_gained = 1

                self._emit(
                    status="online",
                    message=f"Connected | Lvl {self.level} | EXP {self.exp}",
                    level=self.level, exp=self.exp, last_exp=self.last_exp,
                    nickname=self.nickname, game_id=self.game_id,
                    matches_played=self.matches_played, exp_gained=self.exp_gained,
                )

                await run_account_worker(account_data, self.uid)

                if self._stop_event.is_set():
                    break
                self._emit(status="reconnecting", message="Session ended, reconnecting...")
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._emit(status="error", message=f"{type(e).__name__}: {e}")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 1.5, 120)


class BotManager:
    def __init__(self):
        self.workers: Dict[int, BotWorker] = {}
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._loop_thread: Optional[threading.Thread] = None
        self._loop_ready = threading.Event()
        self._lock = threading.RLock()

    def start_loop(self):
        with self._lock:
            if self._loop_thread and self._loop_thread.is_alive():
                return

            def _runner():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                self._loop = loop
                try:
                    loop.run_until_complete(self._bootstrap())
                    loop.run_forever()
                finally:
                    try:
                        loop.close()
                    except Exception:
                        pass

            self._loop_thread = threading.Thread(target=_runner, daemon=True, name="FF-Bot-Loop")
            self._loop_thread.start()
            self._loop_ready.wait(timeout=10)

    async def _bootstrap(self):
        self._loop_ready.set()

    def stop_loop(self):
        with self._lock:
            loop = self._loop
            if loop is None or not loop.is_running():
                return

            async def _cancel_all():
                tasks = [w._task for w in self.workers.values() if w._task and not w._task.done()]
                for t in tasks:
                    t.cancel()
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)

            try:
                fut = asyncio.run_coroutine_threadsafe(_cancel_all(), loop)
                fut.result(timeout=5)
            except Exception:
                pass
            loop.call_soon_threadsafe(loop.stop)

    def _run_on_loop(self, coro, timeout: float = 5.0):
        loop = self._loop
        if loop is None or not loop.is_running():
            raise RuntimeError("Bot loop not running")
        fut = asyncio.run_coroutine_threadsafe(coro, loop)
        return fut.result(timeout=timeout)

    def _on_update(self, snapshot: dict):
        aid = snapshot["account_id"]
        try:
            update_game_account(
                aid, status=snapshot["status"],
                level=snapshot.get("level") or 1,
                exp=snapshot.get("exp") or 0,
                last_exp=snapshot.get("last_exp") or 0,
                nickname=snapshot.get("nickname"),
                game_id=snapshot.get("game_id"),
                matches_played=snapshot.get("matches_played") or 0,
                exp_gained=snapshot.get("exp_gained") or 0,
            )
        except Exception:
            pass

    def start_account(self, account_row: dict) -> bool:
        self.start_loop()
        aid = account_row["id"]

        async def _spawn_in_loop():
            with self._lock:
                existing = self.workers.get(aid)
                if existing and existing.is_alive():
                    return True
                mode = str(account_row.get("mode") or "admin").lower()
                if mode not in ("admin", "risk"):
                    mode = "admin"
                max_matches = int(account_row.get("max_matches") or 500) if mode == "admin" else 10**9
                w = BotWorker(
                    account_id=aid,
                    uid=str(account_row["uid"]),
                    password=str(account_row["password"]),
                    mode=mode,
                    max_matches=max_matches,
                    on_update=self._on_update,
                )
                self.workers[aid] = w
                w.spawn()
                return True

        try:
            return self._run_on_loop(_spawn_in_loop(), timeout=5)
        except Exception as e:
            print_error(f"start_account failed: {e}")
            return False

    def stop_account(self, account_id: int):
        async def _stop():
            w = self.workers.get(account_id)
            if not w:
                return
            w.request_stop()
            if w._task and not w._task.done():
                try:
                    await asyncio.wait_for(asyncio.shield(w._task), timeout=2.0)
                except (asyncio.TimeoutError, asyncio.CancelledError, Exception):
                    try:
                        w._task.cancel()
                    except Exception:
                        pass
            self.workers.pop(account_id, None)

        try:
            self._run_on_loop(_stop(), timeout=6)
        except Exception as e:
            print_error(f"stop_account failed: {e}")

    def stop_all(self, account_ids: Optional[List[int]] = None):
        async def _stop_all():
            target_ids = list(self.workers.keys()) if account_ids is None else list(account_ids)
            for aid in target_ids:
                w = self.workers.get(aid)
                if not w:
                    continue
                w.request_stop()
            await asyncio.sleep(0.5)
            for aid in target_ids:
                w = self.workers.get(aid)
                if not w:
                    continue
                if w._task and not w._task.done():
                    try:
                        w._task.cancel()
                    except Exception:
                        pass
                self.workers.pop(aid, None)

        try:
            self._run_on_loop(_stop_all(), timeout=10)
        except Exception as e:
            print_error(f"stop_all failed: {e}")

    def status(self, account_id: int) -> Optional[dict]:
        w = self.workers.get(account_id)
        return w.snapshot() if w else None

    def is_running(self, account_id: int) -> bool:
        w = self.workers.get(account_id)
        return bool(w and w.is_alive())

    def all_snapshots(self) -> Dict[int, Dict]:
        return {aid: w.snapshot() for aid, w in self.workers.items()}

    def active_matches(self, account_id: int) -> int:
        w = self.workers.get(account_id)
        if not w:
            return 0
        try:
            return int(getattr(w, "active_matches", 0) or 0)
        except Exception:
            return 0


bot_manager = BotManager()


# ==================== ACCOUNTS LOADER ====================
def _prompt_credentials():
    accounts_file = os.environ.get("ACCOUNTS_FILE") if os.environ.get("WEB_MODE") == "1" else None
    if accounts_file:
        accounts = []
        try:
            with open(accounts_file, "r", encoding="utf-8") as f:
                for raw in f:
                    line = raw.strip()
                    if not line or line.startswith("#"):
                        continue
                    if ":" not in line:
                        log(f"[!] Ignoring invalid account line: {line}")
                        continue
                    uid, password = line.split(":", 1)
                    uid, password = uid.strip(), password.strip()
                    if uid and password:
                        accounts.append({"uid": uid, "password": password})
            if not accounts:
                raise ValueError("accounts.txt is empty")
            print(f"[i] Loaded {len(accounts)} accounts from {accounts_file}")
            return accounts
        except Exception as e:
            print(f"[-] Could not load accounts file: {e}")
            return []
    print("[i] Enter account UID and Password")
    uid = input("UID: ").strip()
    password = input("Password: ").strip()
    accounts = [{"uid": uid, "password": password}]
    return accounts


async def _read_web_accounts_live():
    accounts_file = os.environ.get("ACCOUNTS_FILE") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "accounts.txt")
    accounts = []
    try:
        with open(accounts_file, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#") or ":" not in line:
                    continue
                uid, password = line.split(":", 1)
                uid, password = uid.strip(), password.strip()
                if uid and password:
                    accounts.append({"uid": uid, "password": password})
    except Exception as exc:
        log(f"[WEB] Could not reload account list: {type(exc).__name__}: {exc}")
    return accounts


async def web_account_supervisor():
    tasks = {}
    try:
        while True:
            current = await _read_web_accounts_live()
            desired = {str(a["uid"]): str(a["password"]) for a in current}

            for uid, task in list(tasks.items()):
                if task.done():
                    try:
                        task.result()
                    except (asyncio.CancelledError, Exception):
                        pass
                    tasks.pop(uid, None)

            for uid, password in desired.items():
                if uid not in tasks:
                    log(f"[WEB] Discovered account UID {uid}; launching its worker")
                    tasks[uid] = asyncio.create_task(account_loop_guest(uid, password))
                else:
                    task_password = getattr(tasks[uid], "_rex_saved_password", None)
                    if task_password is None:
                        setattr(tasks[uid], "_rex_saved_password", password)
                    elif task_password != password:
                        controls = _account_controls_snapshot().copy()
                        state = controls.get(uid, {})
                        if not isinstance(state, dict): state = {}
                        state["restart_generation"] = int(state.get("restart_generation", 0) or 0) + 1
                        controls[uid] = state
                        tmp = CONTROL_FILE + ".tmp"
                        try:
                            with open(tmp, "w", encoding="utf-8") as f:
                                json.dump(controls, f, ensure_ascii=False, indent=2)
                            os.replace(tmp, CONTROL_FILE)
                            global _CONTROL_CACHE_SIGNATURE
                            _CONTROL_CACHE_SIGNATURE = None
                            setattr(tasks[uid], "_rex_saved_password", password)
                            log(f"[WEB] Password changed for UID {uid}; restarting after active match")
                        except Exception as exc:
                            log(f"[WEB] Could not update restart state for UID {uid}: {type(exc).__name__}")

            await asyncio.sleep(2.0)
    finally:
        for task in tasks.values():
            if not task.done():
                task.cancel()
        if tasks:
            await asyncio.gather(*tasks.values(), return_exceptions=True)


def _prompt_region():
    print("[i] Available Regions: ME, IND, SG, TH, PH, VN, MY, ID, HK, TW, BD, PK, CIS, BR, NA, SAC, EUROPE")
    region = input("Region (default ME): ").strip().upper()
    if not region:
        region = "ME"
    if region not in REGION_PREFIX:
        print(f"[!] Unknown region '{region}', falling back to ME")
        region = "ME"
    return region


async def main():
    global ACCOUNT_REGION

    print_colored("=" * 60, Colors.CYAN)
    print_colored("    TEAM 84FF - FreeFire Level Up Bot (BR + Lone Wolf Auto)", Colors.GREEN)
    print_colored("   Persistent Device ID + TRUE Parallel + Smart DNS", Colors.WHITE)
    print_colored("=" * 60, Colors.CYAN)
    print_info(f"Start Match Interval: {START_MATCH_INTERVAL}s")
    print_info(f"Offline Wait: {NEW_MATCH_DELAY}s (after match found)")
    print_info(f"Non-match Reconnect: {NON_MATCH_RECONNECT_DELAY}s")
    print_info(f"Parallel Matches: UNLIMITED (background)")
    print_info(f"BR Mode: mode={BR_MODE_ID}, map={BR_MAP_ID} (Level < {LONE_WOLF_MIN_LEVEL})")
    print_info(f"Lone Wolf Mode: mode={LW_MODE_ID}, map={LW_MAP_ID} (Level >= {LONE_WOLF_MIN_LEVEL})")
    print_info(f"Match Idle Timeout: {MATCH_IDLE_TIMEOUT}s")
    print_colored("=" * 60, Colors.CYAN)

    accounts = _prompt_credentials()
    if os.environ.get("WEB_MODE") == "1":
        region = os.environ.get("ACCOUNT_REGION", "ME").strip().upper() or "ME"
        if region not in REGION_PREFIX:
            log(f"[!] Invalid ACCOUNT_REGION '{region}' from web settings; falling back to ME")
            region = "ME"
    else:
        region = _prompt_region()

    ACCOUNT_REGION = region
    print(f"[i] Using Region: {ACCOUNT_REGION}")

    log(f"[*] Starting bot for {len(accounts)} accounts...")

    if os.environ.get("WEB_MODE") == "1":
        log("[WEB] Dynamic per-account supervisor enabled; account add/delete/control changes are watched live")
        await web_account_supervisor()
        return

    tasks = []
    for i, acc in enumerate(accounts, 1):
        uid = acc["uid"]
        password = acc["password"]
        log(f"[*] Launching worker {i} | UID: {uid}")
        tasks.append(asyncio.create_task(account_loop_guest(uid, password)))

    try:
        await asyncio.gather(*tasks)
    except (KeyboardInterrupt, asyncio.CancelledError):
        log("[!] Shutting down all workers...")
        for t in tasks:
            t.cancel()
        for t in tasks:
            try:
                await t
            except (asyncio.CancelledError, Exception):
                pass
        log("[+] All sessions cleanly closed.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print_warning("\nProgram stopped by user.")
