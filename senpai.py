# SENPAI X SHIVAM V12 TG SUPER FAST

"""
=============================================================================
           TELEGRAM MULTI-BOT ALL-IN-ONE MANAGEMENT SCRIPT
=============================================================================
Architecture:
- Single-file self-contained design.
- Multi-token engine supporting up to 10 Telegram bot instances concurrently.
- One centralized OWNER_ID with complete administrative authority.
- Sudo/admin authorization system (/addsudo, /delsudo, /sudolist).
- Centralized permission enforcement decorator (@requires_auth).
- General utility commands (/help, /ping, /uptime, /status).
- NC Feature: exactly 6 isolated configuration slots (/nc, /setnc, /delnc).
- Message Features:
    * 4-Message Sequence feature (/msg4, /setmsg4)
    * 2-Slide Interactive Card feature (/slide2, /setslide)
- Single embedded local SQLite persistence layer (bot_data.db).
- Clean, minimal terminal startup telemetry and graceful shutdown handling.
=============================================================================
"""

import asyncio
import contextlib
import datetime
import functools
import html
import logging
import os
import random
import re
import signal
import sqlite3
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional, Set, Tuple, Union

# Ensure UTF-8 output encoding across Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Third-party Telegram Bot API library
import telegram
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.constants import ParseMode
from telegram.error import (
    BadRequest,
    Forbidden,
    InvalidToken,
    NetworkError,
    TelegramError,
)

FloodWaitError = telegram.error.RetryAfter
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ---------------------------------------------------------------------------
# LOGGING CONFIGURATION (Clean & Minimal)
# ---------------------------------------------------------------------------
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger("MultiBotApp")

# Suppress verbose HTTP connection debugging logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("telegram.ext").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)
logging.getLogger("apscheduler.scheduler").setLevel(logging.WARNING)


# ---------------------------------------------------------------------------
# CORE CONFIGURATION & CONSTANTS
# ---------------------------------------------------------------------------
# OWNER_ID: Master owner with unrestricted access
OWNER_ID: int = int(os.getenv("OWNER_ID", "7315714860"))

# Maximum limits defined by specifications
MAX_BOT_TOKENS: int = 10
MAX_NC_SLOTS: int = 6
MAX_MSG4_SLOTS: int = 4
MAX_SLIDE2_SLOTS: int = 2
DEFAULT_NC_COMMANDS: Tuple[str, ...] = (
    "momnc",
    "fstnc",
    "nightnc",
    "coolnc",
    "runnc",
    "glitchnc",
)

NC_INTERVAL = 0.001
TASK_TEST_MODE = os.getenv("TASK_TEST_MODE", "0") == "1"
RUNNC_EMOJIS: Tuple[str, ...] = (
    "❤️", "🩷", "🧡", "💛", "💚", "💙", "💜", "🖤", "🤍", "🤎",
    "💔", "❤️‍🔥", "❤️‍🩹", "💕", "💞", "💓", "💗", "💖", "💘", "💝",
    "💟", "❣️", "💌", "💖", "⭐", "🌟", "✨", "💫",
)
GLITCHNC_EMOJIS: Tuple[str, ...] = (
    "☽🌟☾", "✦🖤✧", "༒︎💀༒︎", "𖤐😈𖤐", "✞︎🦇✞︎", "⛧👁️⛧",
    "𖣂🕷️𖣂", "☥🦂☥", "⚚🐍⚚", "♜🦅♜", "𖤓🐉𖤓", "✧🪽✦",
    "⟡🪬⟡", "⌘🛸⌘", "⌬🛰️⌬", "☾🌙☽", "☄︎💫☄︎", "⟁⚡⟁",
    "❖🔥❖", "◇💎◇", "𖦹🌌𖦹", "✩🌠✩", "⛤🥀⛤", "༺🌹༻",
    "࿔🪷࿔", "꧁🌸꧂", "✟🖤✟", "☠︎︎🧿☠︎︎", "𖧷🦋𖧷", "𖥔🪻𖥔",
    "⚜️🎭⚜️", "♱🕯️♱", "⛓︎🔗⛓︎", "𖨂🪩𖨂", "⌖🎴⌖", "◈🃏◈",
)
SLIDE2_REPLY_EMOJIS: Tuple[str, ...] = (
    "☾😂☽", "☽🤣☾", "☾😆☽", "☽😅☾", "☾😹☽", "☽😄☾", "☾😃☽",
    "☽😀☾", "☾😁☽", "☽😸☾", "☾😺☽", "☽😻☾", "☾🤭☽", "☽🤪☾",
    "☾😜☽", "☽😝☾", "☾😛☽", "☽🫠☾", "☾😭☽", "☽💀☾",
)
COOLNC_SYMBOLS: Tuple[str, ...] = (
    "☠︎︎", "༒︎", "✞︎", "🕸", "𖤐", "✟", "⚚", "🦇", "🕷", "⚔︎",
    "🦂", "☦︎", "☯︎", "♰", "♱", "♠︎", "♣︎", "♦︎", "♥︎", "⚡", "☄︎",
    "☽", "☾", "✦", "✧", "★", "☆", "✩", "✪", "✫", "✬", "✭", "✮",
    "✯", "✰", "𓆩", "𓆪", "𓂀", "𖣂", "𖤓", "𖥔", "𖦹", "𖧷", "𖨆", "𖠋",
    "𖠌", "𖢻", "𖣘", "𖥂", "𖦪", "𖧧", "𖨂", "𖣔", "𖥧", "𖦏", "𖧰",
)

NC_GROUPS: Dict[int, List[str]] = {
    1: [
        "ꪶ🩷ꫂ {target} 𝘽𝙇𝙊𝙊𝘿𝙔 𝙈𝙊𝙏𝙃𝙀𝙍𝙁𝙐𝘾𝙆𝙀𝙍 𒌐",
        "ꪶ❤️ꫂ {target} 𝘽𝙇𝙊𝙊𝘿𝙔 𝙈𝙊𝙏𝙃𝙀𝙍𝙁𝙐𝘾𝙆𝙀𝙍 𒌐",
        "ꪶ💕ꫂ {target} 𝘽𝙇𝙊𝙊𝘿𝙔 𝙈𝙊𝙏𝙃𝙀𝙍𝙁𝙐𝘾𝙆𝙀𝙍 𒌐",
        "ꪶ💗ꫂ {target} 𝘽𝙇𝙊𝙊𝘿𝙔 𝙈𝙊𝙏𝙃𝙀𝙍𝙁𝙐𝘾𝙆𝙀𝙍 𒌐",
        "ꪶ💕ꫂ {target} 𝘽𝙇𝙊𝙊𝘿𝙔 𝙈𝙊𝙏𝙃𝙀𝙍𝙁𝙐𝘾𝙆𝙀𝙍 𒌐",
        "ꪶ💓ꫂ {target} 𝘽𝙇𝙊𝙊𝘿𝙔 𝙈𝙊𝙏𝙃𝙀𝙍𝙁𝙐𝘾𝙆𝙀𝙍 𒌐",
        "ꪶ💖ꫂ {target} 𝘽𝙇𝙊𝙊𝘿𝙔 𝙈𝙊𝙏𝙃𝙀𝙍𝙁𝙐𝘾𝙆𝙀𝙍 𒌐",
        "ꪶ💘ꫂ {target} 𝘽𝙇𝙊𝙊𝘿𝙔 𝙈𝙊𝙏𝙃𝙀𝙍𝙁𝙐𝘾𝙆𝙀𝙍 𒌐",
        "ꪶ💝ꫂ {target} 𝘽𝙇𝙊𝙊𝘿𝙔 𝙈𝙊𝙏𝙃𝙀𝙍𝙁𝙐𝘾𝙆𝙀𝙍 𒌐",
        "ꪶ🩵ꫂ {target} 𝘽𝙇𝙊𝙊𝘿𝙔 𝙈𝙊𝙏𝙃𝙀𝙍𝙁𝙐𝘾𝙆𝙀𝙍 𒌐",
        "ꪶ💙ꫂ {target} 𝘽𝙇𝙊𝙊𝘿𝙔 𝙈𝙊𝙏𝙃𝙀𝙍𝙁𝙐𝘾𝙆𝙀𝙍 𒌐",
        "ꪶ💜ꫂ {target} 𝘽𝙇𝙊𝙊𝘿𝙔 𝙈𝙊𝙏𝙃𝙀𝙍𝙁𝙐𝘾𝙆𝙀𝙍 𒌐",
        "ꪶ🤍ꫂ {target} 𝘽𝙇𝙊𝙊𝘿𝙔 𝙈𝙊𝙏𝙃𝙀𝙍𝙁𝙐𝘾𝙆𝙀𝙍 𒌐",
        "ꪶ🖤ꫂ {target} 𝘽𝙇𝙊𝙊𝘿𝙔 𝙈𝙊𝙏𝙃𝙀𝙍𝙁𝙐𝘾𝙆𝙀𝙍 𒌐",
        "ꪶ🤎ꫂ {target} 𝘽𝙇𝙊𝙊𝘿𝙔 𝙈𝙊𝙏𝙃𝙀𝙍𝙁𝙐𝘾𝙆𝙀𝙍 𒌐",
        "ꪶ💞ꫂ {target} 𝘽𝙇𝙊𝙊𝘿𝙔 𝙈𝙊𝙏𝙃𝙀𝙍𝙁𝙐𝘾𝙆𝙀𝙍 𒌐",
        "ꪶ💟ꫂ {target} 𝘽𝙇𝙊𝙊𝘿𝙔 𝙈𝙊𝙏𝙃𝙀𝙍𝙁𝙐𝘾𝙆𝙀𝙍 𒌐",
        "ꪶ❣️ꫂ {target} 𝘽𝙇𝙊𝙊𝘿𝙔 𝙈𝙊𝙏𝙃𝙀𝙍𝙁𝙐𝘾𝙆𝙀𝙍 𒌐",
    ],
    2: [
        "{target} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 कितनी बार ¥🤔¥ 𓆩1𓆪 बार ",
        "{target} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 कितनी बार ¥🤔¥ 𓆩2𓆪 बार ",
        "{target} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 कितनी बार ¥🤔¥ 𓆩3𓆪 बार ",
        "{target} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 कितनी बार ¥🤔¥ 𓆩4𓆪 बार ",
        "{target} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 कितनी बार ¥🤔¥ 𓆩5𓆪 बार ",
        "{target} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 कितनी बार ¥🤔¥ 𓆩6𓆪 बार ",
        "{target} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 कितनी बार ¥🤔¥ 𓆩7𓆪 बार ",
        "{target} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 कितनी बार ¥🤔¥ 𓆩8𓆪 बार ",
        "{target} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 कितनी बार ¥🤔¥ 𓆩9𓆪 बार ",
        "{target} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 कितनी बार ¥🤔¥ 𓆩10𓆪 बार ",
        "{target} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 कितनी बार ¥🤔¥ 𓆩11𓆪 बार ",
        "{target} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 कितनी बार ¥🤔¥ 𓆩12𓆪 बार ",
        "{target} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 कितनी बार ¥🤔¥ 𓆩13𓆪 बार ",
        "{target} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 कितनी बार ¥🤔¥ 𓆩14𓆪 बार ",
        "{target} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 कितनी बार ¥🤔¥ 𓆩15𓆪 बार ",
        "{target} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 कितनी बार ¥🤔¥ 𓆩16𓆪 बार ",
        "{target} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 कितनी बार ¥🤔¥ 𓆩17𓆪 बार ",
        "{target} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 कितनी बार ¥🤔¥ 𓆩18𓆪 बार ",
        "{target} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 कितनी बार ¥🤔¥ 𓆩19𓆪 बार ",
        "{target} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 कितनी बार ¥🤔¥ 𓆩20𓆪 बार ",
        "{target} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 कितनी बार ¥🤔¥ 𓆩21𓆪 बार ",
        "{target} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 कितनी बार ¥🤔¥ 𓆩22𓆪 बार ",
        "{target} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 कितनी बार ¥🤔¥ 𓆩23𓆪 बार ",
        "{target} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 कितनी बार ¥🤔¥ 𓆩24𓆪 बार ",
        "{target} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 कितनी बार ¥🤔¥ 𓆩25𓆪 बार ",
        "{target} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 कितनी बार ¥🤔¥ 𓆩26𓆪 बार ",
        "{target} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 कितनी बार ¥🤔¥ 𓆩27𓆪 बार ",
        "{target} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 कितनी बार ¥🤔¥ 𓆩28𓆪 बार ",
        "{target} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 कितनी बार ¥🤔¥ 𓆩29𓆪 बार ",
        "{target} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 कितनी बार ¥🤔¥ 𓆩30𓆪 बार ",
        "{target} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 कितनी बार ¥🤔¥ 𓆩31𓆪 बार ",
        "{target} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 कितनी बार ¥🤔¥ 𓆩32𓆪 बार ",
        "{target} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 कितनी बार ¥🤔¥ 𓆩33𓆪 बार ",
        "{target} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 कितनी बार ¥🤔¥ 𓆩34𓆪 बार ",
        "{target} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 कितनी बार ¥🤔¥ 𓆩35𓆪 बार ",
        "{target} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 कितनी बार ¥🤔¥ 𓆩36𓆪 बार ",
        "{target} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 कितनी बार ¥🤔¥ 𓆩37𓆪 बार ",
        "{target} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 कितनी बार ¥🤔¥ 𓆩38𓆪 बार ",
        "{target} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 कितनी बार ¥🤔¥ 𓆩39𓆪 बार ",
        "{target} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 कितनी बार ¥🤔¥ 𓆩40𓆪 बार ",
        "{target} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 कितनी बार ¥🤔¥ 𓆩41𓆪 बार ",
        "{target} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 कितनी बार ¥🤔¥ 𓆩42𓆪 बार ",
        "{target} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 कितनी बार ¥🤔¥ 𓆩43𓆪 बार ",
        "{target} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 कितनी बार ¥🤔¥ 𓆩44𓆪 बार ",
        "{target} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 कितनी बार ¥🤔¥ 𓆩45𓆪 बार ",
        "{target} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 कितनी बार ¥🤔¥ 𓆩46𓆪 बार ",
        "{target} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 कितनी बार ¥🤔¥ 𓆩47𓆪 बार ",
        "{target} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 कितनी बार ¥🤔¥ 𓆩48𓆪 बार ",
        "{target} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 कितनी बार ¥🤔¥ 𓆩49𓆪 बार ",
        "{target} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 कितनी बार ¥🤔¥ 𓆩50𓆪 बार ",
        
    ],
    3: [
        "《🌑》{target} 𝘚𝘓𝘖𝘞 𝘛𝘈𝘛𝘛𝘌 𝘛𝘜 #𝐒 ᴇ ꪀ ᴘ ᴀꪻ अब्बू  𝘒𝘖 𝘕𝘏𝘐 𝘏𝘈𝘙𝘈 𝘚𝘈𝘒𝘛𝘈",
        "《🌒》{target} 𝘚𝘓𝘖𝘞 𝘛𝘈𝘛𝘛𝘌 𝘛𝘜 #𝐒 ᴇ ꪀ ᴘ ᴀꪻ अब्बू  𝘒𝘖 𝘕𝘏𝘐 𝘏𝘈𝘙𝘈 𝘚𝘈𝘒𝘛𝘈",
        "《🌓》{target} 𝘚𝘓𝘖𝘞 𝘛𝘈𝘛𝘛𝘌 𝘛𝘜 #𝐒 ᴇ ꪀ ᴘ ᴀꪻ अब्बू  𝘒𝘖 𝘕𝘏𝘐 𝘏𝘈𝘙𝘈 𝘚𝘈𝘒𝘛𝘈",
        "《🌔》{target} 𝘚𝘓𝘖𝘞 𝘛𝘈𝘛𝘛𝘌 𝘛𝘜 #𝐒 ᴇ ꪀ ᴘ ᴀꪻ अब्बू  𝘒𝘖 𝘕𝘏𝘐 𝘏𝘈𝘙𝘈 𝘚𝘈𝘒𝘛𝘈",
        "《🌜》{target} 𝘚𝘓𝘖𝘞 𝘛𝘈𝘛𝘛𝘌 𝘛𝘜 #𝐒 ᴇ ꪀ ᴘ ᴀꪻ अब्बू  𝘒𝘖 𝘕𝘏𝘐 𝘏𝘈𝘙𝘈 𝘚𝘈𝘒𝘛𝘈",
        "《🌙》{target} 𝘚𝘓𝘖𝘞 𝘛𝘈𝘛𝘛𝘌 𝘛𝘜 #𝐒 ᴇ ꪀ ᴘ ᴀꪻ अब्बू  𝘒𝘖 𝘕𝘏𝘐 𝘏𝘈𝘙𝘈 𝘚𝘈𝘒𝘛𝘈",
        "《🌚》{target} 𝘚𝘓𝘖𝘞 𝘛𝘈𝘛𝘛𝘌 𝘛𝘜 #𝐒 ᴇ ꪀ ᴘ ᴀꪻ अब्बू  𝘒𝘖 𝘕𝘏𝘐 𝘏𝘈𝘙𝘈 𝘚𝘈𝘒𝘛𝘈",
        "《🌛》{target} 𝘚𝘓𝘖𝘞 𝘛𝘈𝘛𝘛𝘌 𝘛𝘜 #𝐒 ᴇ ꪀ ᴘ ᴀꪻ अब्बू  𝘒𝘖 𝘕𝘏𝘐 𝘏𝘈𝘙𝘈 𝘚𝘈𝘒𝘛𝘈",
        "《☄️》{target} 𝘚𝘓𝘖𝘞 𝘛𝘈𝘛𝘛𝘌 𝘛𝘜 #𝐒 ᴇ ꪀ ᴘ ᴀꪻ अब्बू  𝘒𝘖 𝘕𝘏𝘐 𝘏𝘈𝘙𝘈 𝘚𝘈𝘒𝘛𝘈",
        "《✨》{target} 𝘚𝘓𝘖𝘞 𝘛𝘈𝘛𝘛𝘌 𝘛𝘜 #𝐒 ᴇ ꪀ ᴘ ᴀꪻ अब्बू  𝘒𝘖 𝘕𝘏𝘐 𝘏𝘈𝘙𝘈 𝘚𝘈𝘒𝘛𝘈",

    ],
    4: ["જ⁀➴ {target} 𝙃𝘼𝘾𝙇𝙀 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙆𝙐𝙏𝙄𝙔𝘼",],


    5: ["⁀જ➣ {target} 𝗕𝗘𝗚 𝗙𝗢𝗥 𝗠𝗘𝗥𝗖𝗬 𒀱𒀱𒀱𒀱𒀱𒀱𒀱𒀱𒀱𒀱𒀱𒀱𒀱𒀱𒀱𒀱𒀱𒀱𒀱𒀱𒀱𒀱𒀱𒀱𒀱𒀱𒀱𒀱𒀱𒀱𒀱𒀱𒀱𒀱𒀱𒀱𒀱𒀱𒀱𒀱𒀱𒀱𒀱𒀱",
        
    ],
    6: [

        "➙ {target} 𝗟𝗨𝗡𝗗 𝗖𝗛𝗨𝗠 𝗗𝗨𝗡𝗜𝗬𝗔 𝗚𝗛𝗨𝗠 🦋⃤♡⃤🌈⃤🦋⃤♡⃤🌈⃤🦋⃤♡⃤🌈⃤🦋⃤♡⃤🌈⃤🦋⃤♡⃤🌈⃤🦋⃤♡⃤🌈⃤🦋⃤♡⃤🌈⃤🦋⃤♡⃤🌈⃤🦋⃤♡⃤🌈⃤🦋⃤♡⃤🌈⃤🦋⃤♡⃤🌈⃤🦋⃤♡⃤🌈⃤🦋⃤♡⃤🌈⃤🦋⃤♡⃤🌈⃤🦋⃤♡⃤🌈⃤🦋⃤♡⃤🌈⃤🦋⃤♡⃤🌈⃤🦋⃤♡⃤🌈⃤",
    ],
}

