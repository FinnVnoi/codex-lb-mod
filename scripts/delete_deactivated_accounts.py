from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.db.models import Account, AccountStatus
from app.db.session import SessionLocal
from app.modules.accounts.repository import AccountsRepository
from app.modules.accounts.service import AccountsService


async def main() -> None:
    async with SessionLocal() as session:
        result = await session.execute(
            select(Account.id, Account.email).where(Account.status == AccountStatus.DEACTIVATED)
        )
        rows = result.all()

    if not rows:
        print("No deactivated accounts found.")
        return

    print(f"Found {len(rows)} deactivated accounts:")
    for acc_id, email in rows:
        print(f"  - {acc_id}  {email}")

    deleted = 0
    for acc_id, email in rows:
        async with SessionLocal() as session:
            service = AccountsService(AccountsRepository(session))
            ok = await service.delete_account(acc_id, delete_history=False)
        if ok:
            deleted += 1
            print(f"deleted: {acc_id}  {email}")
        else:
            print(f"NOT FOUND (skipped): {acc_id}  {email}")

    print(f"\nDone. Deleted {deleted}/{len(rows)} accounts.")


if __name__ == "__main__":
    asyncio.run(main())
