from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, TextIO

import sqlalchemy as sa
from advanced_alchemy.base import IdentityAuditBase
from sqlalchemy import ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from v2.db.models import GradSession, OptimizationLog, SolutionCommission

from v2.db.models.enums import SolverEnum


@dataclass
class OptimizationConfiguration(IdentityAuditBase):
    __tablename__ = "optimization_configurations"
    __table_args__ = (
        CheckConstraint(
            "NOT online OR (min_professor_number IS NOT NULL AND min_professor_number_masters IS NOT NULL AND max_professor_number IS NOT NULL)",
            name="ck_online_requires_professor_numbers"
        ),
    )

    title: Mapped[str] = mapped_column(
        sa.String(256),
        nullable=False,
        server_default="Nuova configurazione",
        default="Nuova configurazione")

    # Session Foreign Key
    session_id: Mapped[int] = mapped_column(sa.BigInteger, ForeignKey("sessions.id"), nullable=False)
    session: Mapped['GradSession'] = relationship(
        "GradSession",
        back_populates="configurations",
        lazy="selectin")

    max_duration: Mapped[int] = mapped_column(sa.Integer, nullable=False, server_default='210', default=210)
    max_commissions_morning: Mapped[int] = mapped_column(sa.Integer, nullable=False, server_default='6', default=6)
    max_commissions_afternoon: Mapped[int] = mapped_column(sa.Integer, nullable=False, server_default='6', default=6)

    online: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default='True', default=True)
    min_professor_number: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    min_professor_number_masters: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    max_professor_number: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)

    solver: Mapped[SolverEnum] = mapped_column(
        sa.Enum(SolverEnum),
        nullable=False,
        default=SolverEnum.CPLEX,
        server_default=SolverEnum.CPLEX.value)

    optimization_time_limit: Mapped[int] = mapped_column(sa.Integer, nullable=False, server_default='60', default=60)
    optimization_gap: Mapped[float] = mapped_column(sa.Float, nullable=False, server_default='0.005', default=0.005)
    run_lock: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default='False', default=False)

    optimization_log: Mapped[OptimizationLog | None] = relationship(
        "OptimizationLog",
        back_populates="opt_config",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    commissions: Mapped[list['SolutionCommission'] | None] = relationship(
        "SolutionCommission",
        back_populates="opt_config",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def create_dat_file(self, base_path: Path) -> tuple[Path, Path]:
        dat_file = base_path / "temp.dat"
        excel_path = base_path / "val.xls"

        base_path.mkdir(parents=True, exist_ok=True)

        morning_commissions = list(range(0, self.max_commissions_morning))
        afternoon_commissions = list(range(
            self.max_commissions_morning,
            self.max_commissions_morning + self.max_commissions_afternoon
        ))

        with dat_file.open("w") as f:
            f.write(f"param max_durata := {self.max_duration};\n")
            f.write(f"set commissioni_mattina := {' '.join(map(str, morning_commissions))};\n")
            f.write(f"set commissioni_pomeriggio := {' '.join(map(str, afternoon_commissions))};\n")
            f.write(f"param excel_path := \"{excel_path.resolve()}\";\n")

            if self.online:
                f.write(f"param minDocenti := {self.min_professor_number};\n")
                f.write(f"param minDocentiMag := {self.min_professor_number_masters};\n")
                f.write(f"param max_doc := {self.max_professor_number};\n")

        return base_path, dat_file

    def create_virtual_dat_file(self, base_path: Path) -> tuple[Path, TextIO]:
        excel_path = base_path / "val.xls"
        base_path.mkdir(parents=True, exist_ok=True)

        # Create a temporary file that will be automatically deleted
        dat_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.dat',
            prefix='temp_',
            delete=True  # This is the default, file will be deleted when closed
        )

        morning_commissions = list(range(0, self.max_commissions_morning))
        afternoon_commissions = list(range(
            self.max_commissions_morning,
            self.max_commissions_morning + self.max_commissions_afternoon
        ))

        dat_file.write(f"param max_durata := {self.max_duration};\n")
        dat_file.write(f"set commissioni_mattina := {' '.join(map(str, morning_commissions))};\n")
        dat_file.write(f"set commissioni_pomeriggio := {' '.join(map(str, afternoon_commissions))};\n")
        dat_file.write(f"param excel_path := \"{excel_path.resolve()}\";\n")

        if self.online:
            dat_file.write(f"param minDocenti := {self.min_professor_number};\n")
            dat_file.write(f"param minDocentiMag := {self.min_professor_number_masters};\n")
            dat_file.write(f"param max_doc := {self.max_professor_number};\n")

        dat_file.flush()  # Ensure data is written to disk

        # Return the base path and the temporary file object
        # The file path can be accessed via dat_file.name
        return base_path, dat_file  # type: ignore