# Preserve the same slot-based NC template list semantics while matching the
# expected ``NC_NAMES`` naming used by the reference implementation.
NC_NAMES: Dict[int, List[str]] = NC_GROUPS

MessageEntry = Union[str, Tuple[str, int]]
MESSAGE_GROUPS: Dict[int, List[MessageEntry]] = {

    1: [
        " {target} ✘ 𝙏𝘼𝙏𝙏𝙀 𝘽𝘼𝘼𝙋 𝙆𝙀 𝙎𝘼𝙈𝙉𝙀 𝙎𝙋𝘼𝙈 𝙆𝘼𝙍𝙀𝙂𝘼 ✘(🙁)\n\n\n" * 20,
        " {target} ✘ 𝙏𝘼𝙏𝙏𝙀 𝘽𝘼𝘼𝙋 𝙆𝙀 𝙎𝘼𝙈𝙉𝙀 𝙎𝙋𝘼𝙈 𝙆𝘼𝙍𝙀𝙂𝘼 ✘(🙂‍↕️)\n\n\n" * 20,
        " {target} ✘ 𝙏𝘼𝙏𝙏𝙀 𝘽𝘼𝘼𝙋 𝙆𝙀 𝙎𝘼𝙈𝙉𝙀 𝙎𝙋𝘼𝙈 𝙆𝘼𝙍𝙀𝙂𝘼 ✘(😀)\n\n\n" * 20,
        " {target} ✘ 𝙏𝘼𝙏𝙏𝙀 𝘽𝘼𝘼𝙋 𝙆𝙀 𝙎𝘼𝙈𝙉𝙀 𝙎𝙋𝘼𝙈 𝙆𝘼𝙍𝙀𝙂𝘼 ✘(😫)\n\n\n" * 20,
        " {target} ✘ 𝙏𝘼𝙏𝙏𝙀 𝘽𝘼𝘼𝙋 𝙆𝙀 𝙎𝘼𝙈𝙉𝙀 𝙎𝙋𝘼𝙈 𝙆𝘼𝙍𝙀𝙂𝘼 ✘(😶‍🌫)\n\n\n" * 20,
        " {target} ✘ 𝙏𝘼𝙏𝙏𝙀 𝘽𝘼𝘼𝙋 𝙆𝙀 𝙎𝘼𝙈𝙉𝙀 𝙎𝙋𝘼𝙈 𝙆𝘼𝙍𝙀𝙂𝘼 ✘(😌)\n\n\n" * 20,
        " {target} ✘ 𝙏𝘼𝙏𝙏𝙀 𝘽𝘼𝘼𝙋 𝙆𝙀 𝙎𝘼𝙈𝙉𝙀 𝙎𝙋𝘼𝙈 𝙆𝘼𝙍𝙀𝙂𝘼 ✘(🫠)\n\n\n" * 20,
        " {target} ✘ 𝙏𝘼𝙏𝙏𝙀 𝘽𝘼𝘼𝙋 𝙆𝙀 𝙎𝘼𝙈𝙉𝙀 𝙎𝙋𝘼𝙈 𝙆𝘼𝙍𝙀𝙂𝘼 ✘(😕)\n\n\n" * 20,
        " {target} ✘ 𝙏𝘼𝙏𝙏𝙀 𝘽𝘼𝘼𝙋 𝙆𝙀 𝙎𝘼𝙈𝙉𝙀 𝙎𝙋𝘼𝙈 𝙆𝘼𝙍𝙀𝙂𝘼 ✘(🧐)\n\n\n" * 20,
        " {target} ✘ 𝙏𝘼𝙏𝙏𝙀 𝘽𝘼𝘼𝙋 𝙆𝙀 𝙎𝘼𝙈𝙉𝙀 𝙎𝙋𝘼𝙈 𝙆𝘼𝙍𝙀𝙂𝘼 ✘(😷)\n\n\n" * 20,
        " {target} ✘ 𝙏𝘼𝙏𝙏𝙀 𝘽𝘼𝘼𝙋 𝙆𝙀 𝙎𝘼𝙈𝙉𝙀 𝙎𝙋𝘼𝙈 𝙆𝘼𝙍𝙀𝙂𝘼 ✘(🙄)\n\n\n" * 20,
        " {target} ✘ 𝙏𝘼𝙏𝙏𝙀 𝘽𝘼𝘼𝙋 𝙆𝙀 𝙎𝘼𝙈𝙉𝙀 𝙎𝙋𝘼𝙈 𝙆𝘼𝙍𝙀𝙂𝘼 ✘(😩)\n\n\n" * 20,
        " {target} ✘ 𝙏𝘼𝙏𝙏𝙀 𝘽𝘼𝘼𝙋 𝙆𝙀 𝙎𝘼𝙈𝙉𝙀 𝙎𝙋𝘼𝙈 𝙆𝘼𝙍𝙀𝙂𝘼 ✘(🤫)\n\n\n" * 20,
        " {target} ✘ 𝙏𝘼𝙏𝙏𝙀 𝘽𝘼𝘼𝙋 𝙆𝙀 𝙎𝘼𝙈𝙉𝙀 𝙎𝙋𝘼𝙈 𝙆𝘼𝙍𝙀𝙂𝘼 ✘(🥸)\n\n\n" * 20,
        " {target} ✘ 𝙏𝘼𝙏𝙏𝙀 𝘽𝘼𝘼𝙋 𝙆𝙀 𝙎𝘼𝙈𝙉𝙀 𝙎𝙋𝘼𝙈 𝙆𝘼𝙍𝙀𝙂𝘼 ✘(😳)\n\n\n" * 20,
        " {target} ✘ 𝙏𝘼𝙏𝙏𝙀 𝘽𝘼𝘼𝙋 𝙆𝙀 𝙎𝘼𝙈𝙉𝙀 𝙎𝙋𝘼𝙈 𝙆𝘼𝙍𝙀𝙂𝘼 ✘(🤣)\n\n\n" * 20,
        " {target} ✘ 𝙏𝘼𝙏𝙏𝙀 𝘽𝘼𝘼𝙋 𝙆𝙀 𝙎𝘼𝙈𝙉𝙀 𝙎𝙋𝘼𝙈 𝙆𝘼𝙍𝙀𝙂𝘼 ✘(😻)\n\n\n" * 20,
        " {target} ✘ 𝙏𝘼𝙏𝙏𝙀 𝘽𝘼𝘼𝙋 𝙆𝙀 𝙎𝘼𝙈𝙉𝙀 𝙎𝙋𝘼𝙈 𝙆𝘼𝙍𝙀𝙂𝘼 ✘(🫤)\n\n\n" * 20,
        " {target} ✘ 𝙏𝘼𝙏𝙏𝙀 𝘽𝘼𝘼𝙋 𝙆𝙀 𝙎𝘼𝙈𝙉𝙀 𝙎𝙋𝘼𝙈 𝙆𝘼𝙍𝙀𝙂𝘼 ✘(😞)\n\n\n" * 20,
        " {target} ✘ 𝙏𝘼𝙏𝙏𝙀 𝘽𝘼𝘼𝙋 𝙆𝙀 𝙎𝘼𝙈𝙉𝙀 𝙎𝙋𝘼𝙈 𝙆𝘼𝙍𝙀𝙂𝘼 ✘(😗)\n\n\n" * 20,
        " {target} ✘ 𝙏𝘼𝙏𝙏𝙀 𝘽𝘼𝘼𝙋 𝙆𝙀 𝙎𝘼𝙈𝙉𝙀 𝙎𝙋𝘼𝙈 𝙆𝘼𝙍𝙀𝙂𝘼 ✘(🤬)\n\n\n" * 20,
        " {target} ✘ 𝙏𝘼𝙏𝙏𝙀 𝘽𝘼𝘼𝙋 𝙆𝙀 𝙎𝘼𝙈𝙉𝙀 𝙎𝙋𝘼𝙈 𝙆𝘼𝙍𝙀𝙂𝘼 ✘(🤧)\n\n\n" * 20,
        " {target} ✘ 𝙏𝘼𝙏𝙏𝙀 𝘽𝘼𝘼𝙋 𝙆𝙀 𝙎𝘼𝙈𝙉𝙀 𝙎𝙋𝘼𝙈 𝙆𝘼𝙍𝙀𝙂𝘼 ✘(🤒)\n\n\n" * 20,
        " {target} ✘ 𝙏𝘼𝙏𝙏𝙀 𝘽𝘼𝘼𝙋 𝙆𝙀 𝙎𝘼𝙈𝙉𝙀 𝙎𝙋𝘼𝙈 𝙆𝘼𝙍𝙀𝙂𝘼 ✘(🥴)\n\n\n" * 20,
        " {target} ✘ 𝙏𝘼𝙏𝙏𝙀 𝘽𝘼𝘼𝙋 𝙆𝙀 𝙎𝘼𝙈𝙉𝙀 𝙎𝙋𝘼𝙈 𝙆𝘼𝙍𝙀𝙂𝘼 ✘(😪)\n\n\n" * 20,
        " {target} ✘ 𝙏𝘼𝙏𝙏𝙀 𝘽𝘼𝘼𝙋 𝙆𝙀 𝙎𝘼𝙈𝙉𝙀 𝙎𝙋𝘼𝙈 𝙆𝘼𝙍𝙀𝙂𝘼 ✘(👺)\n\n\n" * 20,

    ],
    2: [
        "{target} Bₐᵤₙₐ ╰┈➤─ 🌸 ──╮\n\n\n" * 25,
        "{target} ₖᵤₜₜₐD ╰┈➤─ 🌺 ──╮\n\n\n" * 25,
        "{target} Bₑₙ ₖₑ ₗₒDₑ ╰┈➤─ 🌹 ──╮\n\n\n" * 25,
        "{target} ₗₒDₐ Cₕᵤₛ ╰┈➤─ 🌷 ──╮\n\n\n" * 25,
        "{target} ₗₐₐₜ ₖₕₐ ᵣₙDᵤₖₑ ╰┈➤─ 🌼 ──╮\n\n\n" * 25,
        "{target} ₛₐY 𝚂𝙴𝙽𝙿𝙰𝙸 ₚₐₚₐ ╰┈➤─ 🪷 ──╮\n\n\n" * 25,

    ],
    3: [
        "➜ {target} 匚卄ㄩㄒ卂ᗪ 🛐🛐🛐🛐🛐🛐\n\n\n" * 25,
        "➜ {target} 丂ㄥ卂ᐯ乇 ㄥㄩ几ᗪ ㄥ乇 ♌♌♌♌♌♌\n\n\n" * 25,
        "➜ {target} 匚卄卂爪卂尺 ♋♋♋♋♋♋\n\n\n" * 25,
        "➜ {target}  匚卄ㄩㄒ|ㄚ卂 ♈♈♈♈♈\n\n\n" * 25,
        "➜ {target} ᘜ卂几ᗪㄩ ♏♏♏♏♏\n\n\n" * 25,
        "➜ {target} Ҝㄩㄒ|ㄚ卂 ✝️✝️✝️✝️✝️✝️\n\n\n" * 25,
    ],
    4: [
        (f" {{target}} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝘾𝙃𝙐𝘿𝙀𝙂𝙄 « {distance} 𝙆𝙈 » 𝙆𝙄 𝙎𝙋𝙀𝙀𝘿 𝙎𝙀\n\n\n") * 25
        for distance in range(100, 200)
    ],
}


def parse_message_entry(entry: MessageEntry) -> Tuple[str, int]:
    if isinstance(entry, tuple):
        text, repeat_count = entry
        return text, repeat_count
    return entry, 1


def log_message_config() -> None:
    for entries in MESSAGE_GROUPS.values():
        for entry in entries:
            text, repeat_count = parse_message_entry(entry)
            logger.info(
                "[MESSAGE CONFIG] text=%s repeat_count=%s",
                text,
                repeat_count,
            )


SLIDER_MESSAGES: Dict[int, List[str]] = {
    1: [
        "{target} 𝗖𝗛𝗔𝗟 𝗝𝗔𝗠𝗔𝗗𝗔𝗥 𝗞𝗘 𝗟𝗔𝗗𝗞𝗘 𝗡𝗔𝗟𝗜 𝗦𝗔𝗔𝗙 𝗞𝗔𝗥 🧨",
        "{target} 𝗖𝗛𝗔𝗟 𝗞𝗨𝗗𝗘 𝗪𝗔𝗟𝗜 𝗞𝗘 𝗟𝗔𝗗𝗞𝗘 𝗟𝗘𝗔𝗩𝗘 𝗟𝗘𝗞𝗘 𝗕𝗛𝗔𝗚 🕷️🕷️",
        "{target} 𝗧𝗢𝗛𝗔𝗥 𝗠𝗔𝗜𝗬𝗔 𝗞𝗜 𝗖𝗛𝗨𝗧 😂😂😂😂😂😂",
        "{target} 𝗠𝗘 𝗕𝗢𝗧 𝗛𝗢𝗞𝗘 𝗧𝗘𝗥𝗜 𝗠𝗔𝗔 𝗖𝗛𝗢𝗗 𝗗𝗨𝗚𝗔 𝗧𝗨 𝗗𝗘𝗞𝗛𝗧𝗔 𝗥𝗘𝗛 𝗝𝗔𝗬𝗘𝗚𝗔 🤔🧨❤️‍🔥🎀",
        "{target} 𝗘𝗞 𝗧𝗛𝗔𝗣𝗣𝗔𝗗 𝗠𝗘 𝗧𝗘𝗥𝗜 𝗠𝗔𝗔 𝗖𝗛𝗨𝗗 𝗝𝗔𝗬𝗘𝗚𝗜 😟",
        "{target} 𝗧𝗘𝗥𝗘 𝗠𝗔𝗔 𝗕𝗔𝗔𝗣 𝗔𝗖𝗖𝗗𝗘𝗡𝗧 𝗠𝗘 𝗠𝗔𝗔𝗥 𝗝𝗔𝗬𝗘 🕷️🖤",
        "{target} 𝗦𝗘𝗡𝗣𝗔𝗜 𝗦𝗘 𝗠𝗔𝗙𝗜 𝗠𝗔𝗡𝗚 𝗥𝗔𝗡𝗗𝗜 𝗞𝗘 𝗟𝗔𝗗𝗞𝗘 💜",
        "{target} 𝗕𝗧𝗦 𝗪𝗔𝗟𝗢 𝗦𝗘 𝗧𝗘𝗥𝗜 𝗠𝗔𝗔 𝗖𝗛𝗨𝗗𝗪𝗔𝗗𝗨 🎀",
        "{target} 𝗧𝗘𝗥𝗜 𝗠𝗔𝗔 𝗖𝗛𝗨𝗗𝗜 𝗕𝗔𝗟𝗟𝗘 𝗕𝗔𝗟𝗟𝗘 🐦",
        "{target} 𝗧𝗘𝗥𝗜 𝗠𝗔𝗔 𝗞𝗜 𝗖𝗛𝗨𝗧 🦜𝗖𝗛𝗨𝗧 🦜𝗖𝗛𝗨𝗧 🦜𝗖𝗛𝗨𝗧 🦜𝗖𝗛𝗨𝗧 🦜𝗖𝗛𝗨𝗧 🦜𝗖𝗛𝗨𝗧 🦜𝗖𝗛𝗨𝗧 🦜𝗖𝗛𝗨𝗧 🦜𝗖𝗛𝗨𝗧 🦜𝗖𝗛𝗨𝗧 🦜𝗖𝗛𝗨𝗧 🦜𝗖𝗛𝗨𝗧 🦜",
        "{target} 𝗔𝗖𝗛𝗔 𝗕𝗘𝗧𝗔 𝗞𝗢𝗜 𝗡𝗛𝗜 𝗠𝗔𝗜 𝗧𝗢 𝗧𝗘𝗥𝗜 𝗠𝗔𝗔 𝗖𝗛𝗢𝗗𝗨𝗚𝗔 😂😂🖖",
        "{target} 𝗗𝗘𝗞𝗛 𝗧𝗘𝗥𝗜 𝗕𝗘𝗛𝗘𝗡 𝗖𝗛𝗢𝗗𝗡𝗘 𝗦𝗘𝗡𝗣𝗔𝗜 𝗚𝗢𝗗 𝗔𝗔𝗬𝗔 𝗛𝗔𝗜 😂😂",
        "{target} 𝗧𝗘𝗥𝗜 𝗠𝗔𝗔 𝗞𝗢 𝗛𝗔𝗚𝗧𝗘 𝗧𝗜𝗠𝗘 𝗚𝗔𝗡𝗗 𝗣𝗘 𝗟𝗔𝗔𝗧 𝗠𝗔𝗥𝗨𝗚𝗔 😝😝😝😝😝😝",
        "{target} 𝗧𝗘𝗥𝗜 𝗠𝗔𝗔 𝗞𝗘 𝗔𝗡𝗞𝗛𝗢 𝗠𝗘 𝗠𝗢𝗢𝗧 𝗗𝗨 ? 🤔🤔",
    ],
    2: [
        "📈 <b>{target} Slide 2 of 2</b>",
        "📈 <b>{target} Slide 2 alternate</b>",
    ],
}

