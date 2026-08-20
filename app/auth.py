from __future__ import annotations

from enum import Enum
from typing import Dict

from fastapi import Depends, Header, HTTPException


class Role(str, Enum):
    admin = "admin"
    practitioner = "practitioner"
    reviewer = "reviewer"
    auditor = "auditor"


# Dev keys for local usage. Replace with real IAM in production.
API_KEYS: Dict[str, Role] = {
    "admin-key": Role.admin,
    "practitioner-key": Role.practitioner,
    "reviewer-key": Role.reviewer,
    "auditor-key": Role.auditor,
}


def get_role(x_api_key: str = Header(default="", alias="X-API-Key")) -> Role:
    role = API_KEYS.get(x_api_key)
    if not role:
        raise HTTPException(status_code=401, detail="invalid or missing API key")
    return role


def require_roles(*allowed: Role):
    def checker(role: Role = Depends(get_role)) -> Role:
        if role not in allowed:
            raise HTTPException(status_code=403, detail="insufficient role")
        return role

    return checker
