#!/usr/bin/env python

"""
This module creates a daemon that watches for scrape requests via
the PHP AdBoom Admin Tool.

Actions are triggered when a new request lands in the request folder
in the PHP scope.

"""
import os
import sys
import time
import glob
import json
import logging
import re
import time
from datetime import datetime as dt
from datetime import date, timedelta

from daemon import Daemon
import ConfigParser

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from portals.portal import Portal
from portals.mymerchinfo import Mymerchinfo

logging.basicConfig(filename='/var/log/scraper/watcher.log', level=logging.DEBUG)

class Watch(Daemon):

    def run(self):
        """
        Run!
        """
        # Get all the files for processing
        self.request_dir = '/temp/*.request.json'

        # --------------------------------------------------
        # Loop until we have a file to process 
        # OR 
        # when it is time to do our 'early morning' morning scrape
        # which scrapes everything from the last 2 days from every portal and account
        # --------------------------------------------------
        while True:
            
            # --------------------------------------------------
            # TIME CHECK
            # TODO: Put into config file
            # Set to 1 am 
            # --------------------------------------------------
            if dt.now().hour == 1:
                self.processAuto()
            
            # --------------------------------------------------
            # FILE CHECK
            # Glob the request directory
            # --------------------------------------------------
            files = glob.glob(self.request_dir)

            # As long as we are processing files, the sleep won't trigger
            for file in files:
                logging.info('Processing: %s...'%file)
                
                # Open the request file and load the JSON
                with open(file) as f:
                    j = f.read()
        
                params = json.loads(j)

                self.process(params)
                logging.info('Deleting: %s...'%file)
                os.unlink(file)

            # Sleep a while before checking the directory again
            time.sleep(20)
    
    def processAuto(self):
        """
        Select from our database all the portals and active accounts that have scrapers.
        We are going to loop through each account and scrape the last 2 days data.
        """
        # TODO: connect from config file
        conn_str = 'mysql://root:adboom123@localhost/adboomadmin'
        
        # For direct query to db
        engine = create_engine(conn_str)
        self.conn = engine.connect()
        
        sql = 'select * from portals where scraper_active = 1'
        print self.conn.execute(sql).fetchall()
        
        d=date.today()-timedelta(days=2)
        print d
        
        
        
    
    def process(self, **params):
        """
        This function processes a scrape from the passed params
        """

        # Factory for returning class for specific portal
        def Scraper(portal):
            for cls in Portal.__subclasses__():
                if cls.is_scraper_for(portal):
                    return cls(portal)
            raise ValueError

        # Get the scraper
        scraper = Scraper(params['portal'])

        # Setup the scraper with params necessary to scrape the site
        scraper.setup(params = params)

        # Scrape away
        # TODO: Eventually we will want to start the process in a thread
        try:
            scraper.run()
        except:
            logging.exception(sys.exc_info()[0])


if __name__ == '__main__':
    
    pid_dir = os.path.dirname(os.path.realpath(__file__)) + '/pid'
    pid_file = pid_dir + '/watcher.pid'

    if not os.path.exists(pid_dir):
        os.makedirs(pid_dir)

    if os.path.isfile(pid_file):
        os.remove(pid_file)

    watch = Watch(pid_file)
    # Start the daemon
    #watch.start()

    # or, don't start the daemon
    watch.run()