# SQLite database file path (created automatically in current directory)
DATABASE_FILE: str = os.getenv("BOT_DATABASE_FILE", "bot_data.db")

# Configure up to 10 Telegram Bot Tokens.
# Tokens are loaded from:
# 1. BOT_TOKENS environment variable (comma-separated list), OR
# 2. Individual BOT_TOKEN_1 ... BOT_TOKEN_10 environment variables, OR
# 3. Direct entries in the list below.
_ENV_BOT_TOKENS = os.getenv("BOT_TOKENS", "").strip()
if _ENV_BOT_TOKENS:
    RAW_CONFIGURED_TOKENS: List[str] = [
        t.strip() for t in _ENV_BOT_TOKENS.split(",") if t.strip()
    ]
else:
    RAW_CONFIGURED_TOKENS: List[str] = [
        "8840812192:AAFA3gd9xhAjDZp9m9R8PUgKgHzrWbwKYjs",
        "8728506504:AAFLqUWEns_uZrSBi8OB5gYpKt9RPSrQ7Qo",
        "8429240583:AAF7qUSw8aHh1SBsUnmPLAJNtsaKAZtrhoA",
        "8916318634:AAE5Xw1JGCi5bxvsKHut1YynohkSgsqv2_g",
        "8992880640:AAGZXcFpiSuaA2pDGviezuwDfkUDFj2_-8k",
        "8790579394:AAFaGo226saL9dOs4fLodoXhlmQU_MnC5ic",
        "8988569895:AAE8dpar3wm2l8MsWCyoTUydMlm3VNErB6Y",
        "8635033129:AAEwZYart2xtpwWLU89r8IJL0QLsSaqpwoo",
        "8913004813:AAGGdgKsLLxHiF9wCQbOGurzXyHSh-wEl1k",
        "8888665092:AAEsN_maMRcKbrtcUCFq69sL5TD17JVBKzI",
    ]

# Filter out empty placeholders and enforce maximum limit of 10
ACTIVE_CONFIGURED_TOKENS: List[str] = [
    tok for tok in RAW_CONFIGURED_TOKENS if tok
][:MAX_BOT_TOKENS]


