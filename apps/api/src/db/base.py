from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

from src.models.core import User, Project, ProjectKeyword, SocialAccount, Article, WorkflowRun, Slide, MediaAsset, Approval, PublishJob

