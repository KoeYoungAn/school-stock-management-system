from fastapi import Depends, HTTPException
import models
from auth import get_current_user

ADMIN = "Admin"
STOREKEEPER = "Storekeeper"
TEACHER = "Teacher"


def require_roles(*roles):
    def dep(user: models.User = Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(403, "Permission denied")
        return user
    return dep


def require_admin(user: models.User = Depends(get_current_user)):
    if user.role != ADMIN:
        raise HTTPException(403, "Admin only")
    return user


def require_staff(user: models.User = Depends(get_current_user)):
    """Admin or Storekeeper."""
    if user.role not in (ADMIN, STOREKEEPER):
        raise HTTPException(403, "Staff only")
    return user
