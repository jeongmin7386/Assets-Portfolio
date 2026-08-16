import asyncio

from app.core.database import SessionLocal
from app.repositories.portfolio import SqlPortfolioRepository
from app.services.portfolio import PortfolioService
from app.services.snapshots import SnapshotService


async def main() -> None:
    async with SessionLocal() as session:
        portfolio = PortfolioService(SqlPortfolioRepository(session))
        result = await SnapshotService(session, portfolio).create()
        print(f"Snapshot complete: {result['snapshot_date']}")


if __name__ == "__main__":
    asyncio.run(main())
