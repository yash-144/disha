from sqlalchemy import Column, String, DateTime
from app.core.database import Base
from app.shared.utils import utc_now

class WellbeingEntity(Base):
    __tablename__ = "disha_wellbeing"
    id = Column(String(36), primary_key=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
