from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String

Base = declarative_base()

class ScrapeRaw(Base):
    __tablename__ = 'scrape_data_raw'
    
    id               = Column(Integer, primary_key=True)
    scrape_log_id    = Column(Integer)
    date_received    = Column(String)
    transaction_date = Column(String)
    card_number      = Column(String)
    amount           = Column(String)
    case_number      = Column(String)
    merchant_id      = Column(String)
    messages         = Column(String(1024))
    hash             = Column(Integer)
    
    def __repr__(self):
        return "<ScrapeRaw>"
