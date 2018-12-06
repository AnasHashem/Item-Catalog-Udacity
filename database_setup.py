from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key = True)
    name = Column(String(250), nullable = False)
    email = Column(String(250), nullable = False)
    
class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key = True)
    name = Column(String(100), nullable = False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def json(self):
        return {
            'Id' : self.id,
            'Name' : self.name,
            'item' : ''
        }
    
    
class Item(Base):
    __tablename__ = 'item'

    id = Column(Integer, primary_key = True)
    name = Column(String(100), nullable = False)
    description = Column(String(5000), nullable = False)
    category_id = Column(Integer, ForeignKey('category.id'))
    user = relationship(User)
    user_id = Column(Integer, ForeignKey('user.id'))
    category = relationship(Category)

    @property
    def json(self):
        return {
            'id' : self.id,
            'name' : self.name,
            'description' : self.description,
            'cat_id' : self.category_id
        }    

engine = create_engine('sqlite:///itemcatalogwithusers.db?check_same_thread=False')

Base.metadata.create_all(engine)
