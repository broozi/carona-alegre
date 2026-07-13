"""Funções utilitárias reutilizadas por formulários e controladores."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from flask import current_app


def only_digits(value: str | None) -> str:
    return re.sub(r"\D", "", value or "")


def normalize_email(value: str) -> str:
    return value.strip().lower()


def normalize_plate(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", value or "").upper()


def is_valid_cpf(value: str) -> bool:
    cpf = only_digits(value)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False

    for length in (9, 10):
        total = sum(int(cpf[index]) * (length + 1 - index) for index in range(length))
        digit = (total * 10) % 11
        digit = 0 if digit == 10 else digit
        if digit != int(cpf[length]):
            return False
    return True


def local_now() -> datetime:
    tz_name = current_app.config["APP_TIMEZONE"]
    try:
        tz = ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        tz = timezone.utc
    return datetime.now(tz).replace(tzinfo=None)
