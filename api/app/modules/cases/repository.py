from sqlalchemy.ext.asyncio import AsyncSession

class CaseRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
