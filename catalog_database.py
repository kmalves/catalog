import sys

from sqlalchemy import Column, ForeignKey, Integer, String

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import relationship

from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'
    name = Column(
        String(80), nullable=False)
    email = Column(
        String(80), nullable=False)
    picture = Column(
        String(250))
    id = Column(
        Integer, primary_key=True)


class ActivityCategory(Base):
    __tablename__ = 'category'
    name = Column(
        String(80), nullable=False)
    id = Column(
        Integer, primary_key=True)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id
        }


class ActivityItem(Base):
    __tablename__ = 'item'
    name = Column(
        String(80), nullable=False)
    id = Column(
        Integer, primary_key=True)
    description = Column(String(500))
    website = Column(String(80))
    category_id = Column(
        Integer, ForeignKey('category.id'))
    category = relationship(ActivityCategory)
    user_id = Column(
        Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        return {
            'name': self.name,
            'description': self.description,
            'website': self.website,
            'id': self.id,
            'user_id': self.user_id
        }


engine = create_engine(
    'sqlite:///activitiescatalogwithuser.db')

Base.metadata.create_all(engine)
