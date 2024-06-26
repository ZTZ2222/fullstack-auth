from typing import Annotated
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies.auth import (
    get_current_active_user,
    get_current_admin_user,
)
from core.config import settings
from core.models import db_helper
from core.schemas import (
    UserRead,
    UserUpdate,
)
from core.schemas.users import SuperuserCreate
from core.services import UserService
from utils.exceptions import UnauthorizedAccessException


router = APIRouter(
    prefix=settings.api.v1.users,
    tags=["users"],
)


@router.get(
    "", response_model=list[UserRead], dependencies=[Depends(get_current_admin_user)]
)
async def get_multiple_users(
    # fancy writing style of this:
    # session: AsyncSession = Depends(db_helper.session_getter),
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
    offset: int = Query(
        0,
        description="The number of items to skip before starting to collect the result set",
    ),
    limit: int = Query(10, description="The maximum number of items to return"),
):
    user_crud = UserService(session=session)
    users = await user_crud.get_users_paginated(offset=offset, limit=limit)
    return users


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
    user_id: int,
    current_user: UserRead = Depends(get_current_active_user),
):
    if current_user.id != user_id and not current_user.is_superuser:
        raise UnauthorizedAccessException
    user_crud = UserService(session=session)
    user = await user_crud.find_user(id=user_id)
    return user


@router.put("/{user_id}", response_model=UserRead)
async def update_user(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
    user_id: int,
    user_update: UserUpdate,
    current_user: UserRead = Depends(get_current_active_user),
):
    if current_user.id != user_id and not current_user.is_superuser:
        raise UnauthorizedAccessException
    user_crud = UserService(session=session)
    user = await user_crud.update_user(user_id=user_id, user_update=user_update)
    return user


@router.delete("/{user_id}")
async def delete_user(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
    user_id: int,
    current_user: UserRead = Depends(get_current_active_user),
):
    if current_user.id != user_id and not current_user.is_superuser:
        raise UnauthorizedAccessException
    user_crud = UserService(session=session)
    await user_crud.delete_user(user_id=user_id)

    return {"message": "User deleted successfully"}


@router.post(
    "/superuser",
    response_model=UserRead,
    dependencies=[Depends(get_current_admin_user)],
)
async def create_superuser(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
    user_create: SuperuserCreate,
):
    user_crud = UserService(session=session)
    user = await user_crud.create_user(user_create=user_create)
    return user