# ---------------------------------------------------------------------------
# DATABASE & STORAGE LAYER (Single SQLite Architecture)
# ---------------------------------------------------------------------------
class DatabaseManager:
    """
    Self-contained SQLite manager for Sudo users, NC slots,
    4-Message sequences, and 2-Slide contents.
    """

    def __init__(self, db_path: str = DATABASE_FILE) -> None:
        self.db_path = db_path
        self._sudo_cache: Set[int] = set()
        self._init_database()
        self._load_sudo_cache()

    @contextlib.contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_database(self) -> None:
        """Creates required tables and populates default slots if absent."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Sudo users table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS sudo_users (
                    user_id INTEGER PRIMARY KEY,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

            # NC slots table (Enforcing strictly slots 1 through 6)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS nc_slots (
                    slot INTEGER PRIMARY KEY CHECK(slot >= 1 AND slot <= 6),
                    content TEXT DEFAULT '',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS nc_commands (
                    slot INTEGER PRIMARY KEY CHECK(slot >= 1 AND slot <= 6),
                    command TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

            # 4-Message slots table (Slots 1 through 4)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS msg4_slots (
                    slot INTEGER PRIMARY KEY CHECK(slot >= 1 AND slot <= 4),
                    content TEXT DEFAULT '',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

            # 2-Slide slots table (Slides 1 through 2)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS slide2_slots (
                    slot INTEGER PRIMARY KEY CHECK(slot >= 1 AND slot <= 2),
                    content TEXT DEFAULT '',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

            # Seed NC slots (1..6) if empty
            for slot_num in range(1, MAX_NC_SLOTS + 1):
                cursor.execute(
                    "INSERT OR IGNORE INTO nc_slots (slot, content) VALUES (?, '')",
                    (slot_num,),
                )
                cursor.execute(
                    "INSERT OR IGNORE INTO nc_commands (slot, command) VALUES (?, ?)",
                    (slot_num, DEFAULT_NC_COMMANDS[slot_num - 1]),
                )

            # Seed 4-Message default templates if empty
            default_msgs = {
                1: "📨 [1/4] Notice: System operational and active.",
                2: "📋 [2/4] Info: Review instructions and community guidelines.",
                3: "🔗 [3/4] Links: Official updates and pinned materials.",
                4: "📞 [4/4] Support: Contact authorized administrators for queries.",
            }
            for slot_num, default_text in default_msgs.items():
                cursor.execute(
                    "INSERT OR IGNORE INTO msg4_slots (slot, content) VALUES (?, ?)",
                    (slot_num, default_text),
                )

            # Seed 2-Slide default templates if empty
            default_slides = {
                1: (
                    "📊 <b>SLIDE 1 of 2: System Overview</b>\n\n"
                    "• Framework: Asynchronous Multi-Bot Manager\n"
                    "• Multi-Token Architecture: Up to 10 bots supported\n"
                    "• Database: SQLite Persistence Engine Active\n\n"
                    "<i>Use navigation buttons below to view Slide 2.</i>"
                ),
                2: (
                    "📈 <b>SLIDE 2 of 2: Operational Specifications</b>\n\n"
                    "• Permissions: Centralized Owner & Sudo Access\n"
                    "• NC Feature: Exactly 6 dedicated slots\n"
                    "• Messaging: 4-Message sequence & 2-Slide cards\n\n"
                    "<i>Use navigation buttons below to return to Slide 1.</i>"
                ),
            }
            for slide_num, default_text in default_slides.items():
                cursor.execute(
                    "INSERT OR IGNORE INTO slide2_slots (slot, content) VALUES (?, ?)",
                    (slide_num, default_text),
                )

            conn.commit()

    def _load_sudo_cache(self) -> None:
        """Loads sudo user IDs into in-memory set for instantaneous checks."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM sudo_users")
            rows = cursor.fetchall()
            self._sudo_cache = {int(row["user_id"]) for row in rows}

    # --- Sudo Methods ---
    def add_sudo(self, user_id: int) -> bool:
        """Adds a user ID to the sudo list."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR IGNORE INTO sudo_users (user_id) VALUES (?)",
                    (user_id,),
                )
                conn.commit()
            self._sudo_cache.add(user_id)
            return True
        except Exception as e:
            logger.error("Failed to add sudo user %s: %s", user_id, e)
            return False

    def del_sudo(self, user_id: int) -> bool:
        """Removes a user ID from the sudo list."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM sudo_users WHERE user_id = ?",
                    (user_id,),
                )
                conn.commit()
            self._sudo_cache.discard(user_id)
            return True
        except Exception as e:
            logger.error("Failed to delete sudo user %s: %s", user_id, e)
            return False

    def is_sudo(self, user_id: int) -> bool:
        """Checks if a user ID has sudo authorization."""
        return user_id in self._sudo_cache

    def get_sudo_list(self) -> List[Tuple[int, str]]:
        """Returns list of (user_id, added_at) for all sudo users."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_id, added_at FROM sudo_users ORDER BY user_id ASC"
            )
            return [(int(row["user_id"]), str(row["added_at"])) for row in cursor.fetchall()]

    # --- NC Slots Methods (1..6) ---
    def get_nc_slot(self, slot: int) -> Optional[str]:
        if not (1 <= slot <= MAX_NC_SLOTS):
            return None
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT content FROM nc_slots WHERE slot = ?", (slot,))
            row = cursor.fetchone()
            return str(row["content"]) if row else None

    def get_all_nc_slots(self) -> Dict[int, str]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT slot, content FROM nc_slots ORDER BY slot ASC")
            return {int(row["slot"]): str(row["content"]) for row in cursor.fetchall()}

    def set_nc_slot(self, slot: int, content: str) -> bool:
        if not (1 <= slot <= MAX_NC_SLOTS):
            return False
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO nc_slots (slot, content, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(slot) DO UPDATE SET
                    content = excluded.content,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (slot, content),
            )
            conn.commit()
        return True

    def clear_nc_slot(self, slot: int) -> bool:
        if not (1 <= slot <= MAX_NC_SLOTS):
            return False
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE nc_slots SET content = '', updated_at = CURRENT_TIMESTAMP WHERE slot = ?",
                (slot,),
            )
            conn.commit()
        return True

    def get_nc_commands(self) -> Dict[int, str]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT slot, command FROM nc_commands ORDER BY slot ASC")
            return {int(row["slot"]): str(row["command"]) for row in cursor.fetchall()}

    def set_nc_command(self, slot: int, command: str) -> bool:
        if not (1 <= slot <= MAX_NC_SLOTS):
            return False
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO nc_commands (slot, command, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(slot) DO UPDATE SET
                    command = excluded.command,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (slot, command),
            )
            conn.commit()
        return True

    # --- 4-Message Slots Methods (1..4) ---
    def get_msg4_slot(self, slot: int) -> Optional[str]:
        if not (1 <= slot <= MAX_MSG4_SLOTS):
            return None
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT content FROM msg4_slots WHERE slot = ?", (slot,))
            row = cursor.fetchone()
            return str(row["content"]) if row else None

    def get_all_msg4_slots(self) -> Dict[int, str]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT slot, content FROM msg4_slots ORDER BY slot ASC")
            return {int(row["slot"]): str(row["content"]) for row in cursor.fetchall()}

    def set_msg4_slot(self, slot: int, content: str) -> bool:
        if not (1 <= slot <= MAX_MSG4_SLOTS):
            return False
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO msg4_slots (slot, content, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(slot) DO UPDATE SET
                    content = excluded.content,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (slot, content),
            )
            conn.commit()
        return True

    # --- 2-Slide Slots Methods (1..2) ---
    def get_slide2_slot(self, slot: int) -> Optional[str]:
        if not (1 <= slot <= MAX_SLIDE2_SLOTS):
            return None
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT content FROM slide2_slots WHERE slot = ?", (slot,))
            row = cursor.fetchone()
            return str(row["content"]) if row else None

    def get_all_slide2_slots(self) -> Dict[int, str]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT slot, content FROM slide2_slots ORDER BY slot ASC")
            return {int(row["slot"]): str(row["content"]) for row in cursor.fetchall()}

    def set_slide2_slot(self, slot: int, content: str) -> bool:
        if not (1 <= slot <= MAX_SLIDE2_SLOTS):
            return False
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO slide2_slots (slot, content, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(slot) DO UPDATE SET
                    content = excluded.content,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (slot, content),
            )
            conn.commit()
        return True


# Global database instance
db_manager = DatabaseManager()


class FloodWaitHandler:
    def __init__(self, recovery: "FloodRecovery", retry_after: "RetryAfterManager") -> None:
        self.recovery = recovery
        self.retry_after = retry_after

    @staticmethod
    def seconds(error: BaseException) -> float:
        value = getattr(error, "retry_after", 0.0)
        try:
            return max(0.0, float(value))
        except (TypeError, ValueError):
            return 0.0

    async def handle(self, bot_id: int, operation: str, error: BaseException) -> float:
        wait_for = self.seconds(error)
        self.recovery.set(bot_id, operation, wait_for)
        self.retry_after.set(bot_id, operation, wait_for)
        logger.warning(
            "[RETRY] bot=%s operation=%s FloodWait %.2fs",
            bot_id,
            operation,
            wait_for,
        )
        return wait_for


class AdaptiveBackoff:
    def __init__(self, base: float = 0.25, maximum: float = 8.0, jitter: float = 0.2) -> None:
        self.base = base
        self.maximum = maximum
        self.jitter = jitter
        self._attempts: Dict[Tuple[int, str], int] = {}

    def delay(self, key: Tuple[int, str]) -> float:
        attempt = self._attempts.get(key, 0)
        self._attempts[key] = min(attempt + 1, 10)
        raw = min(self.maximum, self.base * (2 ** attempt))
        return min(self.maximum, raw + random.uniform(0.0, raw * self.jitter))

    def reset(self, key: Tuple[int, str]) -> None:
        self._attempts.pop(key, None)


class CooldownManager:
    def __init__(self) -> None:
        self._until: Dict[Tuple[int, str], float] = {}

    def set(self, bot_id: int, operation: str, seconds: float) -> None:
        self._until[(bot_id, operation)] = max(
            self._until.get((bot_id, operation), 0.0),
            time.monotonic() + max(0.0, seconds),
        )

    def remaining(self, bot_id: int, operation: str) -> float:
        key = (bot_id, operation)
        wait_for = max(0.0, self._until.get(key, 0.0) - time.monotonic())
        if not wait_for:
            self._until.pop(key, None)
        return wait_for


class RetryAfterManager(CooldownManager):
    pass


class FloodRecovery(CooldownManager):
    async def wait(self, bot_id: int, operation: str) -> None:
        wait_for = self.remaining(bot_id, operation)
        if wait_for:
            await asyncio.sleep(wait_for)


class InstantRecovery:
    def __init__(self, recovery: FloodRecovery) -> None:
        self.recovery = recovery

    async def wait(self, bot_id: int, operation: str) -> None:
        await self.recovery.wait(bot_id, operation)


class HyperRateLimiter:
    def __init__(self, minimum_interval: float = 0.001) -> None:
        self.minimum_interval = minimum_interval
        self._next_allowed: Dict[Tuple[int, str], float] = {}
        self._locks: Dict[Tuple[int, str], asyncio.Lock] = {}

    async def acquire(self, bot_id: int, operation: str) -> None:
        key = (bot_id, operation)
        lock = self._locks.setdefault(key, asyncio.Lock())
        async with lock:
            now = time.monotonic()
            wait_for = max(0.0, self._next_allowed.get(key, now) - now)
            if wait_for:
                await asyncio.sleep(wait_for)
            self._next_allowed[key] = time.monotonic() + self.minimum_interval

    def clear(self) -> None:
        self._next_allowed.clear()
        self._locks.clear()


class RateLimitManager:
    def __init__(self) -> None:
        self.limiter = HyperRateLimiter()

    async def acquire(self, bot_id: int, operation: str) -> None:
        await self.limiter.acquire(bot_id, operation)

    def clear(self) -> None:
        self.limiter.clear()


class SmartRetry:
    def __init__(
        self,
        flood_wait: FloodWaitHandler,
        recovery: FloodRecovery,
        instant_recovery: "InstantRecovery",
        cooldowns: CooldownManager,
        retry_after: RetryAfterManager,
        rate_limits: "RateLimitManager",
        backoff: AdaptiveBackoff,
        maximum_attempts: int = 4,
    ) -> None:
        self.flood_wait = flood_wait
        self.recovery = recovery
        self.instant_recovery = instant_recovery
        self.cooldowns = cooldowns
        self.retry_after = retry_after
        self.rate_limits = rate_limits
        self.backoff = backoff
        self.maximum_attempts = maximum_attempts

    @staticmethod
    def is_retryable(error: BaseException) -> bool:
        return isinstance(error, (FloodWaitError, NetworkError, asyncio.TimeoutError, TimeoutError))

    async def execute(
        self,
        bot_id: int,
        operation: str,
        operation_factory: Callable[[], Awaitable[Any]],
    ) -> Any:
        key = (bot_id, operation)
        for attempt in range(self.maximum_attempts + 1):
            await self.instant_recovery.wait(bot_id, operation)
            retry_wait = self.retry_after.remaining(bot_id, operation)
            if retry_wait:
                await asyncio.sleep(retry_wait)
            cooldown_wait = self.cooldowns.remaining(bot_id, operation)
            if cooldown_wait:
                await asyncio.sleep(cooldown_wait)
            await self.rate_limits.acquire(bot_id, operation)
            try:
                result = await operation_factory()
                self.backoff.reset(key)
                return result
            except asyncio.CancelledError:
                raise
            except FloodWaitError as error:
                if attempt >= self.maximum_attempts:
                    raise
                await self.flood_wait.handle(bot_id, operation, error)
            except BaseException as error:
                if not self.is_retryable(error) or attempt >= self.maximum_attempts:
                    raise
                wait_for = self.backoff.delay(key)
                self.cooldowns.set(bot_id, operation, wait_for)
                logger.warning(
                    "[RETRY] bot=%s operation=%s attempt=%d delay=%.2fs error=%s",
                    bot_id,
                    operation,
                    attempt + 1,
                    wait_for,
                    type(error).__name__,
                )
        raise RuntimeError("retry loop exited unexpectedly")


@dataclass(order=True)
class _PriorityTask:
    priority: int
    sequence: int
    operation: Callable[[], Awaitable[Any]] = field(compare=False)
    future: asyncio.Future[Any] = field(compare=False)
    operation_name: str = field(compare=False, default="operation")
    dedupe_key: Optional[str] = field(compare=False, default=None)


class FastLoopEngine:
    def __init__(self) -> None:
        self.stop_event = asyncio.Event()

    async def wait_for_stop(self) -> None:
        await self.stop_event.wait()

    def stop(self) -> None:
        self.stop_event.set()


class HyperfireEngine(FastLoopEngine):
    workers_per_bot = 4
    queue_size = 128

    def __init__(self) -> None:
        super().__init__()
        self.recovery = FloodRecovery()
        self.instant_recovery = InstantRecovery(self.recovery)
        self.retry_after = RetryAfterManager()
        self.cooldowns = CooldownManager()
        self.rate_limits = RateLimitManager()
        self.backoff = AdaptiveBackoff()
        self.flood_wait = FloodWaitHandler(self.recovery, self.retry_after)
        self.retry = SmartRetry(
            self.flood_wait,
            self.recovery,
            self.instant_recovery,
            self.cooldowns,
            self.retry_after,
            self.rate_limits,
            self.backoff,
        )
        self.queues: Dict[int, asyncio.PriorityQueue[_PriorityTask]] = {}
        self.worker_tasks: Dict[int, List[asyncio.Task[Any]]] = {}
        self.pending: Dict[Tuple[int, str], asyncio.Future[Any]] = {}
        self._sequence = 0
        self._lock = asyncio.Lock()

    async def ensure_bot(self, bot_id: int) -> None:
        async with self._lock:
            if bot_id in self.worker_tasks:
                return
            queue: asyncio.PriorityQueue[_PriorityTask] = asyncio.PriorityQueue(self.queue_size)
            self.queues[bot_id] = queue
            self.worker_tasks[bot_id] = [
                asyncio.create_task(self._worker_loop(bot_id, worker_index))
                for worker_index in range(self.workers_per_bot)
            ]
            logger.info("[ENGINE] bot=%s workers=%d started", bot_id, self.workers_per_bot)

    async def _worker_loop(self, bot_id: int, worker_index: int) -> None:
        queue = self.queues[bot_id]
        try:
            while True:
                item = await queue.get()
                try:
                    if item.future.cancelled():
                        continue
                    operation_task = asyncio.create_task(
                        self.retry.execute(
                            bot_id,
                            item.operation_name,
                            item.operation,
                        )
                    )

                    def cancel_operation(future: asyncio.Future[Any]) -> None:
                        if future.cancelled() and not operation_task.done():
                            operation_task.cancel()

                    item.future.add_done_callback(cancel_operation)
                    try:
                        result = await operation_task
                    except asyncio.CancelledError:
                        if not item.future.cancelled():
                            raise
                        continue
                    finally:
                        item.future.remove_done_callback(cancel_operation)
                    if not item.future.done():
                        item.future.set_result(result)
                except asyncio.CancelledError:
                    if not item.future.done():
                        item.future.cancel()
                    raise
                except Exception as error:
                    if not item.future.done():
                        item.future.set_exception(error)
                    logger.error(
                        "[ENGINE] bot=%s worker=%d operation=%s failed: %s",
                        bot_id,
                        worker_index,
                        item.operation_name,
                        error,
                    )
                finally:
                    if item.dedupe_key:
                        pending_key = (bot_id, item.dedupe_key)
                        if self.pending.get(pending_key) is item.future:
                            self.pending.pop(pending_key, None)
                    queue.task_done()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("[ENGINE] bot=%s worker=%d stopped unexpectedly", bot_id, worker_index)

    async def submit(
        self,
        bot_id: int,
        operation: Callable[[], Awaitable[Any]],
        operation_name: str,
        priority: int = 10,
        dedupe_key: Optional[str] = None,
    ) -> Any:
        await self.ensure_bot(bot_id)
        pending_key = (bot_id, dedupe_key) if dedupe_key else None
        if pending_key:
            existing = self.pending.get(pending_key)
            if existing and not existing.done():
                return await asyncio.shield(existing)
        loop = asyncio.get_running_loop()
        future: asyncio.Future[Any] = loop.create_future()
        self._sequence += 1
        item = _PriorityTask(
            priority,
            self._sequence,
            operation,
            future,
            operation_name,
            dedupe_key,
        )
        if pending_key:
            self.pending[pending_key] = future
        try:
            await self.queues[bot_id].put(item)
            return await asyncio.shield(future)
        except asyncio.CancelledError:
            future.cancel()
            raise

    async def execute_immediate(
        self,
        bot_id: int,
        operation_name: str,
        operation: Callable[[], Awaitable[Any]],
    ) -> Any:
        return await self.retry.execute(bot_id, operation_name, operation)

    async def stop_bot(self, bot_id: int) -> None:
        tasks = self.worker_tasks.pop(bot_id, [])
        queue = self.queues.pop(bot_id, None)
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        if queue:
            while not queue.empty():
                item = queue.get_nowait()
                if not item.future.done():
                    item.future.cancel()
                queue.task_done()
        for key in [key for key in self.pending if key[0] == bot_id]:
            self.pending.pop(key, None)

    async def shutdown(self) -> None:
        self.stop()
        for bot_id in list(self.worker_tasks):
            await self.stop_bot(bot_id)
        self.rate_limits.clear()
        logger.info("[ENGINE] all workers stopped")


class AttackController:
    def __init__(self, engine: HyperfireEngine) -> None:
        self.engine = engine

    async def submit(
        self,
        bot_id: int,
        operation: Callable[[], Awaitable[Any]],
        operation_name: str,
        priority: int = 10,
        dedupe_key: Optional[str] = None,
    ) -> Any:
        return await self.engine.submit(
            bot_id,
            operation,
            operation_name,
            priority,
            dedupe_key,
        )


_hyperfire_engine = HyperfireEngine()
_attack_controller = AttackController(_hyperfire_engine)


_title_state_lock = asyncio.Lock()
_title_locks: Dict[Tuple[int, int], asyncio.Lock] = {}
_pending_titles: Dict[Tuple[int, int], str] = {}


async def fast_set_chat_title(bot: Any, chat_id: int, title: str) -> None:
    bot_id = int(getattr(bot, "id", 0))
    key = (bot_id, chat_id)
    async with _title_state_lock:
        _pending_titles[key] = title
        title_lock = _title_locks.setdefault(key, asyncio.Lock())
    try:
        async with title_lock:
            while True:
                async with _title_state_lock:
                    current_title = _pending_titles.pop(key, None)
                if current_title is None:
                    break
                await _hyperfire_engine.execute_immediate(
                    bot_id,
                    "chat_title",
                    lambda current_title=current_title: bot.set_chat_title(
                        chat_id=chat_id,
                        title=current_title,
                    ),
                )
    finally:
        async with _title_state_lock:
            if key not in _pending_titles and _title_locks.get(key) is title_lock:
                _title_locks.pop(key, None)


# Category-specific task tracking keeps global stop commands isolated.
_tracked_tasks: Dict[str, Set[asyncio.Task[Any]]] = {
    "nc": set(),
    "spam": set(),
    "slide": set(),
}

TaskKey = Tuple[int, int]
SpamTaskKey = Tuple[int, int, int]

# Rotation state for NC title templates per slot.
_nc_rotation_state: Dict[int, int] = {}
_coolnc_symbol_index = 0
_runnc_emoji_index = 0
_glitchnc_emoji_index = 0
_slide2_emoji_index = 0

# Per-chat/per-bot registries keep each feature's ownership independent.
nc_tasks: Dict[TaskKey, asyncio.Task[Any]] = {}
spam_tasks: Dict[SpamTaskKey, asyncio.Task[Any]] = {}
_spam_task_lock = asyncio.Lock()
slide_tasks: Dict[TaskKey, asyncio.Task[Any]] = {}
slide_stop_events: Dict[int, asyncio.Event] = {}
_nc_task_specs: Dict[TaskKey, Tuple[str, str]] = {}

# Backwards-compatible internal name for callers that used the old registry.
message_tasks = spam_tasks


def _forget_tracked_task(category: str, task: asyncio.Task[Any]) -> None:
    _tracked_tasks[category].discard(task)
    for task_registry in (nc_tasks, message_tasks, slide_tasks):
        for task_key, tracked_task in list(task_registry.items()):
            if tracked_task is task:
                del task_registry[task_key]
                if task_registry is nc_tasks:
                    _nc_task_specs.pop(task_key, None)
                break
    if task.cancelled():
        return
    error = task.exception()
    if error is not None:
        logger.error("Tracked %s task failed: %s", category, error, exc_info=error)


def create_tracked_task(category: str, operation: Awaitable[Any]) -> asyncio.Task[Any]:
    task = asyncio.create_task(operation)
    _tracked_tasks[category].add(task)
    task.add_done_callback(lambda completed: _forget_tracked_task(category, completed))
    task.add_done_callback(
        lambda completed: (
            getattr(operation, "close", lambda: None)()
            if completed.cancelled()
            else None
        )
    )
    return task


async def run_tracked_task(category: str, operation: Awaitable[Any]) -> None:
    task = create_tracked_task(category, operation)
    try:
        await task
    except asyncio.CancelledError:
        logger.info("[NC] tracked task cancelled: category=%s", category)
        raise
    except Exception:
        logger.exception("[NC] tracked task failed: category=%s", category)
        raise


async def stop_tracked_tasks(category: str) -> int:
    tasks = list(_tracked_tasks[category])
    for task in tasks:
        if not task.done():
            logger.info("[NC] cancelling task=%s category=%s", task, category)
            task.cancel()
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
    _tracked_tasks[category].clear()
    return len(tasks)


def _active_bot_instances() -> List["BotInstance"]:
    return [
        instance
        for instance in bot_manager.bot_instances
        if instance.status == "ONLINE" and instance.app and instance.app.bot
    ]


def _bot_id(instance: "BotInstance") -> int:
    if instance.bot_info:
        return instance.bot_info.id
    if instance.app and instance.app.bot:
        return instance.app.bot.id
    return instance.index


async def _run_bot_operation(
    category: str,
    bot_id: int,
    operation_factory: Callable[[], Awaitable[Any]],
) -> None:
    operation: Optional[Awaitable[Any]] = None
    try:
        operation = operation_factory()
        await operation
        if TASK_TEST_MODE:
            logger.info(
                "[%s TEST] bot=%s task=%s completed",
                category.upper(),
                bot_id,
                id(asyncio.current_task()),
            )
    except asyncio.CancelledError:
        close_operation = getattr(operation, "close", None) if operation else None
        if close_operation:
            close_operation()
        raise
    except FloodWaitError as exc:
        logger.warning(
            "[%s] bot=%s rate limited for %.2fs",
            category.upper(),
            bot_id,
            exc.retry_after,
        )
    except TelegramError as exc:
        logger.warning("[%s] bot=%s failed: %s", category.upper(), bot_id, exc)
    except Exception:
        logger.exception("[%s] bot=%s failed", category.upper(), bot_id)


async def _cancel_task(task: Optional[asyncio.Task[Any]]) -> None:
    if task is None:
        return
    if not task.done():
        task.cancel()
    await asyncio.gather(task, return_exceptions=True)


async def _start_bot_task(
    category: str,
    task_registry: Dict[TaskKey, asyncio.Task[Any]],
    instance: "BotInstance",
    chat_id: int,
    operation_factory: Callable[[], Awaitable[Any]],
) -> asyncio.Task[Any]:
    bot_id = _bot_id(instance)
    task_key = (chat_id, bot_id)
    previous = task_registry.get(task_key)
    await _cancel_task(previous)
    task = create_tracked_task(
        category,
        _attack_controller.submit(
            bot_id,
            operation_factory,
            category,
            priority=5 if category == "nc" else 10,
            dedupe_key=f"{category}:{chat_id}",
        ),
    )
    task_registry[task_key] = task
    return task


async def _run_spam_worker(
    bot_id: int,
    task_key: SpamTaskKey,
    target: str,
    operation_factory: Callable[[], Awaitable[Any]],
) -> None:
    logger.info("[SPAM] loop started target=%s bot=%s", target, bot_id)
    try:
        while True:
            await _run_bot_operation("spam", bot_id, operation_factory)
            await asyncio.sleep(NC_INTERVAL)
    except asyncio.CancelledError:
        logger.info("[SPAM] loop cancelled bot=%s", bot_id)
        raise
    finally:
        logger.info("[SPAM] loop stopped bot=%s", bot_id)


async def _start_spam_task(
    instance: "BotInstance",
    chat_id: int,
    slot: int,
    target: str,
    operation_factory: Callable[[], Awaitable[Any]],
) -> asyncio.Task[Any]:
    async with _spam_task_lock:
        task_key = (chat_id, _bot_id(instance), slot)
        await _cancel_task(spam_tasks.get(task_key))
        task = create_tracked_task(
            "spam",
            _attack_controller.submit(
                _bot_id(instance),
                lambda: _run_spam_worker(
                    _bot_id(instance), task_key, target, operation_factory
                ),
                "spam",
                priority=10,
                dedupe_key=f"spam:{chat_id}:{slot}",
            ),
        )
        spam_tasks[task_key] = task
        return task


async def stop_all_test_spam_tasks(chat_id: int) -> int:
    async with _spam_task_lock:
        tracked_items = [
            (task_key, task)
            for task_key, task in spam_tasks.items()
            if task_key[0] == chat_id and not task.done()
        ]
        tasks = [task for _, task in tracked_items]
        logger.info("[SPAM] stop requested")
        logger.info("[SPAM] cancelling %d task(s)", len(tasks))
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        for task_key, task in tracked_items:
            if spam_tasks.get(task_key) is task:
                spam_tasks.pop(task_key, None)
        _tracked_tasks["spam"].difference_update(tasks)
        logger.info("[SPAM] all spam tasks stopped")
        return len(tasks)


async def _stop_bot_tasks(
    category: str,
    task_registry: Dict[TaskKey, asyncio.Task[Any]],
    chat_id: Optional[int] = None,
) -> int:
    owned_keys = [
        key for key in task_registry
        if chat_id is None or key[0] == chat_id
    ]
    tasks = [task_registry[key] for key in owned_keys]
    for task in tasks:
        await _cancel_task(task)
    for key in owned_keys:
        task_registry.pop(key, None)
    _tracked_tasks[category].difference_update(tasks)
    return len(tasks)


# ---------------------------------------------------------------------------
# CENTRALIZED PERMISSION DECORATOR
# ---------------------------------------------------------------------------
def requires_auth(owner_only: bool = False) -> Callable:
    """
    Centralized decorator for verifying command execution authority.
    - If owner_only is True, execution is strictly restricted to OWNER_ID.
    - Otherwise, execution is permitted for OWNER_ID or authorized SUDO users.
    - Any unauthorized attempt triggers the exact response:
      ❌ Command Denied
    """
    def decorator(handler_func: Callable) -> Callable:
        @functools.wraps(handler_func)
        async def wrapper(
            update: Update,
            context: ContextTypes.DEFAULT_TYPE,
            *args,
            **kwargs
        ):
            user = update.effective_user
            if not user:
                return

            user_id = user.id
            is_owner = (user_id == OWNER_ID)
            is_sudo = db_manager.is_sudo(user_id)

            if owner_only:
                if not is_owner:
                    if update.effective_message:
                        await _reply_command_output(update.effective_message, "❌ Command Denied")
                    return
            else:
                if not (is_owner or is_sudo):
                    if update.effective_message:
                        await _reply_command_output(update.effective_message, "❌ Command Denied")
                    return

            return await handler_func(update, context, *args, **kwargs)
        return wrapper
    return decorator


# ---------------------------------------------------------------------------
# BOT INSTANCE DATA MODEL & MANAGER
# ---------------------------------------------------------------------------
@dataclass
class BotInstance:
    """Data representation of a single managed Telegram bot instance."""
    index: int
    token: str
    app: Optional[Application] = None
    bot_info: Optional[telegram.User] = None
    status: str = "INITIALIZING"
    error_reason: Optional[str] = None


class BotManager:
    """
    Manages lifecycle, async initialization, polling, health monitoring,
    and graceful shutdown of up to 10 Telegram Bot instances.
    """

    def __init__(self, tokens: List[str]) -> None:
        self.raw_tokens = tokens
        self.bot_instances: List[BotInstance] = []
        self.start_timestamp: float = time.time()
        self._running: bool = False

        # Populate bot slots (1..10)
        for i in range(MAX_BOT_TOKENS):
            token = tokens[i] if i < len(tokens) else ""
            status = "CONFIGURED" if token else "UNCONFIGURED"
            self.bot_instances.append(
                BotInstance(index=i + 1, token=token, status=status)
            )

    @property
    def online_count(self) -> int:
        return sum(1 for b in self.bot_instances if b.status == "ONLINE")

    def get_uptime_formatted(self) -> str:
        elapsed = int(time.time() - self.start_timestamp)
        days, remainder = divmod(elapsed, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{days}d {hours}h {minutes}m {seconds}s"

    async def initialize_and_start_bot(self, instance: BotInstance) -> None:
        """
        Initializes a single bot instance.
        A failure here is isolated and will not crash other instances.
        """
        if not instance.token:
            instance.status = "UNCONFIGURED"
            return

        try:
            # Build Application
            app = ApplicationBuilder().token(instance.token).build()

            # Register standard command handlers on this instance
            register_all_handlers(app)

            # Initialize client and verify credentials with Telegram API
            await app.initialize()
            bot_info = await app.bot.get_me()
            instance.bot_info = bot_info

            # Start updater polling
            await app.start()
            await app.updater.start_polling(drop_pending_updates=True)

            instance.app = app
            instance.status = "ONLINE"
            instance.error_reason = None
            await _hyperfire_engine.ensure_bot(bot_info.id)
            print(f"[BOT #{instance.index:02d}] ✅ @{bot_info.username} (ID: {bot_info.id}) - ONLINE")

        except InvalidToken:
            instance.status = "FAILED"
            instance.error_reason = "Invalid Token"
            print(f"[BOT #{instance.index:02d}] ❌ Failed: Invalid Token")

        except NetworkError as e:
            instance.status = "FAILED"
            instance.error_reason = f"Network Error: {e}"
            print(f"[BOT #{instance.index:02d}] ⚠️ Failed: Network Connection Error")

        except TelegramError as e:
            instance.status = "FAILED"
            instance.error_reason = f"Telegram API Error: {e}"
            print(f"[BOT #{instance.index:02d}] ❌ Failed: {e}")

        except Exception as e:
            instance.status = "FAILED"
            instance.error_reason = f"Unexpected Exception: {e}"
            print(f"[BOT #{instance.index:02d}] ❌ Error: {e}")

    async def start_all(self) -> None:
        """Starts all configured bot instances concurrently."""
        self._running = True
        self.start_timestamp = time.time()

        print("\n" + "=" * 54)
        print("         TELEGRAM MULTI-BOT MANAGER STARTUP       ")
        print("=" * 54)
        print(f"[*] Owner ID           : {OWNER_ID}")
        print(f"[*] Sudo Users Count   : {len(db_manager._sudo_cache)}")
        print(f"[*] Database Status    : SQLite Ready ({DATABASE_FILE})")
        print(f"[*] NC Slots Limit     : {MAX_NC_SLOTS} slots enforced")
        print(f"[*] Message Features   : 4-Message Sequence & 2-Slide Ready")
        print(f"[*] Max Bot Capacity   : {MAX_BOT_TOKENS} slots")
        print("-" * 54)
        print("[*] Connecting and initializing bot tokens...")

        # Initialize all bots asynchronously
        tasks = [
            self.initialize_and_start_bot(instance)
            for instance in self.bot_instances
            if instance.token
        ]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        print("-" * 54)
        print(
            f"[STATUS] {self.online_count} of {len(ACTIVE_CONFIGURED_TOKENS)} "
            f"configured bots are ONLINE."
        )
        if self.online_count == 0:
            print("[NOTICE] No bots are currently online.")
            print("         Please provide valid Telegram bot tokens in BOT_TOKENS,")
            print("         BOT_TOKEN_1 ... BOT_TOKEN_10, or directly in the script.")
        print("=" * 54 + "\n")
        logger.disabled = True

    async def stop_all(self) -> None:
        """Gracefully halts all polling updaters and shuts down applications."""
        print("\n[SHUTDOWN] Initiating graceful termination for all active bots...")
        self._running = False
        for instance in self.bot_instances:
            if instance.app and instance.status == "ONLINE":
                try:
                    if instance.app.updater and instance.app.updater.running:
                        await instance.app.updater.stop()
                    if instance.app.running:
                        await instance.app.stop()
                    await instance.app.shutdown()
                    await _hyperfire_engine.stop_bot(_bot_id(instance))
                    instance.status = "OFFLINE"
                    print(f"[BOT #{instance.index:02d}] Stopped cleanly.")
                except Exception as e:
                    logger.warning("Error stopping bot #%d: %s", instance.index, e)
            await _hyperfire_engine.shutdown()
        print("[SHUTDOWN] All bot instances stopped. Exiting cleanly.\n")


# Global Bot Manager instance
bot_manager = BotManager(ACTIVE_CONFIGURED_TOKENS)


# ---------------------------------------------------------------------------
# GENERAL COMMAND HANDLERS (/help, /ping, /uptime, /status)
# ---------------------------------------------------------------------------
_MATH_SANS_CHARS = (
    "𝘼𝘽𝘾𝘿𝙀𝙁𝙂𝙃𝙄𝙅𝙆𝙇𝙈𝙉𝙊𝙋𝙌𝙍𝙎𝙏𝙐𝙑𝙒𝙓𝙔𝙕𝙖𝙗𝙘𝙙𝙚𝙛𝙜𝙝𝙞𝙟𝙠𝙡𝙢𝙣𝙤𝙥𝙦𝙧𝙨𝙩𝙪𝙫𝙬𝙭𝙮𝙯0123456789"
)
_MONOSPACE_STYLE = (
    "𝘼𝘽𝘾𝘿𝙀𝙁𝙂𝙃𝙄𝙅𝙆𝙇𝙈𝙉𝙊𝙋𝙌𝙍𝙎𝙏𝙐𝙑𝙒𝙓𝙔𝙕"
    "𝙖𝙗𝙘𝙙𝙚𝙛𝙜𝙝𝙞𝙟𝙠𝙡𝙢𝙣𝙤𝙥𝙦𝙧𝙨𝙩𝙪𝙫𝙬𝙭𝙮𝙯"
    "𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵"
)
_MONOSPACE_TRANSLATION = str.maketrans(_MATH_SANS_CHARS, _MONOSPACE_STYLE)
_ASCII_COMMAND_CHARS = (
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "abcdefghijklmnopqrstuvwxyz"
    "0123456789"
)
_COMMAND_OUTPUT_TRANSLATION = str.maketrans(
    _ASCII_COMMAND_CHARS,
    _MONOSPACE_STYLE,
)
_COMMAND_OUTPUT_TRANSLATION.update(_MONOSPACE_TRANSLATION)


def _style_command_output(text: str) -> str:
    """Apply the bot's monospace style without changing HTML tags."""
    parts = re.split(r"(<[^>]+>)", text)
    return "".join(
        part if part.startswith("<") and part.endswith(">") else part.translate(_COMMAND_OUTPUT_TRANSLATION)
        for part in parts
    )


