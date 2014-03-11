"""
Portal Class

This class is inherited by all the portal scraper classes
"""

import os
import sys
import json
import time
import logging
import ConfigParser
from db.upload import Upload

class Portal(object):
    def __init__(self, portal):
        self.portal = portal
        self.error  = False
        
        
    def setup(self, **params):
        """
        This initializes the class with all the parameters 
        it will need to scrape the site for the inherited class.
        """

        # Turn all the incoming kwargs to class variables
        params = params['params']
        for k, v in params.iteritems():
            setattr(self, k, v)
        
        # If max not specified, set to lots or records returned
        if not self.max_records > 0:
            self.max_records = 1000
            # self.logger.exception(sys.exc_info()[0])
            
        # Set the start time
        self.start_time = time.strftime("%Y%m%d.%I.%M.%S")
        
        # Set up logger for this scraper
        # TODO: get from config file
        self.logger = logging.getLogger('scraper')
        hdlr = logging.FileHandler('%s/%s.log' % (self.path, self.start_time))
        format = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        hdlr.setFormatter(format)
        self.logger.addHandler(hdlr)
        self.logger.setLevel(logging.DEBUG)

    def run(self):
        """
        Run!
        """
        
        self.logger.info('Starting scrape...')

        # Scrape data from site
        self.scrape()
        
        # Transform the scraped data into db table format
        self.transform()
        
        # Upload it to our database
        self.load()
        
        self.logger.info('----- DONE -----')

        
        
    def transform(self):
        # --------------------------------------------------
        # From here, all scrapers should have be able to 
        # call parent function to finish, so we are not duplicating
        # code
        # --------------------------------------------------
        if self.error:
            return
        
        # --------------------------------------------------
        # Trim down the data to only the fields we're looking for
        # And replace with canonical scraper table column name
        # --------------------------------------------------

        udata = []

        for rec in self.adata:
            d = {}
            
            for k, v in self._col_lookup.iteritems():
                if rec.has_key(v):
                    d[k] = rec[v].strip()
                else:
                    d[k] = ''
                
            udata.append(d)
        
        # --------------------------------------------------
        # Before saving the file we can either pickle the data
        # or turn it into JSON
        # --------------------------------------------------
        self.logger.info('Converting to JSON...')
        new_file = json.dumps(udata, sort_keys=True, indent=4, separators=(',', ': '))
        
        # --------------------------------------------------
        # Save the file
        # --------------------------------------------------
        self.logger.info('Saving data file...')

        # If the path doesn't yet exist, create it
        try:
            if not os.path.isdir(self.path):
                os.makedirs(self.path)
        except:
            self.logger.exception(sys.exc_info()[0])
            raise

        # Create filename from our start time so json and log files match
        filename = self.start_time + ".json"

        # Write the file
        self.logger.info('Saving scraped file...')
        with open('%s/%s'%(self.path, filename), 'w') as f:
            f.write(new_file)


    def load(self):
        if self.error:
            return
        # --------------------------------------------------
        # Send to processing for db upload
        # For now we still have our udata which we can send for uploading.
        # --------------------------------------------------
        self.logger.info('Uploading to database...')
        try:
            upload = Upload()
            upload.upload(udata)
        except:
            self.logger.exception(sys.exc_info()[0])
            raise
        
        
            

