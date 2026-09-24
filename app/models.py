from datetime import date, datetime
from uuid import uuid4

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def id_default() -> str:
    return str(uuid4())


class Timestamped:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class Owner(Timestamped, Base):
    __tablename__ = "owners"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=id_default)
    name: Mapped[str] = mapped_column(String(200))
    profiles: Mapped[list["Profile"]] = relationship(back_populates="owner")


class Profile(Timestamped, Base):
    __tablename__ = "profiles"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=id_default)
    owner_id: Mapped[str] = mapped_column(ForeignKey("owners.id"), index=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    headline: Mapped[str] = mapped_column(String(300))
    summary: Mapped[str] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    github_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    owner: Mapped[Owner] = relationship(back_populates="profiles")
    experiences: Mapped[list["Experience"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )
    education: Mapped[list["Education"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )
    skill_groups: Mapped[list["SkillGroup"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )
    projects: Mapped[list["Project"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )
    contact_configuration: Mapped["ContactConfiguration"] = relationship(
        back_populates="profile", uselist=False, cascade="all, delete-orphan"
    )


class Experience(Timestamped, Base):
    __tablename__ = "experiences"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=id_default)
    profile_id: Mapped[str] = mapped_column(ForeignKey("profiles.id"), index=True)
    employer: Mapped[str] = mapped_column(String(200))
    title: Mapped[str] = mapped_column(String(200))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    summary: Mapped[str] = mapped_column(Text)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    profile: Mapped[Profile] = relationship(back_populates="experiences")
    accomplishments: Mapped[list["ExperienceAccomplishment"]] = relationship(
        back_populates="experience", cascade="all, delete-orphan"
    )


class ExperienceAccomplishment(Timestamped, Base):
    __tablename__ = "experience_accomplishments"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=id_default)
    experience_id: Mapped[str] = mapped_column(ForeignKey("experiences.id"), index=True)
    content: Mapped[str] = mapped_column(Text)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    experience: Mapped[Experience] = relationship(back_populates="accomplishments")


class Education(Timestamped, Base):
    __tablename__ = "education"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=id_default)
    profile_id: Mapped[str] = mapped_column(ForeignKey("profiles.id"), index=True)
    institution: Mapped[str] = mapped_column(String(200))
    program: Mapped[str] = mapped_column(String(200))
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    profile: Mapped[Profile] = relationship(back_populates="education")


class SkillGroup(Timestamped, Base):
    __tablename__ = "skill_groups"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=id_default)
    profile_id: Mapped[str] = mapped_column(ForeignKey("profiles.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    profile: Mapped[Profile] = relationship(back_populates="skill_groups")
    skills: Mapped[list["Skill"]] = relationship(
        back_populates="group", cascade="all, delete-orphan"
    )


class Skill(Timestamped, Base):
    __tablename__ = "skills"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=id_default)
    group_id: Mapped[str] = mapped_column(ForeignKey("skill_groups.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    group: Mapped[SkillGroup] = relationship(back_populates="skills")


class Project(Timestamped, Base):
    __tablename__ = "projects"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=id_default)
    profile_id: Mapped[str] = mapped_column(ForeignKey("profiles.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    profile: Mapped[Profile] = relationship(back_populates="projects")


class ContactConfiguration(Timestamped, Base):
    __tablename__ = "contact_configurations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=id_default)
    profile_id: Mapped[str] = mapped_column(
        ForeignKey("profiles.id"), unique=True, index=True
    )
    to_address: Mapped[str] = mapped_column(String(320))
    from_address: Mapped[str] = mapped_column(String(320))
    call_to_action: Mapped[str] = mapped_column(String(200), default="Get in touch")
    profile: Mapped[Profile] = relationship(back_populates="contact_configuration")
