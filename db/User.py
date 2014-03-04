from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    firstname = Column(String)
    lastname = Column(String)
    email = Column(String)
    password = Column(String)
    created_at = Column(String)
    updated_at = Column(String)
    
    def __repr__(self):
        return "<User(firstname='%s', lastname='%s', email='%s', password='%s')>" % (
                         self.firstname, self.lastname, self.email, self.password)
    
