from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy import Sequence

Base = declarative_base()

class Portal(Base):
    __tablename__ = 'portals'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    scraper_name = Column(String)
    scraper_active = Column(Integer)
    login_url = Column(String)
    search_params = Column(String)
    created_at = Column(String)
    updated_at = Column(String)
    
    def __repr__(self):
        return "<User(firstname='%s', lastname='%s', email='%s', password='%s')>" % (
                         self.firstname, self.lastname, self.email, self.password)
    

