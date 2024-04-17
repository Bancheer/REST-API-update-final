from fastapi import APIRouter, HTTPException, Depends, status, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.entity.models import User, Role
from src.repository import contacts as repository_contacts
from src.schema.contact import ContactSchema, ContactUpdate, ContactResponse
from src.services.auth import auth_service
from src.services.roles import RoleAccess

router = APIRouter(prefix='/contacts', tags=['contacts'])

access_to_route_all = RoleAccess([Role.admin, Role.moderator])


@router.get('/', response_model=list[ContactResponse])
async def get_contacts(limit: int = Query(10, ge=10, le=100), offset: int = Query(0, ge=0),
                       name: str = Query(None, title="Name filter"), surname: str = Query(None, title="Surname filter"),
                       email: str = Query(None, title="Email filter"), db: AsyncSession = Depends(get_db),
                       user: User = Depends(auth_service.get_current_user)):
    contacts = await repository_contacts.get_contacts(limit, offset, name, surname, email, db, user)
    if contacts:
        return contacts
    else:
        raise HTTPException(status_code=404, detail="Contacts not found")


@router.get('/all', response_model=list[ContactResponse], dependencies=[Depends(access_to_route_all)])
async def get_all_contacts(limit: int = Query(10, ge=10, le=100), offset: int = Query(0, ge=0),
                           db: AsyncSession = Depends(get_db)):
    contacts = await repository_contacts.get_all_contacts(limit, offset, db)
    if contacts:
        return contacts
    else:
        raise HTTPException(status_code=404, detail="Contacts not found")


@router.get('/{contacts_id}', response_model=ContactResponse)
async def get_contact(contacts_id: int, db: AsyncSession = Depends(get_db),
                      user: User = Depends(auth_service.get_current_user)):
    contact = await repository_contacts.get_contact(contacts_id, db, user)
    if contact:
        return contact
    else:
        raise HTTPException(status_code=404, detail="Contact not found")


@router.post('/', response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(body: ContactSchema, db: AsyncSession = Depends(get_db),
                         user: User = Depends(auth_service.get_current_user)):
    contact = await repository_contacts.create_contact(body, db, user)
    return contact


@router.put('/{contacts_id}', response_model=ContactResponse, status_code=status.HTTP_200_OK)
async def update_contact(contacts_id: int, body: ContactUpdate, db: AsyncSession = Depends(get_db),
                         user: User = Depends(auth_service.get_current_user)):
    contact = await repository_contacts.update_contact(contacts_id, body, db, user)
    if contact:
        return contact
    else:
        raise HTTPException(status_code=404, detail="Contact not found")


@router.delete('/{contacts_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(contacts_id: int, db: AsyncSession = Depends(get_db),
                         user: User = Depends(auth_service.get_current_user)):
    contact = await repository_contacts.delete_contact(contacts_id, db, user)
    if contact:
        return contact
    else:
        raise HTTPException(status_code=404, detail="Contact not found")


@router.get("/birthday/", response_model=list[ContactResponse])
async def get_upcoming_birthdays(db: AsyncSession = Depends(get_db),
                                 user: User = Depends(auth_service.get_current_user)):
    contacts = await repository_contacts.get_upcoming_birthdays(db, user)
    if contacts:
        return contacts
    else:
        raise HTTPException(status_code=404, detail="Contacts not found")
