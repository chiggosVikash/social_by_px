from sqlalchemy import Integer, String, Boolean, ForeignKey, DateTime, Float, JSON, Text, func, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import List, Optional
from datetime import datetime
from db.base import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    firebase_uid: Mapped[Optional[str]] = mapped_column(String, unique=True, index=True, nullable=True) # Adding for Firebase Auth
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[Optional[str]] = mapped_column(String, nullable=True) # Make nullable for users who sign up via Google
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=func.now())
    
    projects: Mapped[List["Project"]] = relationship("Project", back_populates="owner")
    social_accounts: Mapped[List["SocialAccount"]] = relationship("SocialAccount", back_populates="owner")

class Project(Base):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    industry: Mapped[Optional[str]] = mapped_column(String)
    owner_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    avoid_image_generation: Mapped[bool] = mapped_column(Boolean, default=False)
    background_image_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    style_preset: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        server_default="general_soft",
        index=True,
    )
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=func.now())
    
    owner: Mapped["User"] = relationship("User", back_populates="projects")
    keywords: Mapped[List["ProjectKeyword"]] = relationship("ProjectKeyword", back_populates="project")
    articles: Mapped[List["Article"]] = relationship("Article", back_populates="project")
    workflow_runs: Mapped[List["WorkflowRun"]] = relationship("WorkflowRun", back_populates="project", cascade="all, delete-orphan")

class WorkflowRun(Base):
    __tablename__ = "workflow_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("projects.id"))
    status: Mapped[str] = mapped_column(String, nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    project: Mapped["Project"] = relationship("Project", back_populates="workflow_runs")

class ProjectKeyword(Base):
    __tablename__ = "project_keywords"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("projects.id"))
    keyword: Mapped[str] = mapped_column(String, nullable=False)
    
    project: Mapped["Project"] = relationship("Project", back_populates="keywords")

class SocialAccount(Base):
    __tablename__ = "social_accounts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    owner_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    platform: Mapped[str] = mapped_column(String, nullable=False) # e.g., 'facebook', 'instagram'
    account_id: Mapped[str] = mapped_column(String, nullable=False)
    access_token: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=func.now())
    
    owner: Mapped["User"] = relationship("User", back_populates="social_accounts")

class Article(Base):
    __tablename__ = "articles"
    # [SOLID: SRP] — Scoping unique constraint to (project_id, url) to allow same article in multiple projects
    __table_args__ = (
        UniqueConstraint("project_id", "url", name="uq_article_project_url"),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("projects.id"))
    title: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)
    source: Mapped[Optional[str]] = mapped_column(String)
    published_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String, default="pending") # pending, approved, rejected, published
    relevance_score: Mapped[Optional[float]] = mapped_column(Float)
    
    project: Mapped["Project"] = relationship("Project", back_populates="articles")
    slides: Mapped[List["Slide"]] = relationship("Slide", back_populates="article")

class Slide(Base):
    __tablename__ = "slides"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    article_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("articles.id"))
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    hook_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # question | statistic | bold_claim | story | cta
    image_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    text_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    caption: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    emoji: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    text_zone: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        server_default="center-bottom third",
    )
    visual_type: Mapped[Optional[str]] = mapped_column(
        String(16),
        nullable=True,
        server_default="minimalist",
    )

    article: Mapped["Article"] = relationship("Article", back_populates="slides")

