from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from scraperaw import ScrapeRaw
import ConfigParser
import logging
import sys

logging.basicConfig(filename='/var/log/scraper/watcher.log', level=logging.DEBUG)

class Upload(object):
    """
    This class takes the incoming dataset, de-duplicates it,
    uploads to the staging/raw table, again de-duplicates, then 
    inserts the data into the clean table.
    """
    def __init__(self):
        
        try:
            
            config = ConfigParser.ConfigParser()
            config.read('config.cfg')
            
            # Are we uploading to dev or stage?
            # Make this an IF statement:
            section = 'db.stage'
            
            conn_str = '%s://%s:%s@%s/%s' % (config.get(section, 'protocol'),
                                             config.get(section, 'uid'),
                                             config.get(section, 'pwd'),
                                             config.get(section, 'host'),
                                             config.get(section, 'database'),)
            
            logging.info('Connection String: ' % conn_str)
            
        except:
            # If we have config prob, default to loading local db.
            conn_str = 'mysql://hirsh:adboom123@mysql.adboom.technology/adboomadmin'
            #conn_str = 'mysql://root:adboom123@localhost/adboomadmin'
            #logging.debug('Unexpected error: %s' % sys.exc_info()[0])
            logging.debug('Exception: Using connect %s ' % conn_str)
        
        # For direct query to db
        engine = create_engine(conn_str)
        self.conn = engine.connect()
        
        # For ORM
        Session = sessionmaker(bind=engine)
        self.session = Session()
        
    def upload(self, data):
        """
        This takes the incoming dictionary and maps to our ORM object
        """
        # Returns our unique numeric hash
        # Unique is hash numeric of transaction_date, card_number, amount
        def uhash(*args):
            return hash('~~~'.join(args))
        
        # Holds list of hashes
        hlist = []
        
        for row in data:
            s = ScrapeRaw()
            s.scrape_log_id    = 1 #TODO: pass scrape_log_id
            s.date_received    = row['date_received']
            s.transaction_date = row['transaction_date']
            s.card_number      = row['card_number']
            s.amount           = row['amount']
            s.case_number      = row['case_number']
            s.merchant_id      = row['merchant_id']
            s.messages         = row['messages']
            s.hash             = uhash(s.transaction_date, s.card_number, s.amount)
            
            # Only add unique
            if s.hash in hlist:
                continue
            
            # Otherwise add the hash to the list and object to the session
            hlist.append(s.hash)
            self.session.add(s)
            
        # Truncate the raw data
        self.conn.execute("SET SQL_SAFE_UPDATES = 0")
        self.conn.execute("truncate table scrape_data_raw")
        
        # Upload the data
        self.session.commit()
        
        # Delete records that are already in the clean table
        self.conn.execute("delete from scrape_data_raw where hash in (select hash from scrape_data_clean)")
        
        # Insert new 'clean' records
        self.conn.execute(" insert into scrape_data_clean "\
           " (scrape_log_id, date_received, transaction_date, card_number, amount, case_number, merchant_id, messages, hash) "\
           " select scrape_log_id, date_received, transaction_date, card_number, amount, case_number, merchant_id, messages, hash from scrape_data_raw "
           )
        
        # Be safe young Padwan
        self.conn.execute("SET SQL_SAFE_UPDATES = 1")
            
            
        
        
        
        
        
        
        
        