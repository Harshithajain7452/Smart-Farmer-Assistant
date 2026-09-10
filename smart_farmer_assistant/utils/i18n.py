"""
Lightweight JSON-file translation layer.

Translation catalogues live in ``static/locales/<lang>.json``. Missing keys
gracefully fall back to English and finally to the key itself, so a partially
translated catalogue never breaks a page.
"""
import json
import os

from flask import current_app, g, request, session

_CACHE = {}


def _load(lang: str) -> dict:
    if lang in _CACHE:
        return _CACHE[lang]
    path = os.path.join(current_app.static_folder, "locales", f"{lang}.json")
    data = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    _CACHE[lang] = data
    return data


def get_locale() -> str:
    """Resolve active language: session -> user profile -> browser -> default."""
    supported = current_app.config["SUPPORTED_LANGUAGES"]
    lang = session.get("lang")
    if lang in supported:
        return lang
    from flask_login import current_user  # local import avoids circular deps
    if current_user.is_authenticated and current_user.profile:
        if current_user.profile.preferred_language in supported:
            return current_user.profile.preferred_language
    best = request.accept_languages.best_match(list(supported.keys()))
    return best or current_app.config["DEFAULT_LANGUAGE"]


def translate(key: str, **kwargs) -> str:
    """Template helper exposed as ``t()``."""
    lang = getattr(g, "lang", None) or get_locale()
    value = _load(lang).get(key) or _load("en").get(key) or key
    if kwargs:
        try:
            value = value.format(**kwargs)
        except (KeyError, IndexError):
            pass
    return value
