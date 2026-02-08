"""SQLAlchemy models for classification schema (macro_economic_sectors, sectors, industries, basic_industries)."""

from sqlalchemy import Column, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class MacroEconomicSector(Base):
    """Macro economic sector (top level)."""

    __tablename__ = "macro_economic_sectors"
    __table_args__ = {"schema": "classification"}

    mes_code = Column(String(20), primary_key=True)
    macro_economic_sector = Column(String(255), nullable=False)


class Sector(Base):
    """Sector (child of macro economic sector)."""

    __tablename__ = "sectors"
    __table_args__ = {"schema": "classification"}

    sect_code = Column(String(20), primary_key=True)
    sector_name = Column(String(255), nullable=False)
    mes_code = Column(
        String(20),
        ForeignKey("classification.macro_economic_sectors.mes_code"),
        nullable=False,
    )


class Industry(Base):
    """Industry (child of sector)."""

    __tablename__ = "industries"
    __table_args__ = {"schema": "classification"}

    ind_code = Column(String(20), primary_key=True)
    industry_name = Column(String(255), nullable=False)
    sect_code = Column(
        String(20),
        ForeignKey("classification.sectors.sect_code"),
        nullable=False,
    )


class BasicIndustry(Base):
    """Basic industry (leaf, child of industry)."""

    __tablename__ = "basic_industries"
    __table_args__ = {"schema": "classification"}

    basic_ind_code = Column(String(20), primary_key=True)
    basic_industry_name = Column(String(255), nullable=False)
    definition = Column(Text, nullable=True)
    ind_code = Column(
        String(20),
        ForeignKey("classification.industries.ind_code"),
        nullable=False,
    )