async def _reply_command_output(
    message: Any,
    text: str,
    parse_mode: Optional[str] = None,
) -> None:
    kwargs = {"parse_mode": parse_mode} if parse_mode else {}
    await message.reply_text(_style_command_output(text), **kwargs)


async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Renders clean, Unicode-based help manual containing ONLY implemented features.
    """
    logger.info("[HELP] help request received")
    if not update.effective_message:
        logger.warning("[HELP] early return: no effective message")
        return

    nc_command_text = ", ".join(
        f"/{command}" for command in db_manager.get_nc_commands().values()
    )
    nc_command_names = [command.lstrip("/") for command in nc_command_text.split(", ")]
    help_text = (
        "꒰━━━━━━━━━━━━━━━⋆⊱༻𖥸༺⊰⋆━━━━━━━━━━━━━━━꒱\n"
        "ᛝ          🕷️ 𝑺𝑬𝑵𝑷𝑨𝑰 𝑩𝑶𝑻 𝑴𝑬𝑵𝑼         ᛝ\n"
        "꒰━━━━━━━━━━━━━━━⋆⊱༻𖥸༺⊰⋆━━━━━━━━━━━━━━━꒱\n\n"
        "╰┈➤ 🕷️ <b>𝑮𝑬𝑵𝑬𝑹𝑨𝑳</b>\n"
        "│\n"
        "╰┈➤ ✦ ♰ 𝙝𝙚𝙡𝙥   • 𝘾𝙤𝙢𝙢𝙖𝙣𝙙𝙨 𝙢𝙚𝙣𝙪\n"
        "╰┈➤ ✦ ♰ 𝙥𝙞𝙣𝙜   • 𝙍𝙚𝙨𝙥𝙤𝙣𝙨𝙚 𝙡𝙖𝙩𝙚𝙣𝙘𝙮\n"
        "╰┈➤ ✦ ♰ 𝙪𝙥𝙩𝙞𝙢𝙚 • 𝘽𝙤𝙩 𝙪𝙥𝙩𝙞𝙢𝙚\n"
        "╰┈➤ ✦ ♰ 𝙨𝙩𝙖𝙩𝙪𝙨 • 𝘽𝙤𝙩 𝙨𝙩𝙖𝙩𝙪𝙨\n"
        "╰┈➤ ✦ ♰ 𝙙𝙚𝙡𝙖𝙮 &lt; 0.005 - 0.01 &gt;  • 𝙎𝙚𝙩 𝙉𝘾 𝙡𝙤𝙤𝙥 𝙙𝙚𝙡𝙖𝙮\n"
        "╰┈➤ ✦ ♰ 𝙨𝙩𝙤𝙥𝙖𝙡𝙡   • 𝙎𝙩𝙤𝙥 𝙖𝙡𝙡 𝙩𝙖𝙨𝙠𝙨\n\n"
        "╰┈➤ 🕷️ <b>𝑺𝑼𝑫𝑶 𝑴𝑨𝑵𝑨𝑮𝑬𝑴𝑬𝑵𝑻</b>\n"
        "│\n"
        "╰┈➤ ✦ ♰ 𝙖𝙙𝙙𝙨𝙪𝙙𝙤  • 𝘼𝙙𝙙 𝙨𝙪𝙙𝙤\n"
        "╰┈➤ ✦ ♰ 𝙙𝙚𝙡𝙨𝙪𝙙𝙤  • 𝙍𝙚𝙢𝙤𝙫𝙚 𝙨𝙪𝙙𝙤\n"
        "╰┈➤ ✦ ♰ 𝙨𝙪𝙙𝙤𝙡𝙞𝙨𝙩  • 𝙎𝙪𝙙𝙤 𝙡𝙞𝙨𝙩\n\n"
        "╰┈➤ 🕷️ <b>𝑵𝑪 𝑺𝒀𝑺𝑻𝑬𝑴</b> 〔𝟔 𝑺𝑳𝑶𝑻𝑺〕\n"
        "│\n"
        f"╰┈➤ ✦ ♰{nc_command_names[0]}\n"
        f"╰┈➤ ✦ ♰{nc_command_names[1]}\n"
        f"╰┈➤ ✦ ♰{nc_command_names[2]}\n"
        f"╰┈➤ ✦ ♰{nc_command_names[3]}\n"
        f"╰┈➤ ✦ ♰{nc_command_names[4]}\n"
        f"╰┈➤ ✦ ♰{nc_command_names[5]}\n"
        "╰┈➤ ✦ ♰stopnc   • Stop all NC tasks\n\n"
        "╰┈➤ 🕷️ <b>𝑴𝑬𝑺𝑺𝑨𝑮𝑬 𝑭𝑬𝑨𝑻𝑼𝑹𝑬𝑺</b>\n"
        "│\n"
        "╰┈➤ ✦ ♰ 𝙨𝙥𝙖𝙢 ~ 1    • \n"
        "╰┈➤ ✦ ♰ 𝙨𝙥𝙖𝙢2    • \n"
        "╰┈➤ ✦ ♰ 𝙨𝙥𝙖𝙢3    • \n"
        "╰┈➤ ✦ ♰ 𝙨𝙥𝙖𝙢4    • \n"
        "╰┈➤ ✦ ♰ 𝙨𝙩𝙤𝙥𝙨𝙥𝙖𝙢 • 𝙎𝙩𝙤𝙥 𝙢𝙚𝙨𝙨𝙖𝙜𝙚 𝙩𝙖𝙨𝙠𝙨\n\n"
        "╰┈➤ 🕷️ <b>𝑺𝑳𝑰𝑫𝑬 𝑭𝑬𝑨𝑻𝑼𝑹𝑬𝑺</b>\n"
        "│\n"
        "╰┈➤ ✦ ♰ 𝐬𝐥𝐢𝐝𝐞 ~ 1   • \n"
        "╰┈➤ ✦ ♰ 𝐬𝐥𝐢𝐝𝐞 ~ 2   • \n"
        "╰┈➤ ✦ ♰ 𝙨𝙩𝙤𝙥𝙨𝒍𝒊𝙙𝙚 • \n\n"
        "╰┈➤ 🕷️ <b>𝑩𝑶𝑻 𝑪𝑶𝑵𝑻𝑹𝑶𝑳</b>\n"
        "│\n"
        "╰┈➤ ✦ ♰ 𝙥𝙧𝙤𝙢𝙤𝙩𝙚𝙗𝙤𝙩 • 𝙋𝙧𝙤𝙢𝙤𝙩𝙚 𝙖𝙡𝙡 𝙗𝙤𝙩𝙨\n"
        "╰┈➤ ✦ ♰ 𝙡𝙚𝙖𝙫𝙚      • 𝙈𝙖𝙠𝙚 𝙖𝙡𝙡 𝙗𝙤𝙩𝙨 𝙡𝙚𝙖𝙫𝙚\n\n"
        "꒰━━━━━━━━━━━━━━━⋆⊱༻𖥸༺⊰⋆━━━━━━━━━━━━━━━꒱╯\n"
        "          🕷️ 𝑺𝒆𝒏𝒑𝒂𝒊 • 𝑪𝒐𝒎𝒎𝒂𝒏𝒅𝒔"
    )
    logger.info("[HELP] sending help menu")
    await _reply_command_output(update.effective_message, help_text, ParseMode.HTML)


_bot_control_command_lock = asyncio.Lock()
_processed_bot_control_commands: Set[Tuple[int, int, str]] = set()


async def _claim_bot_control_command(update: Update, command: str) -> bool:
    chat = update.effective_chat
    message = update.effective_message
    if not chat or not message:
        return False

    command_key = (chat.id, message.message_id, command)
    async with _bot_control_command_lock:
        if command_key in _processed_bot_control_commands:
            return False
        _processed_bot_control_commands.add(command_key)
        if len(_processed_bot_control_commands) > 2048:
            _processed_bot_control_commands.pop()
    return True


@requires_auth(owner_only=False)
async def handle_promotebot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _claim_bot_control_command(update, "promotebot"):
        return
    chat_id = update.effective_chat.id if update.effective_chat else None
    if chat_id is None:
        return

    instances = _active_bot_instances()
    controller: Optional[BotInstance] = None
    for instance in instances:
        bot = instance.app.bot
        bot_id = _bot_id(instance)
        try:
            member = await bot.get_chat_member(chat_id=chat_id, user_id=bot_id)
            is_admin = member.status in {"administrator", "creator"}
            can_promote = member.status == "creator" or bool(
                getattr(member, "can_promote_members", False)
            )
            if is_admin and can_promote:
                controller = instance
                break
        except TelegramError as exc:
            logger.warning(
                "[PROMOTE] bot=%s cannot be controller in chat=%s: %s",
                bot_id,
                chat_id,
                exc,
            )
        except Exception:
            logger.exception(
                "[PROMOTE] failed checking controller bot=%s chat=%s",
                bot_id,
                chat_id,
            )

    if controller is None:
        logger.warning("[PROMOTE] no bot with promote permission found in chat=%s", chat_id)
        if update.effective_message:
            await _reply_command_output(
                update.effective_message,
                "❌ Give full admin permission to one bot first."
            )
        return

    controller_bot = controller.app.bot
    promoted = 0
    for instance in instances:
        if instance is controller:
            continue
        bot = instance.app.bot
        bot_id = _bot_id(instance)
        try:
            await controller_bot.promote_chat_member(
                chat_id=chat_id,
                user_id=bot_id,
                can_change_info=True,
                can_post_messages=True,
                can_edit_messages=True,
                can_delete_messages=True,
                can_invite_users=True,
                can_restrict_members=True,
                can_pin_messages=True,
                can_manage_video_chats=True,
                can_promote_members=False,
            )
            await bot.send_message(
                chat_id=chat_id,
                text=_style_command_output(
                    "𝚒'𝚖 𝚙𝚛𝚘𝚖𝚘𝚝𝚎𝚍 𝚜𝚎𝚗𝚙𝚊𝚒 𝚔𝚎𝚗𝚐\n 𓆩❤︎𓆪"
                ),
            )
            promoted += 1
        except TelegramError as exc:
            logger.warning(
                "[PROMOTE] controller=%s failed promoting bot=%s in chat=%s: %s",
                _bot_id(controller),
                bot_id,
                chat_id,
                exc,
            )
        except Exception:
            logger.exception(
                "[PROMOTE] controller=%s failed promoting bot=%s in chat=%s",
                _bot_id(controller),
                bot_id,
                chat_id,
            )

    logger.info(
        "[PROMOTE] controller=%s promoted=%d chat=%s",
        _bot_id(controller),
        promoted,
        chat_id,
    )


@requires_auth(owner_only=True)
async def handle_leave(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _claim_bot_control_command(update, "leave"):
        return
    chat_id = update.effective_chat.id if update.effective_chat else None
    if chat_id is None:
        return

    left = 0
    for instance in _active_bot_instances():
        bot = instance.app.bot
        bot_id = _bot_id(instance)
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=_style_command_output("𝚂𝚊𝚢𝚘𝚗𝚊𝚛𝚊 𓆩❤︎𓆪"),
            )
            await bot.leave_chat(chat_id=chat_id)
            left += 1
        except TelegramError as exc:
            logger.warning("[LEAVE] bot=%s failed in chat=%s: %s", bot_id, chat_id, exc)
        except Exception:
            logger.exception("[LEAVE] bot=%s failed in chat=%s", bot_id, chat_id)

    logger.info("[LEAVE] bots_left=%d chat=%s", left, chat_id)


async def handle_ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Measures bot-to-Telegram API round-trip latency."""
    if not update.effective_message:
        return
    start_time = time.monotonic()
    sent_msg = await update.effective_message.reply_text(
        _style_command_output("🏓 𝙿𝚒𝚗𝚐𝚒𝚗𝚐...")
    )
    end_time = time.monotonic()
    latency_ms = round((end_time - start_time) * 1000, 2)
    await sent_msg.edit_text(
        _style_command_output(f"🏓 <b>Pong!</b> Latency: <code>{latency_ms} ms</code>"),
        parse_mode=ParseMode.HTML,
    )


