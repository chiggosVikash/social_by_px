from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Float, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from src.db.base import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    projects = relationship("Project", back_populates="owner")
    social_accounts = relationship("SocialAccount", back_populates="owner")

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    industry = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    owner = relationship("User", back_populates="projects")
    keywords = relationship("ProjectKeyword", back_populates="project")
    articles = relationship("Article", back_populates="project")
    workflow_runs = relationship("WorkflowRun", back_populates="project")

class ProjectKeyword(Base):
    __tablename__ = "project_keywords"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    keyword = Column(String, nullable=False)
    
    project = relationship("Project", back_populates="keywords")

class SocialAccount(Base):
    __tablename__ = "social_accounts"
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    platform = Column(String, nullable=False) # e.g., 'facebook', 'instagram'
    account_id = Column(String, nullable=False)
    access_token = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    owner = relationship("User", back_populates="social_accounts")

class Article(Base):
    __tablename__ = "articles"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    title = Column(String, nullable=False)
    url = Column(String, unique=True, nullable=False)
    source = Column(String)
    published_date = Column(DateTime)
    summary = Column(Text)
    status = Column(String, default="pending") # pending, approved, rejected, published
    relevance_score = Column(Float)
    
    project = relationship("Project", back_populates="articles")
    slides = relationship("Slide", back_populates="article")

class WorkflowRun(Base):
    __tablename__ = "workflow_runs"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    status = Column(String, default="started")
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    logs = Column(JSON, nullable=True)
    
    project = relationship("Project", back_populates="workflow_runs")

class Slide(Base):
    __tablename__ = "slides"
    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id"))
    order_index = Column(Integer, nullable=False)
    image_url = Column(String, nullable=True)
    text_content = Column(Text, nullable=True)
    
    article = relationship("Article", back_populates="slides")

class MediaAsset(Base):
    __tablename__ = "media_assets"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    asset_type = Column(String) # logo, template, thumbnail
    file_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Approval(Base):
    __tablename__ = "approvals"
    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id"))
    status = Column(String) # approved, rejected, regenerate
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class PublishJob(Base):
    __tablename__ = "publish_jobs"
    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id"))
    social_account_id = Column(Integer, ForeignKey("social_accounts.id"))
    status = Column(String, default="pending") # pending, processing, success, failed
    error_message = Column(Text, nullable=True)
    published_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
