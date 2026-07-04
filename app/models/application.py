import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.job import Job


class ApplicationStatus(enum.StrEnum):
    """Lifecycle of a job application, in the order it usually happens."""

    SAVED = "saved"          # offre mise de côté, pas encore postulé
    APPLIED = "applied"      # candidature envoyée
    INTERVIEW = "interview"  # entretien obtenu
    OFFER = "offer"          # proposition reçue
    REJECTED = "rejected"    # refus (ça fait partie du jeu !)


class Application(Base):
    """Tracks MY application to one job listing."""

    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True)
    # unique=True: one application per job listing, enforced by the database
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), unique=True)
    status: Mapped[ApplicationStatus] = mapped_column(
        # native_enum=False stores the value as a plain VARCHAR + CHECK
        # constraint: adding a status later is a trivial migration, whereas
        # PostgreSQL native enums are painful to alter.
        Enum(ApplicationStatus, native_enum=False, length=20),
        default=ApplicationStatus.SAVED,
    )
    notes: Mapped[str | None] = mapped_column(Text)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    job: Mapped[Job] = relationship()

    def __repr__(self) -> str:
        return f"Application(id={self.id}, job_id={self.job_id}, status={self.status})"
