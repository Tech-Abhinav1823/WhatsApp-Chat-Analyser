import re
from typing import List

import pandas as pd

_TIME_STAMP_PATTERN = re.compile(
    r"(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4},\s+\d{1,2}:\d{2}"
    r"(?:[\s\u202f]?(?:AM|PM|am|pm|A\.M\.|P\.M\.))?)\s[-–]\s"
)

_VERBOSE_PERIODS = {
    "in the morning": "AM",
    "in the afternoon": "PM",
    "in the evening": "PM",
    "at night": "PM",
}


def _normalise_export_text(raw: str) -> str:
    """Clean up unicode quirks and convert verbose period labels to AM/PM."""
    clean_text = (
        raw.replace("\u202f", " ")  # narrow non-breaking space used before am/pm
        .replace("\u200f", "")      # rtl marks
        .replace("\ufeff", "")      # BOM
    )
    for verbose, replacement in _VERBOSE_PERIODS.items():
        clean_text = re.sub(verbose, replacement, clean_text, flags=re.IGNORECASE)
    return clean_text


def _split_records(text: str) -> List[str]:
    """Split chat export into alternating [timestamp, message] entries."""
    parts = re.split(_TIME_STAMP_PATTERN, text)[1:]
    if not parts:
        raise ValueError(
            "Could not detect WhatsApp timestamps. "
            "Please ensure the export is in plain text format."
        )
    return parts


def _parse_dates(date_strings: List[str]) -> pd.Series:
    """Parse date strings trying both MM/DD and DD/MM interpretations."""
    for day_first in (False, True):
        parsed = pd.to_datetime(date_strings, errors="coerce", dayfirst=day_first)
        if parsed.notna().all():
            return parsed
    raise ValueError("Unable to parse timestamps in the uploaded chat.")


def preprocess(data: str) -> pd.DataFrame:
    normalized = _normalise_export_text(data)
    parts = _split_records(normalized)
    dates = parts[0::2]
    messages = parts[1::2]

    if len(dates) != len(messages):
        raise ValueError("Mismatched timestamps and messages in the chat export.")

    df = pd.DataFrame({"user_message": messages, "date": _parse_dates(dates)})

    users: List[str] = []
    cleaned_messages: List[str] = []
    for message in df["user_message"]:
        entry = re.split(r"([\w\W]+?):\s", message)
        if entry[1:]:
            users.append(entry[1])
            cleaned_messages.append(entry[2])
        else:
            users.append("group_notification")
            cleaned_messages.append(entry[0])

    df["user"] = users
    df["message"] = cleaned_messages
    df.drop(columns=["user_message"], inplace=True)

    df["only_date"] = df["date"].dt.date
    df["year"] = df["date"].dt.year
    df["month_num"] = df["date"].dt.month
    df["month"] = df["date"].dt.month_name()
    df["day"] = df["date"].dt.day
    df["day_name"] = df["date"].dt.day_name()
    df["hour"] = df["date"].dt.hour
    df["minute"] = df["date"].dt.minute

    if df.empty:
        raise ValueError("The uploaded chat file contains no messages.")

    return df