async def handle_uptime(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays total elapsed uptime since launch."""
    if not update.effective_message:
        return
    uptime_str = bot_manager.get_uptime_formatted()
    start_dt = datetime.datetime.fromtimestamp(
        bot_manager.start_timestamp, tz=datetime.timezone.utc
    ).strftime("%Y-%m-%d %H:%M:%S UTC")

    text = (
        "⏱️ <b>SYSTEM UPTIME</b>\n"
        f"• Duration: <code>{uptime_str}</code>\n"
        f"• Started At: <code>{start_dt}</code>"
    )
    await _reply_command_output(update.effective_message, text, ParseMode.HTML)


@requires_auth(owner_only=False)
async def handle_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Displays comprehensive status across all 10 bot instances,
    database connectivity, active sudo users, and NC slot allocations.
    """
    if not update.effective_message:
        return

    nc_slots = db_manager.get_all_nc_slots()
    filled_nc = sum(1 for content in nc_slots.values() if content.strip())
    sudo_count = len(db_manager._sudo_cache)

    lines = [
        "🤖 <b>SYSTEM & BOTS STATUS REPORT</b>",
        f"• Total Bot Slots: <code>{MAX_BOT_TOKENS}</code>",
        f"• Active Online Bots: <code>{bot_manager.online_count}/{MAX_BOT_TOKENS}</code>",
        f"• System Uptime: <code>{bot_manager.get_uptime_formatted()}</code>",
        f"• Database Engine: <code>SQLite (Active)</code>",
        f"• Authorized Sudo Users: <code>{sudo_count}</code>",
        f"• NC Slots In Use: <code>{filled_nc}/{MAX_NC_SLOTS}</code>",
        "",
        "📡 <b>MANAGED BOT INSTANCES:</b>",
    ]

    for b in bot_manager.bot_instances:
        prefix = f"├ Bot #{b.index:02d}: " if b.index < MAX_BOT_TOKENS else f"└ Bot #{b.index:02d}: "
        if b.status == "ONLINE" and b.bot_info:
            lines.append(f"{prefix}@{b.bot_info.username} ➔ 🟢 <b>ONLINE</b>")
        elif b.status == "FAILED":
            reason = b.error_reason or "Unknown Error"
            lines.append(f"{prefix}[Slot #{b.index}] ➔ 🔴 <b>FAILED</b> ({html.escape(reason)})")
        elif b.status == "UNCONFIGURED":
            lines.append(f"{prefix}[Slot #{b.index}] ➔ ⚪ <i>Unconfigured</i>")
        else:
            lines.append(f"{prefix}[Slot #{b.index}] ➔ 🟡 <i>{b.status}</i>")

    await _reply_command_output(update.effective_message, "\n".join(lines), ParseMode.HTML)


# ---------------------------------------------------------------------------
# SUDO / ADMIN SYSTEM HANDLERS (/addsudo, /delsudo, /sudolist)
# ---------------------------------------------------------------------------
@requires_auth(owner_only=True)
async def handle_addsudo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Grants sudo privileges to target user ID or replied user (Owner Only)."""
    if not update.effective_message:
        return

    target_id: Optional[int] = None

    # Check if replied to a user message
    if update.effective_message.reply_to_message and update.effective_message.reply_to_message.from_user:
        target_id = update.effective_message.reply_to_message.from_user.id
    elif context.args and len(context.args) > 0:
        try:
            target_id = int(context.args[0])
        except ValueError:
            await _reply_command_output(update.effective_message, "❌ User ID must be a valid numeric integer.")
            return

    if target_id is None:
        await _reply_command_output(
            update.effective_message,
            "ℹ️ <b>Usage:</b>\n"
            "• <code>/addsudo &lt;user_id&gt;</code>\n"
            "• Reply to a user's message with <code>/addsudo</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    if target_id == OWNER_ID:
        await _reply_command_output(update.effective_message, "👑 Specified user is already the permanent Bot Owner.")
        return

    if db_manager.is_sudo(target_id):
        await _reply_command_output(update.effective_message, f"ℹ️ 𝗨𝗦𝗘𝗥 {target_id} 𝗔𝗗𝗗 𝗜𝗡 𝗦𝗨𝗗𝗢 𝗟𝗜𝗦𝗧", ParseMode.HTML)
        return

    success = db_manager.add_sudo(target_id)
    if success:
        await _reply_command_output(update.effective_message, f"✅ 𝗨𝗦𝗘𝗥 {target_id} 𝗛𝗔𝗦 𝗕𝗘𝗘𝗡 𝗚𝗥𝗔𝗡𝗧𝗘𝗗 𝗦𝗨𝗗𝗢 𝗔𝗨𝗧𝗛𝗢𝗥𝗜𝗔𝗧𝗜𝗢𝗡.", ParseMode.HTML)
    else:
        await _reply_command_output(update.effective_message, "❌ Database error while adding sudo user.")


@requires_auth(owner_only=True)
async def handle_delsudo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Revokes sudo privileges from target user ID or replied user (Owner Only)."""
    if not update.effective_message:
        return

    target_id: Optional[int] = None

    if update.effective_message.reply_to_message and update.effective_message.reply_to_message.from_user:
        target_id = update.effective_message.reply_to_message.from_user.id
    elif context.args and len(context.args) > 0:
        try:
            target_id = int(context.args[0])
        except ValueError:
            await _reply_command_output(update.effective_message, "❌ User ID must be a valid numeric integer.")
            return

    if target_id is None:
        await _reply_command_output(
            update.effective_message,
            "ℹ️ <b>Usage:</b>\n"
            "• <code>/delsudo &lt;user_id&gt;</code>\n"
            "• Reply to a user's message with <code>/delsudo</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    if target_id == OWNER_ID:
        await _reply_command_output(update.effective_message, "❌ Cannot revoke permissions from the Bot Owner.")
        return

    if not db_manager.is_sudo(target_id):
        await _reply_command_output(update.effective_message, f"ℹ️ 𝗨𝗦𝗘𝗥 {target_id} 𝗜𝗦 𝗡𝗢𝗧 𝗜𝗡 𝗦𝗨𝗗𝗢 𝗟𝗜𝗦𝗧", ParseMode.HTML)
        return

    success = db_manager.del_sudo(target_id)
    if success:
        await _reply_command_output(update.effective_message, f"✅ 𝗨𝗦𝗘𝗥 {target_id} 𝗛𝗔𝗦 𝗕𝗘𝗘𝗡 𝗥𝗘𝗠𝗢𝗩𝗘𝗗 𝗙𝗥𝗢𝗠 𝗦𝗨𝗗𝗢 𝗟𝗜𝗦𝗧", ParseMode.HTML)
    else:
        await _reply_command_output(update.effective_message, "❌ Database error while removing sudo user.")


@requires_auth(owner_only=False)
async def handle_sudolist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lists the owner and all active authorized sudo users."""
    if not update.effective_message:
        return

    sudo_users = db_manager.get_sudo_list()
    lines = [
        "👑 <b>BOT AUTHORIZATION LIST</b>",
        f"<b>Owner ID:</b> <code>{OWNER_ID}</code> (Full Control)",
        "",
        "⭐ <b>AUTHORIZED SUDO USERS:</b>",
    ]

    if not sudo_users:
        lines.append("• <i>No sudo users currently registered.</i>")
    else:
        for idx, (uid, added_at) in enumerate(sudo_users, 1):
            lines.append(f"{idx}. <code>{uid}</code> (Added: {added_at})")

    lines.append("\n<i>Only Owner can add or delete sudo users.</i>")
    await _reply_command_output(update.effective_message, "\n".join(lines), ParseMode.HTML)


# ---------------------------------------------------------------------------
# NC FEATURE HANDLERS (EXACTLY 6 SLOTS ENFORCED)
# ---------------------------------------------------------------------------
def _command_name(update: Update) -> str:
    message = update.effective_message
    if not message or not message.text:
        return ""
    return message.text.split(maxsplit=1)[0].lstrip("/!").split("@", 1)[0].lower()


async def _send_nc_slot(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    slot: int,
    target: str,
    bot_instance: Optional[BotInstance] = None,
) -> None:
    chat_id = update.effective_chat.id if update.effective_chat else None
    if bot_instance and bot_instance.app and bot_instance.app.bot:
        target_bot = bot_instance.app.bot
    else:
        target_bot = context.bot

    logger.info("[NC] execution entered: slot=%d chat_id=%s bot=%s", slot, chat_id, getattr(bot_instance, 'index', 'default'))
    if not chat_id:
        logger.warning("[NC] stopped: current update has no chat id (slot=%d)", slot)
        return

    target = target.strip()
    templates = list(NC_NAMES.get(slot, []) or NC_GROUPS.get(slot, []))
    if slot in (4, 6):
        saved_content = db_manager.get_nc_slot(slot)
        if saved_content and saved_content.strip():
            templates = [saved_content]
    logger.info("[NC] resolved slot=%d target=%r templates=%d", slot, target, len(templates))
    if not target or not templates:
        logger.warning("[NC] stopped: missing target or NC templates for slot=%d", slot)
        return

    try:
        if update.effective_message:
            logger.info("[NC] START command target=%r slot=%d bot=%s", target, slot, getattr(bot_instance, 'index', 'default'))
            await _hyperfire_engine.execute_immediate(
                _bot_id(bot_instance) if bot_instance else int(getattr(target_bot, "id", 0)),
                "nc_start",
                lambda: target_bot.send_message(
                    chat_id=chat_id,
                    reply_to_message_id=(
                        update.effective_message.message_id
                        if update.effective_message
                        else None
                    ),
                    text=_style_command_output(
                        "🕷️ 𝑵𝑪 𝒍𝒐𝒐𝒑 𝒔𝒕𝒂𝒓𝒕\n"
                        f"🎯 {target}"
                    ),
                ),
            )
        while True:
            index = _nc_rotation_state.get(slot, 0)
            raw_name = templates[index % len(templates)]
            formatted_name = raw_name.replace("{target}", target)
            if slot == 5:
                global _runnc_emoji_index
                runnc_emoji = RUNNC_EMOJIS[_runnc_emoji_index % len(RUNNC_EMOJIS)]
                _runnc_emoji_index += 1
                formatted_name = formatted_name.replace("⁀જ➣", f"⁀જ➣ {runnc_emoji}", 1)
            elif slot == 6:
                global _glitchnc_emoji_index
                glitchnc_emoji = GLITCHNC_EMOJIS[_glitchnc_emoji_index % len(GLITCHNC_EMOJIS)]
                _glitchnc_emoji_index += 1
                formatted_name = formatted_name.replace("➙", f"➙ {glitchnc_emoji}", 1)
            _nc_rotation_state[slot] = (index + 1) % len(templates)

            async def _title_update_once(task_index: int) -> None:
                title = formatted_name
                if slot == 4:
                    global _coolnc_symbol_index
                    if _coolnc_symbol_index >= len(COOLNC_SYMBOLS):
                        _coolnc_symbol_index = 0
                    title = f"{title.rstrip()} {COOLNC_SYMBOLS[_coolnc_symbol_index]}"
                    _coolnc_symbol_index += 1
                logger.info("[NC] title task %d start: slot=%d index=%d title=%r bot=%s", task_index, slot, index, title, getattr(bot_instance, 'index', 'default'))
                while True:
                    try:
                        await fast_set_chat_title(target_bot, chat_id, title)
                        logger.info("[NC] title task %d complete: slot=%d index=%d title=%r bot=%s", task_index, slot, index, title, getattr(bot_instance, 'index', 'default'))
                        break
                    except FloodWaitError as exc:
                        logger.warning("[NC] title task %d FloodWait %.2fs: slot=%d index=%d title=%r bot=%s", task_index, exc.retry_after, slot, index, title, getattr(bot_instance, 'index', 'default'))
                        await asyncio.sleep(exc.retry_after)
                    except Exception:
                        logger.exception("[NC] title task %d failed: slot=%d index=%d title=%r bot=%s", task_index, slot, index, title, getattr(bot_instance, 'index', 'default'))
                        break

            await _title_update_once(0)
            logger.info("[NC] group title batch complete: slot=%d index=%d title=%r bot=%s", slot, index, formatted_name, getattr(bot_instance, 'index', 'default'))

            await asyncio.sleep(NC_INTERVAL)
    except asyncio.CancelledError:
        logger.info("[NC] cancelled: slot=%d chat_id=%s target=%r bot=%s", slot, chat_id, target, getattr(bot_instance, 'index', 'default'))
        raise
    except Exception:
        logger.exception("[NC] unexpected exception: slot=%d chat_id=%s target=%r bot=%s", slot, chat_id, target, getattr(bot_instance, 'index', 'default'))
        raise


async def handle_dynamic_nc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    commands = db_manager.get_nc_commands()
    command = _command_name(update)
    if not command:
        return

    ignored_commands = {
        "help",
        "ping",
        "uptime",
        "status",
        "delay",
        "addsudo",
        "delsudo",
        "sudolist",
        "stopnc",
        "stopspam",
        "stopslide",
        "stopall",
    }
    if command in ignored_commands:
        return

    logger.info("[NC] command received: command=%r configured=%s", command, commands)
    if update.effective_message:
        message_id = update.effective_message.message_id
        processed_key = f"nc_processed_{message_id}"
        if context.chat_data.get(processed_key):
            logger.info("[NC] duplicate callback ignored: command=%r message_id=%s", command, message_id)
            return
        context.chat_data[processed_key] = True

    for slot, configured_command in commands.items():
        if command == configured_command:
            logger.info("[NC] command matched: command=%r slot=%d", command, slot)
            user = update.effective_user
            if not user or (user.id != OWNER_ID and not db_manager.is_sudo(user.id)):
                logger.warning("[NC] permission denied: command=%r user=%s", command, user.id if user else None)
                if update.effective_message:
                    await _reply_command_output(update.effective_message, "❌ Command Denied")
                return
            logger.info("[NC] permission granted: command=%r user=%s", command, user.id)
            target = " ".join(context.args or []).strip()
            if not target and update.effective_message:
                message_parts = (update.effective_message.text or "").split(maxsplit=1)
                target = message_parts[1].strip() if len(message_parts) == 2 else ""

            online_bots = [
                bot
                for bot in bot_manager.bot_instances
                if bot.status == "ONLINE" and bot.app and bot.app.bot
            ]
            if not online_bots:
                logger.warning("[NC] no online bot instances available for slot=%d target=%r", slot, target)
                return

            for bot in online_bots:
                task_key = (update.effective_chat.id, _bot_id(bot)) if update.effective_chat else None
                previous = nc_tasks.get(task_key) if task_key else None
                task_spec = (command, target)
                if (
                    previous
                    and not previous.done()
                    and task_key
                    and _nc_task_specs.get(task_key) == task_spec
                ):
                    logger.info(
                        "[NC] existing session kept: chat=%s bot=%s command=%s",
                        task_key[0],
                        task_key[1],
                        command,
                    )
                    continue
                if previous and not previous.done():
                    logger.info("[NC] cancelling previous task for chat=%s bot #%02d before restart", update.effective_chat.id, bot.index)
                    await _cancel_task(previous)
                logger.info("[NC] BOT #%02d started slot=%d target=%r", bot.index, slot, target)
                task = create_tracked_task(
                    "nc",
                    _attack_controller.submit(
                        _bot_id(bot),
                        lambda bot=bot: _send_nc_slot(
                            update, context, slot, target, bot_instance=bot
                        ),
                        "nc",
                        priority=5,
                        dedupe_key=f"nc:{update.effective_chat.id if update.effective_chat else 0}",
                    ),
                )
                if task_key:
                    nc_tasks[task_key] = task
                    _nc_task_specs[task_key] = task_spec

            logger.info("[NC] started %d bot tasks for command=%s slot=%d target=%r", len(online_bots), command, slot, target)
            await _reply_command_output(
                update.effective_message,
                "🕷️ 𝗡𝗖 𝗟𝗢𝗢𝗣 𝗦𝗧𝗔𝗥𝗧𝗘𝗗 𝗦𝗜𝗥 🎀🕷️🖤",
            )
            return
    logger.warning("[NC] no configured command matched: command=%r", command)


@requires_auth(owner_only=False)
async def handle_stopnc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("[NC] STOP requested")
    stopped = await _stop_bot_tasks(
        "nc",
        nc_tasks,
        update.effective_chat.id if update.effective_chat else None,
    )
    _nc_rotation_state.clear()
    await _reply_command_output(update.effective_message, f" {stopped} 𝗡𝗖 𝗜𝗦 𝗦𝗧𝗢𝗣𝗘𝗗 𝗦𝗜𝗥 🎀🕷️🖤")
    logger.info("[NC] STOP complete: stopped=%d", stopped)


@requires_auth(owner_only=False)
async def handle_delay(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_message:
        return

    args = context.args or []
    if len(args) != 1:
        await _reply_command_output(update.effective_message, "❌ Usage: /delay <seconds> (0.001 to 0.01)")
        return

    try:
        new_interval = float(args[0])
    except ValueError:
        await _reply_command_output(update.effective_message, "❌ Invalid delay value. Use 0.001 to 0.01")
        return

    if not 0.001 <= new_interval <= 0.01:
        await _reply_command_output(update.effective_message, "❌ Delay must be between 0.001 and 0.01")
        return

    global NC_INTERVAL
    NC_INTERVAL = new_interval
    await _reply_command_output(update.effective_message, f"🕷️ Shared task delay set to {str(new_interval)}s")


@requires_auth(owner_only=False)
async def handle_nc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Overview or retrieval of the 6 NC slots.
    - /nc             -> Overview table of all 6 slots
    - /nc <1-6>       -> Retrieve full content of specified slot
    - /nc set <1-6> <text> -> Update slot content
    - /nc del <1-6>        -> Clear slot content
    """
    if not update.effective_message:
        return

    args = context.args or []

    # Case 1: Subcommand set: /nc set <1-6> <content>
    if len(args) >= 3 and args[0].lower() == "set":
        try:
            slot_num = int(args[1])
        except ValueError:
            await _reply_command_output(update.effective_message, "❌ Slot must be an integer between 1 and 6.")
            return

        if not (1 <= slot_num <= MAX_NC_SLOTS):
            await _reply_command_output(update.effective_message, f"❌ Invalid NC slot! Only slots 1 to {MAX_NC_SLOTS} are available.")
            return

        content = " ".join(args[2:]).strip()
        db_manager.set_nc_slot(slot_num, content)
        await _reply_command_output(update.effective_message, f"✅ NC Slot #{slot_num} updated successfully.")
        return

    # Case 2: Subcommand del: /nc del <1-6>
    if len(args) >= 2 and args[0].lower() in ("del", "clear"):
        try:
            slot_num = int(args[1])
        except ValueError:
            await _reply_command_output(update.effective_message, "❌ Slot must be an integer between 1 and 6.")
            return

        if not (1 <= slot_num <= MAX_NC_SLOTS):
            await _reply_command_output(update.effective_message, f"❌ Invalid NC slot! Only slots 1 to {MAX_NC_SLOTS} are available.")
            return

        db_manager.clear_nc_slot(slot_num)
        await _reply_command_output(update.effective_message, f"🗑️ NC Slot #{slot_num} has been cleared.")
        return

    # Case 3: View specific slot: /nc <1-6>
    if len(args) == 1 and args[0].isdigit():
        slot_num = int(args[0])
        if not (1 <= slot_num <= MAX_NC_SLOTS):
            await _reply_command_output(update.effective_message, f"❌ Invalid NC slot! Only slots 1 to {MAX_NC_SLOTS} exist.")
            return

        content = db_manager.get_nc_slot(slot_num)
        if not content:
            await _reply_command_output(
                update.effective_message,
                f"📦 <b>NC Slot #{slot_num}</b> is currently <i>Empty</i>.\n"
                f"Use <code>/setnc {slot_num} &lt;text&gt;</code> to populate it.",
                parse_mode=ParseMode.HTML,
            )
        else:
            await _reply_command_output(
                update.effective_message,
                f"📦 <b>NC Slot #{slot_num} Content:</b>\n\n{html.escape(content)}",
                parse_mode=ParseMode.HTML,
            )
        return

    # Case 4: No args -> Overview of all 6 slots
    slots = db_manager.get_all_nc_slots()
    commands = db_manager.get_nc_commands()
    lines = [
        "📋 <b>NC SLOTS OVERVIEW (Slots 1 to 6)</b>",
        "Enforcing strictly 6 operational slots.\n",
    ]

    for slot_num in range(1, MAX_NC_SLOTS + 1):
        content = slots.get(slot_num, "")
        command_name = commands.get(slot_num, f"nc{slot_num}")
        if content.strip():
            preview = (content[:35] + "...") if len(content) > 35 else content
            lines.append(
                f"• <b>Slot {slot_num} (/{command_name}):</b> 🟢 Set ➔ "
                f"<code>{html.escape(preview)}</code>"
            )
        else:
            lines.append(f"• <b>Slot {slot_num} (/{command_name}):</b> ⚪ <i>Empty</i>")

    lines.append("\n<b>Commands:</b>")
    lines.append("• <code>/nc &lt;1-6&gt;</code> — View full slot content")
    lines.append("• <code>/setnc &lt;1-6&gt; &lt;text&gt;</code> — Set slot content")
    lines.append("• <code>/delnc &lt;1-6&gt;</code> — Clear slot content")

    await _reply_command_output(update.effective_message, "\n".join(lines), ParseMode.HTML)


@requires_auth(owner_only=False)
async def handle_setnc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sets content for a specific NC slot (1 through 6)."""
    if not update.effective_message:
        return

    args = context.args or []
    if len(args) < 2:
        await _reply_command_output(
            update.effective_message,
            "ℹ️ <b>Usage:</b> <code>/setnc &lt;slot 1-6&gt; &lt;content text&gt;</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    try:
        slot_num = int(args[0])
    except ValueError:
        await _reply_command_output(update.effective_message, "❌ Slot parameter must be a numeric integer between 1 and 6.")
        return

    if not (1 <= slot_num <= MAX_NC_SLOTS):
        await _reply_command_output(
            update.effective_message,
            f"❌ Invalid NC slot! Only slots 1 to {MAX_NC_SLOTS} are supported."
        )
        return

    content = " ".join(args[1:]).strip()
    db_manager.set_nc_slot(slot_num, content)
    await _reply_command_output(
        update.effective_message,
        f"✅ <b>NC Slot #{slot_num}</b> successfully updated.",
        parse_mode=ParseMode.HTML,
    )


@requires_auth(owner_only=False)
async def handle_delnc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clears content for a specific NC slot (1 through 6)."""
    if not update.effective_message:
        return

    args = context.args or []
    if len(args) < 1:
        await _reply_command_output(
            update.effective_message,
            "ℹ️ <b>Usage:</b> <code>/delnc &lt;slot 1-6&gt;</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    try:
        slot_num = int(args[0])
    except ValueError:
        await _reply_command_output(update.effective_message, "❌ Slot parameter must be a numeric integer between 1 and 6.")
        return

    if not (1 <= slot_num <= MAX_NC_SLOTS):
        await _reply_command_output(
            update.effective_message,
            f"❌ Invalid NC slot! Only slots 1 to {MAX_NC_SLOTS} exist."
        )
        return

    db_manager.clear_nc_slot(slot_num)
    await _reply_command_output(
        update.effective_message,
        f"🗑️ <b>NC Slot #{slot_num}</b> has been cleared.",
        parse_mode=ParseMode.HTML,
    )


# ---------------------------------------------------------------------------
# MESSAGE FEATURES: 4-MESSAGE FEATURE (/msg4, /setmsg4)
# ---------------------------------------------------------------------------
def _template_target(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    args = context.args or []
    if args:
        return " ".join(args)
    message = update.effective_message
    if message and message.text:
        command_parts = message.text.split(maxsplit=1)
        if len(command_parts) == 2:
            return command_parts[1].strip()
    chat = update.effective_chat
    return str(chat.id) if chat else ""


def _render_templates(
    templates: List[MessageEntry],
    target: str,
    fallback: str,
) -> str:
    rendered = [
        text.replace("{target}", target)
        for text, _ in (parse_message_entry(entry) for entry in templates)
        if text
    ]
    return "\n".join(rendered) if rendered else fallback


async def _send_test_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    slot: int,
    bot_instance: Optional[BotInstance] = None,
) -> None:
    fallback = db_manager.get_msg4_slot(slot) or f"🧪 Test message slot {slot}"
    target = _template_target(update, context)
    rendered_items = [
        text.replace("{target}", target) * repeat_count
        for text, repeat_count in (
            parse_message_entry(entry) for entry in MESSAGE_GROUPS.get(slot, [])
        )
        if text
    ] or [fallback]
    chat_id = update.effective_chat.id if update.effective_chat else None
    if chat_id:
        bot = bot_instance.app.bot if bot_instance and bot_instance.app else context.bot
        bot_id = _bot_id(bot_instance) if bot_instance else "active"
        for content in rendered_items:
            message_length = len(content)
            logger.info("[SPAM] bot=%s message_length=%d", bot_id, message_length)
            if message_length > 4096:
                logger.warning("[SPAM] message skipped: length=%d", message_length)
                continue

            while True:
                try:
                    await _hyperfire_engine.execute_immediate(
                        bot_id if isinstance(bot_id, int) else int(getattr(bot, "id", 0)),
                        "spam_message",
                        lambda content=content: bot.send_message(
                            chat_id=chat_id,
                            text=_style_command_output(content),
                        ),
                    )
                    break
                except FloodWaitError as exc:
                    logger.warning(
                        "[SPAM] bot=%s rate limited for %.2fs; retrying",
                        bot_id,
                        exc.retry_after,
                    )
                    await asyncio.sleep(exc.retry_after)
                except asyncio.CancelledError:
                    raise
                except Exception:
                    logger.exception("[SPAM] bot=%s failed test message", bot_id)
                    break


async def _mock_spam_operation() -> None:
    await asyncio.sleep(0)


@requires_auth(owner_only=False)
async def handle_spam_slot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    command = _command_name(update)
    slot = int(command[-1]) if command in {"spam1", "spam2", "spam3", "spam4"} else 0
    chat_id = update.effective_chat.id if update.effective_chat else None
    if slot and chat_id is not None:
        target = _template_target(update, context)
        instances = _active_bot_instances()
        logger.info("[SPAM] connected bots=%d", len(instances))
        for instance in instances:
            bot_id = _bot_id(instance)
            logger.info("[SPAM] starting bot=%s", bot_id)
            operation_factory = (
                (lambda: _mock_spam_operation())
                if TASK_TEST_MODE
                else (
                    lambda instance=instance: _send_test_message(
                        update, context, slot, bot_instance=instance
                    )
                )
            )
            try:
                await _start_spam_task(
                    instance, chat_id, slot, target, operation_factory
                )
            except Exception:
                logger.exception("[SPAM] bot=%s failed to start test task", bot_id)
        if instances and update.effective_message:
            await _reply_command_output(
                update.effective_message,
                f"🕷️ 𝗦𝗣𝗔𝗠 𝗟𝗢𝗢𝗣 𝗦𝗧𝗔𝗥𝗧𝗘𝗗 𝗦𝗜𝗥 🎀🕷️🖤\nTarget: {target}"
            )


@requires_auth(owner_only=False)
async def handle_stopspam(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id if update.effective_chat else None
    stopped = await stop_all_test_spam_tasks(chat_id) if chat_id is not None else 0
    await _reply_command_output(
        update.effective_message,
        "✅ Spam stopped."
        if stopped
        else "ℹ️ No spam is running."
    )


@requires_auth(owner_only=False)
async def handle_stopall(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id if update.effective_chat else None
    if chat_id is None:
        return

    stopped_nc = await _stop_bot_tasks("nc", nc_tasks, chat_id)
    stopped_spam = await stop_all_test_spam_tasks(chat_id)
    stopped_slide = await _stop_bot_tasks("slide", slide_tasks, chat_id)
    _nc_rotation_state.clear()
    total_stopped = stopped_nc + stopped_spam + stopped_slide

    await _reply_command_output(
        update.effective_message,
        f"✅ Stopped all tasks.\n"
        f"NC: {stopped_nc} | Spam: {stopped_spam} | Slide: {stopped_slide}\n"
        f"Total: {total_stopped}"
    )


@requires_auth(owner_only=False)
async def handle_msg4(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Executes or views the 4-message sequence feature.
    - /msg4          -> Dispatches all 4 configured messages sequentially.
    - /msg4 view     -> Previews all 4 message slots without sending separately.
    - /msg4 set <1-4> <text> -> Updates slot 1..4.
    """
    if not update.effective_message:
        return

    args = context.args or []

    # Subcommand: set via /msg4 set <1-4> <text>
    if len(args) >= 3 and args[0].lower() == "set":
        try:
            slot_num = int(args[1])
        except ValueError:
            await _reply_command_output(update.effective_message, "❌ Slot must be an integer between 1 and 4.")
            return

        if not (1 <= slot_num <= MAX_MSG4_SLOTS):
            await _reply_command_output(update.effective_message, f"❌ Invalid slot! Only message slots 1 to {MAX_MSG4_SLOTS} exist.")
            return

        content = " ".join(args[2:]).strip()
        db_manager.set_msg4_slot(slot_num, content)
        await _reply_command_output(update.effective_message, f"✅ Message Slot #{slot_num} (of 4) updated.")
        return

    # Subcommand: view preview
    if len(args) >= 1 and args[0].lower() == "view":
        slots = db_manager.get_all_msg4_slots()
        lines = ["📨 <b>4-MESSAGE SEQUENCE PREVIEW:</b>\n"]
        for i in range(1, MAX_MSG4_SLOTS + 1):
            text = slots.get(i, "(Empty)")
            lines.append(f"<b>Part {i}/4:</b>\n{html.escape(text)}\n")
        lines.append("<i>Use /msg4 to dispatch this sequence.</i>")
        await _reply_command_output(update.effective_message, "\n".join(lines), ParseMode.HTML)
        return

    # Default action: Send the 4 messages in sequence
    slots = db_manager.get_all_msg4_slots()
    chat_id = update.effective_chat.id if update.effective_chat else None
    if not chat_id:
        return

    async def send_sequence() -> None:
        for i in range(1, MAX_MSG4_SLOTS + 1):
            content = slots.get(i, f"📨 [Part {i}/{MAX_MSG4_SLOTS}]")
            if not content.strip():
                content = f"📨 [Part {i}/{MAX_MSG4_SLOTS}] (Empty placeholder)"
            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=_style_command_output(content),
                )
                await asyncio.sleep(NC_INTERVAL)
            except TelegramError as e:
                logger.warning("Failed to dispatch part %d of 4-message: %s", i, e)

    task_key = (chat_id, getattr(context.bot, "id", 0))
    await _cancel_task(spam_tasks.get(task_key))
    spam_tasks[task_key] = create_tracked_task(
        "spam",
        _attack_controller.submit(
            task_key[1],
            lambda: send_sequence(),
            "msg4",
            priority=10,
            dedupe_key=f"msg4:{chat_id}",
        ),
    )
    await _reply_command_output(
        update.effective_message,
        "📨 𝟰-𝗠𝗘𝗦𝗦𝗔𝗚𝗘 𝗟𝗢𝗢𝗣 𝗦𝗧𝗔𝗥𝗧𝗘𝗗 𝗦𝗜𝗥 🎀🕷️🖤",
    )


@requires_auth(owner_only=False)
async def handle_setmsg4(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sets content for one of the 4 message slots (1 through 4)."""
    if not update.effective_message:
        return

    args = context.args or []
    if len(args) < 2:
        await _reply_command_output(
            update.effective_message,
            "ℹ️ <b>Usage:</b> <code>/setmsg4 &lt;slot 1-4&gt; &lt;text&gt;</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    try:
        slot_num = int(args[0])
    except ValueError:
        await _reply_command_output(update.effective_message, "❌ Slot must be a numeric integer between 1 and 4.")
        return

    if not (1 <= slot_num <= MAX_MSG4_SLOTS):
        await _reply_command_output(
            update.effective_message,
            f"❌ Invalid slot! Only slots 1 to {MAX_MSG4_SLOTS} are supported for 4-message feature."
        )
        return

    content = " ".join(args[1:]).strip()
    db_manager.set_msg4_slot(slot_num, content)
    await _reply_command_output(
        update.effective_message,
        f"✅ <b>Message Slot #{slot_num} (of 4)</b> updated successfully.",
        parse_mode=ParseMode.HTML,
    )


# ---------------------------------------------------------------------------
# MESSAGE FEATURES: 2-SLIDE FEATURE (/slide2, /setslide, callbacks)
# ---------------------------------------------------------------------------
async def _send_slide_slot(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    slide_num: int,
    interactive: bool = False,
    bot_instance: Optional[BotInstance] = None,
    target_override: Optional[str] = None,
) -> None:
    if not update.effective_message:
        return

    chat_id = update.effective_chat.id if update.effective_chat else None
    stop_event = slide_stop_events.get(chat_id) if chat_id is not None else None
    while stop_event is None or not stop_event.is_set():
        target = target_override if target_override is not None else _template_target(update, context)
        if update.effective_chat and target == str(update.effective_chat.id):
            target = ""
        fallback = db_manager.get_slide2_slot(slide_num) or f"📊 <b>Slide {slide_num} of 2</b>"
        templates = SLIDER_MESSAGES.get(slide_num, [])
        if slide_num == 2 and target_override is not None:
            global _slide2_emoji_index
            slide2_emoji = SLIDE2_REPLY_EMOJIS[
                _slide2_emoji_index % len(SLIDE2_REPLY_EMOJIS)
            ]
            _slide2_emoji_index += 1
            items = [f"{html.escape(target_override)} {slide2_emoji}"]
        elif templates:
            items = [
                text.replace("{target}", target)
                for text in templates
                if text and text.strip()
            ]
        else:
            items = [fallback.replace("{target}", target)] if fallback.strip() else []

        if not items:
            return

        keyboard = _build_slide_keyboard(slide_num) if interactive else None
        reply_to_message_id = (
            update.effective_message.reply_to_message.message_id
            if update.effective_message.reply_to_message
            else None
        )
        bot = bot_instance.app.bot if bot_instance and bot_instance.app else context.bot

        for content in items:
            while True:
                try:
                    await _hyperfire_engine.execute_immediate(
                        _bot_id(bot_instance) if bot_instance else int(getattr(bot, "id", 0)),
                        "slide_message",
                        lambda content=content: bot.send_message(
                            chat_id=update.effective_chat.id,
                            text=_style_command_output(content),
                            reply_to_message_id=reply_to_message_id,
                            reply_markup=keyboard,
                            parse_mode=ParseMode.HTML,
                        ),
                    )
                    break
                except FloodWaitError as exc:
                    logger.warning(
                        "[SLIDE] bot=%s rate limited for %.2fs; retrying",
                        _bot_id(bot_instance) if bot_instance else "active",
                        exc.retry_after,
                    )
                    await asyncio.sleep(exc.retry_after)
            await asyncio.sleep(NC_INTERVAL)

        await asyncio.sleep(NC_INTERVAL)


@requires_auth(owner_only=False)
async def handle_slide1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id if update.effective_chat else None
    if chat_id is None:
        return
    slide_stop_events.setdefault(chat_id, asyncio.Event()).clear()
    for instance in _active_bot_instances():
        await _start_bot_task(
            "slide",
            slide_tasks,
            instance,
            chat_id,
            lambda instance=instance: _send_slide_slot(
                update, context, 1, bot_instance=instance
            ),
        )
    await _reply_command_output(
        update.effective_message,
        "📊 𝗦𝗟𝗜𝗗𝗘𝟭 𝗟𝗢𝗢𝗣 𝗦𝗧𝗔𝗥𝗧𝗘𝗗 𝗦𝗜𝗥 🎀🕷️🖤",
    )


@requires_auth(owner_only=False)
async def handle_stopslide(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id if update.effective_chat else None
    if chat_id is not None:
        slide_stop_events.setdefault(chat_id, asyncio.Event()).set()
    stopped = await _stop_bot_tasks(
        "slide",
        slide_tasks,
        chat_id,
    )
    await _reply_command_output(
        update.effective_message,
        f"✅ 𝗦𝗟𝗜𝗗𝗘 𝗜𝗦 𝗦𝗧𝗢𝗣𝗣𝗘𝗗 𝗦𝗜𝗥 🎀🕷️🖤\nStopped: {stopped}",
    )


def _build_slide_keyboard(active_slide: int) -> InlineKeyboardMarkup:
    """Constructs navigation inline buttons for the 2-slide interactive card."""
    if active_slide == 1:
        buttons = [
            [
                InlineKeyboardButton("🟢 Slide 1 (Active)", callback_data="slide:1"),
                InlineKeyboardButton("Slide 2 ➡️", callback_data="slide:2"),
            ]
        ]
    else:
        buttons = [
            [
                InlineKeyboardButton("⬅️ Slide 1", callback_data="slide:1"),
                InlineKeyboardButton("🟢 Slide 2 (Active)", callback_data="slide:2"),
            ]
        ]
    return InlineKeyboardMarkup(buttons)


@requires_auth(owner_only=False)
async def handle_slide2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Renders or configures the interactive 2-slide card.
    - /slide2          -> Sends Slide 1 with navigation buttons.
    - /slide2 view     -> Previews both slides.
    - /slide2 set <1-2> <text> -> Updates slide 1 or 2.
    """
    if not update.effective_message:
        return

    args = context.args or []

    # Subcommand: set via /slide2 set <1-2> <text>
    if len(args) >= 3 and args[0].lower() == "set":
        try:
            slide_num = int(args[1])
        except ValueError:
            await _reply_command_output(update.effective_message, "❌ Slide number must be 1 or 2.")
            return

        if not (1 <= slide_num <= MAX_SLIDE2_SLOTS):
            await _reply_command_output(update.effective_message, f"❌ Invalid slide! Only slides 1 and {MAX_SLIDE2_SLOTS} exist.")
            return

        content = " ".join(args[2:]).strip()
        db_manager.set_slide2_slot(slide_num, content)
        await _reply_command_output(update.effective_message, f"✅ Slide #{slide_num} updated.")
        return

    # Subcommand: view preview
    if len(args) >= 1 and args[0].lower() == "view":
        slides = db_manager.get_all_slide2_slots()
        lines = ["📊 <b>2-SLIDE FEATURE PREVIEW:</b>\n"]
        for i in range(1, MAX_SLIDE2_SLOTS + 1):
            text = slides.get(i, "(Empty)")
            lines.append(f"<b>--- Slide {i}/2 ---</b>\n{text}\n")
        lines.append("<i>Use /slide2 to send the interactive card.</i>")
        await _reply_command_output(update.effective_message, "\n".join(lines), ParseMode.HTML)
        return

    # Default action: Send interactive Slide 1
    chat_id = update.effective_chat.id if update.effective_chat else None
    if chat_id is None:
        return
    slide_stop_events.setdefault(chat_id, asyncio.Event()).clear()
    command_text = " ".join(args).strip()
    target_override = command_text or None
    for instance in _active_bot_instances():
        await _start_bot_task(
            "slide",
            slide_tasks,
            instance,
            chat_id,
            lambda instance=instance: _send_slide_slot(
                update,
                context,
                2 if target_override else 1,
                interactive=False,
                bot_instance=instance,
                target_override=target_override,
            ),
        )
    await _reply_command_output(
        update.effective_message,
        "📊 𝗦𝗟𝗜𝗗𝗘𝟮 𝗟𝗢𝗢𝗣 𝗦𝗧𝗔𝗥𝗧𝗘𝗗 𝗦𝗜𝗥 🎀🕷️🖤",
    )


@requires_auth(owner_only=False)
async def handle_setslide(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sets content for Slide 1 or Slide 2."""
    if not update.effective_message:
        return

    args = context.args or []
    if len(args) < 2:
        await _reply_command_output(
            update.effective_message,
            "ℹ️ <b>Usage:</b> <code>/setslide &lt;1 or 2&gt; &lt;content text&gt;</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    try:
        slide_num = int(args[0])
    except ValueError:
        await _reply_command_output(update.effective_message, "❌ Slide number must be 1 or 2.")
        return

    if not (1 <= slide_num <= MAX_SLIDE2_SLOTS):
        await _reply_command_output(
            update.effective_message,
            f"❌ Invalid slide! Only slides 1 and {MAX_SLIDE2_SLOTS} are supported."
        )
        return

    content = " ".join(args[1:]).strip()
    db_manager.set_slide2_slot(slide_num, content)
    await _reply_command_output(
        update.effective_message,
        f"✅ <b>Slide #{slide_num} (of 2)</b> updated successfully.",
        parse_mode=ParseMode.HTML,
    )


async def handle_slide_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles inline button clicks to switch between Slide 1 and Slide 2."""
    query = update.callback_query
    if not query or not query.data:
        return

    await query.answer()

    data_parts = query.data.split(":")
    if len(data_parts) != 2 or data_parts[0] != "slide":
        return

    try:
        slide_target = int(data_parts[1])
    except ValueError:
        return

    if not (1 <= slide_target <= MAX_SLIDE2_SLOTS):
        return

    target = str(query.from_user.id) if query.from_user else ""
    if query.message and target == str(query.message.chat_id):
        target = ""
    fallback = db_manager.get_slide2_slot(slide_target) or f"📊 <b>Slide {slide_target} of 2</b>"
    templates = SLIDER_MESSAGES.get(slide_target, [])
    if templates:
        content = _render_templates(templates, target, fallback)
    else:
        content = fallback.replace("{target}", target)
    content = _style_command_output(content)
    keyboard = _build_slide_keyboard(active_slide=slide_target)

    try:
        await query.edit_message_text(
            text=content,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
        )
    except BadRequest as e:
        # Ignore Telegram's "Message is not modified" error when clicking current active slide
        if "Message is not modified" not in str(e):
            logger.warning("Failed to edit slide message: %s", e)


# ---------------------------------------------------------------------------
# GLOBAL ERROR HANDLER
# ---------------------------------------------------------------------------
async def handle_error(update: Optional[object], context: ContextTypes.DEFAULT_TYPE) -> None:
    """Concise global error interceptor to prevent silent failures."""
    err = context.error
    if isinstance(err, (InvalidToken, Forbidden)):
        logger.error("Authentication/Authorization error: %s", err)
    elif isinstance(err, NetworkError):
        logger.warning("Network transmission error: %s", err)
    else:
        logger.error("Unhandled handler exception: %s", err, exc_info=err)


# ---------------------------------------------------------------------------
# HANDLER REGISTRATION
# ---------------------------------------------------------------------------
BANG_COMMAND_HANDLERS: Dict[
    str, Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[None]]
] = {}


async def handle_bang_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    message = update.effective_message
    if not message or not message.text:
        return

    parts = message.text.split()
    command = parts[0][1:].split("@", 1)[0].lower()
    context.args = parts[1:]
    handler = BANG_COMMAND_HANDLERS.get(command)
    if handler:
        await handler(update, context)


def register_all_handlers(app: Application) -> None:
    """Registers all required command handlers and callback query handlers."""
    BANG_COMMAND_HANDLERS.clear()
    BANG_COMMAND_HANDLERS.update(
        {
            "help": handle_help,
            "ping": handle_ping,
            "uptime": handle_uptime,
            "status": handle_status,
            "addsudo": handle_addsudo,
            "delsudo": handle_delsudo,
            "sudolist": handle_sudolist,
            "nc": handle_nc,
            "setnc": handle_setnc,
            "delnc": handle_delnc,
            "delay": handle_delay,
            "stopnc": handle_stopnc,
            "stopall": handle_stopall,
            "promotebot": handle_promotebot,
            "leave": handle_leave,
            "spam1": handle_spam_slot,
            "spam2": handle_spam_slot,
            "spam3": handle_spam_slot,
            "spam4": handle_spam_slot,
            "stopspam": handle_stopspam,
            "msg4": handle_msg4,
            "setmsg4": handle_setmsg4,
            "slide1": handle_slide1,
            "slide2": handle_slide2,
            "setslide": handle_setslide,
            "stopslide": handle_stopslide,
        }
    )

    # General Commands
    app.add_handler(CommandHandler("help", handle_help))
    app.add_handler(
        MessageHandler(
            filters.Regex(r"^![A-Za-z0-9_]+(?:@\w+)?(?:\s+.*)?$"),
            handle_bang_command,
        )
    )
    app.add_handler(CommandHandler("ping", handle_ping))
    app.add_handler(CommandHandler("uptime", handle_uptime))
    app.add_handler(CommandHandler("status", handle_status))

    # Sudo Management Commands
    app.add_handler(CommandHandler("addsudo", handle_addsudo))
    app.add_handler(CommandHandler("delsudo", handle_delsudo))
    app.add_handler(CommandHandler("sudolist", handle_sudolist))

    # NC Feature Commands (Strictly 6 slots)
    app.add_handler(CommandHandler("nc", handle_nc))
    app.add_handler(CommandHandler("setnc", handle_setnc))
    app.add_handler(CommandHandler("delnc", handle_delnc))
    app.add_handler(CommandHandler("delay", handle_delay))
    app.add_handler(CommandHandler("stopnc", handle_stopnc))
    app.add_handler(CommandHandler("stopall", handle_stopall))
    app.add_handler(CommandHandler("promotebot", handle_promotebot))
    app.add_handler(CommandHandler("leave", handle_leave))

    # Controlled test-message features
    for command_name in ("spam1", "spam2", "spam3", "spam4"):
        app.add_handler(CommandHandler(command_name, handle_spam_slot))
    app.add_handler(CommandHandler("stopspam", handle_stopspam))

    # Message Features: 4-Message Sequence
    app.add_handler(CommandHandler("msg4", handle_msg4))
    app.add_handler(CommandHandler("setmsg4", handle_setmsg4))

    # Message Features: 2-Slide Interactive Card
    app.add_handler(CommandHandler("slide1", handle_slide1))
    app.add_handler(CommandHandler("slide2", handle_slide2))
    app.add_handler(CommandHandler("setslide", handle_setslide))
    app.add_handler(CommandHandler("stopslide", handle_stopslide))
    app.add_handler(CallbackQueryHandler(handle_slide_callback, pattern=r"^slide:\d+$"))

    # Register persisted NC names directly and retain the dynamic fallback for renamed slots.
    for nc_command in db_manager.get_nc_commands().values():
        logger.debug("[NC] registering command: /%s", nc_command)
        BANG_COMMAND_HANDLERS[nc_command] = handle_dynamic_nc
        app.add_handler(CommandHandler(nc_command, handle_dynamic_nc))
    app.add_handler(MessageHandler(filters.COMMAND, handle_dynamic_nc), group=1)

    # Global Error Handler
    app.add_error_handler(handle_error)


# ---------------------------------------------------------------------------
# MAIN APPLICATION LIFECYCLE
# ---------------------------------------------------------------------------
async def run_task_management_test() -> None:
    """Exercise task ownership and cleanup without contacting Telegram."""
    for registry in (nc_tasks, spam_tasks, slide_tasks):
        registry.clear()
    for tasks in _tracked_tasks.values():
        tasks.clear()

    async def mock_operation(fail: bool = False) -> None:
        await asyncio.sleep(0)
        if fail:
            raise RuntimeError("isolated mock failure")

    async def start_mock(
        category: str,
        registry: Dict[TaskKey, asyncio.Task[Any]],
        chat_id: int,
        bot_id: int,
        fail: bool = False,
    ) -> asyncio.Task[Any]:
        key = (chat_id, bot_id)
        await _cancel_task(registry.get(key))
        task = create_tracked_task(
            category,
            _run_bot_operation(
                category, bot_id, lambda: mock_operation(fail)
            ),
        )
        registry[key] = task
        return task

    replaced = await start_mock("nc", nc_tasks, 101, 1)
    await start_mock("nc", nc_tasks, 101, 1)
    await asyncio.gather(replaced, return_exceptions=True)

    spam_failed = await start_mock("spam", spam_tasks, 102, 2, fail=True)
    spam_completed = await start_mock("spam", spam_tasks, 102, 3)
    await asyncio.gather(spam_failed, spam_completed, return_exceptions=True)

    slide_completed = await start_mock("slide", slide_tasks, 103, 4)
    await asyncio.gather(slide_completed, return_exceptions=True)
    await asyncio.sleep(0)
    await start_mock("slide", slide_tasks, 103, 4)
    await start_mock("slide", slide_tasks, 103, 5)
    stopped = await _stop_bot_tasks("slide", slide_tasks, 103)
    if stopped != 2:
        raise AssertionError(f"expected two slide tasks to stop, got {stopped}")

    await asyncio.sleep(0)
    if nc_tasks or spam_tasks or slide_tasks or any(_tracked_tasks.values()):
        raise AssertionError("task registries retained a completed or stopped task")
    logger.info("[TASK TEST] duplicate replacement, stop ownership, cleanup, and isolation passed")


async def main() -> None:
    """Main asynchronous execution lifecycle."""
    if TASK_TEST_MODE:
        await run_task_management_test()
        return

    # Initialize and start all configured bot instances
    await bot_manager.start_all()

    # Loop until an external shutdown trigger arrives
    stop_event = asyncio.Event()

    # For Unix systems, register signal handlers
    loop = asyncio.get_running_loop()
    if sys.platform != "win32":
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, stop_event.set)

    try:
        if sys.platform == "win32":
            # On Windows, periodically sleep to allow KeyboardInterrupt processing
            while not stop_event.is_set():
                await asyncio.sleep(1.0)
        else:
            await stop_event.wait()
    except (asyncio.CancelledError, KeyboardInterrupt):
        pass
    finally:
        for category in _tracked_tasks:
            await stop_tracked_tasks(category)
        await bot_manager.stop_all()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass