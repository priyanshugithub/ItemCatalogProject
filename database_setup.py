import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
 
Base = declarative_base()

class User(Base):
	__tablename__ = 'user'

	id = Column(Integer, primary_key=True)
	name = Column(String(250), nullable=False)
	email = Column(String(250), nullable=False)
	picture = Column(String(250))
 
class Genre(Base):
    __tablename__ = 'genre'
   
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name'        : self.name,
            'id'          : self.id,
            'user_id'   :self.user_id 
        }

class Movie(Base):
    __tablename__ = 'movie'


    name =Column(String(80), nullable = False)
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    region = Column(String(20))
    genre_id = Column(Integer,ForeignKey('genre.id'))
    genre = relationship(Genre)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User) 

#We added this serialize function to be able to send JSON objects in a serializable format
    @property
    def serialize(self):
       
       return {
           'name'         : self.name,
           'description'  : self.description,
           'region'       : self.region,
           'id'           : self.id
            }
 

engine = create_engine('sqlite:///moviebaseusers.db')
 

Base.metadata.create_all(engine)