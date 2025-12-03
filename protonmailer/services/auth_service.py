"""Lightweight, local-only session authentication helpers."""

from fastapi import HTTPException, Request, status

from protonmailer.config import get_settings


def is_authenticated(request: Request) -> bool:
    return bool(request.session.get("authenticated"))


def require_login(request: Request) -> bool:
    if not is_authenticated(request):
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/ui/login"},
        )
    return True


def login_user(request: Request, username: str, password: str) -> bool:
    settings = get_settings()
    if username == settings.ADMIN_USERNAME and password == settings.ADMIN_PASSWORD:
        request.session["authenticated"] = True
        request.session["username"] = username
        return True
    return False


def logout_user(request: Request) -> None:
    request.session.clear()
