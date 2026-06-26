from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, BigInteger, Double, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import JSONB
from orm.base import Base


class AlgorithmRunORM(Base):
    __tablename__ = "algorithm_runs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    algorithm_name: Mapped[str] = mapped_column(String(50), nullable=False)
    parameters: Mapped[dict | None] = mapped_column(JSONB)
    started_at: Mapped[object] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())
    execution_time_ms: Mapped[int | None] = mapped_column(BigInteger)
    hard_violations: Mapped[int | None] = mapped_column(Integer)
    soft_violations: Mapped[int | None] = mapped_column(Integer)
    fitness_score: Mapped[float | None] = mapped_column(Double)
    extra_metrics: Mapped[dict | None] = mapped_column(JSONB)