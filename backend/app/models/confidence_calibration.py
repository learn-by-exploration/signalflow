"""Confidence calibration model — tracks historical accuracy per score bucket."""

from sqlalchemy import Column, Integer, Numeric, String, TIMESTAMP, UniqueConstraint
from sqlalchemy.sql import func

from app.database import Base


class ConfidenceCalibration(Base):
    """Stores observed success rates for each confidence bucket per market type."""

    __tablename__ = "confidence_calibration"

    id = Column(Integer, primary_key=True, autoincrement=True)
    score_bucket = Column(Integer, nullable=False)  # 0-20, 20-40, 40-60, 60-80, 80-100
    total_signals = Column(Integer, default=0)
    successful_signals = Column(Integer, default=0)
    calibrated_probability = Column(Numeric(5, 4), nullable=True)
    market_type = Column(String(10), nullable=True)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("score_bucket", "market_type", name="uq_bucket_market"),
    )

    def __repr__(self) -> str:
        return (
            f"<ConfidenceCalibration bucket={self.score_bucket} "
            f"market={self.market_type} rate={self.calibrated_probability}>"
        )
