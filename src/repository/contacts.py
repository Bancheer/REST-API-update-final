from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, and_, extract

from src.entity.models import Contact, User
from src.schema import contact
from src.schema.contact import ContactSchema, ContactUpdate


async def get_contacts(limit: int, offset: int, name: str, surname: str, email: str, db: AsyncSession,
                       user: User):
    """
        Retrieves a list of contacts for a specific user with optional filtering by name, surname, and email.

        Args:
            limit (int): The maximum number of contacts to return.
            offset (int): The offset to start the query from.
            name (str): Optional filter by the contact's name.
            surname (str): Optional filter by the contact's surname.
            email (str): Optional filter by the contact's email.
            db (AsyncSession): The database session.
            user (User): The user whose contacts are being retrieved.

        Returns:
            List[Contact]: A list of contacts that match the criteria.
        """
    statement = select(Contact).filter_by(user=user).offset(offset).limit(limit)

    if name:
        statement = statement.filter(Contact.name.ilike(f"%{name}%"))
    if surname:
        statement = statement.filter(Contact.surname.ilike(f"%{surname}%"))
    if email:
        statement = statement.filter(Contact.email.ilike(f"%{email}%"))

    contacts = await db.execute(statement)
    await db.close()
    return contacts.scalars().all()


async def get_all_contacts(limit: int, offset: int, db: AsyncSession):
    """
        Retrieves a list of all contacts in the database with pagination.

        Args:
            limit (int): The maximum number of contacts to return.
            offset (int): The offset to start the query from.
            db (AsyncSession): The database session.

        Returns:
            List[Contact]: A list of contacts.
        """
    statement = select(Contact).offset(offset).limit(limit)

    contacts = await db.execute(statement)
    await db.close()
    return contacts.scalars().all()


async def get_contact(contact_id: int, db: AsyncSession, user: User):
    """
        Retrieves a single contact by ID for a specific user.

        Args:
            contact_id (int): The ID of the contact to retrieve.
            db (AsyncSession): The database session.
            user (User): The user whose contact is being retrieved.

        Returns:
            Contact or None: The requested contact, or None if not found.
        """
    statement = select(Contact).filter_by(id=contact_id, user=user)
    contact = await db.execute(statement)
    await db.close()
    return contact.scalar_one_or_none()


async def create_contact(body: ContactSchema, db: AsyncSession, user: User):
    """
        Creates a new contact for a user.

        Args:
            body (ContactSchema): The contact data to create.
            db (AsyncSession): The database session.
            user (User): The user for whom the contact is being created.

        Returns:
            Contact: The newly created contact.

        Raises:
            HTTPException: If the birthday is in the future or a database error occurs.
        """
    if body.birthday >= date.today():
        raise HTTPException(status_code=400, detail="Birthday must be in the past")

    try:
        contact = Contact(**body.model_dump(), user=user)
        db.add(contact)
        await db.commit()
        await db.refresh(contact)
        return contact
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        await db.close()


async def update_contact(contact_id: int, contact_update: ContactUpdate, db: AsyncSession, user: User):
    """
        Updates an existing contact by ID for a specific user.

        Args:
            contact_id (int): The ID of the contact to update.
            contact_update (ContactUpdate): The updated contact data.
            db (AsyncSession): The database session.
            user (User): The user whose contact is being updated.

        Returns:
            Contact or None: The updated contact, or None if not found.

        Raises:
            HTTPException: If the contact is not found.
        """
    statement = select(Contact).filter_by(id=contact_id, user=user)
    existing_contact = await db.execute(statement)
    existing_contact = existing_contact.scalar_one_or_none()

    if not existing_contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    if existing_contact:
        for key, value in contact_update.model_dump().items():
            setattr(existing_contact, key, value)
        await db.commit()
        await db.refresh(existing_contact)
        await db.close()
    return existing_contact


async def delete_contact(contact_id: int, db: AsyncSession, user: User):
    """
        Deletes a contact by ID for a specific user.

        Args:
            contact_id (int): The ID of the contact to delete.
            db (AsyncSession): The database session.
            user (User): The user whose contact is being deleted.

        Returns:
            Contact or None: The deleted contact, or None if not found.

        Raises:
            HTTPException: If the contact is not found.
        """
    statement = select(Contact).filter_by(id=contact_id, user=user)
    contact = await db.execute(statement)
    contact = contact.scalar_one_or_none()

    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    if contact:
        await db.delete(contact)
        await db.commit()
        return contact


async def get_upcoming_birthdays(db: AsyncSession, user: User):
    """
        Retrieves contacts with upcoming birthdays within the next week for a specific user.

        Args:
            db (AsyncSession): The database session.
            user (User): The user whose contacts are being checked for upcoming birthdays.

        Returns:
            List[Contact]: A list of contacts with upcoming birthdays.
        """
    today = date.today()
    next_week = today + timedelta(days=7)

    query = select(Contact).filter(
        or_(
            and_(
                extract('month', Contact.birthday) == today.month,
                extract('day', Contact.birthday) >= today.day,
                extract('month', Contact.birthday) == next_week.month,
                extract('day', Contact.birthday) <= next_week.day,
            ),
            and_(
                today.month != next_week.month,
                or_(
                    and_(
                        extract('month', Contact.birthday) == today.month,
                        extract('day', Contact.birthday) >= today.day,
                    ),
                    and_(
                        extract('month', Contact.birthday) == next_week.month,
                        extract('day', Contact.birthday) <= next_week.day,
                    )
                )
            )
        )
    )

    result = await db.execute(query)
    await db.close()
    return result.scalars().all()
