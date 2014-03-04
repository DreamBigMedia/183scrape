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
from daemon import Daemon
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

        # Loop until we have a file to process
        while True:
            # Glob the request directory
            files = glob.glob(self.request_dir)

            # As long as we are processing files, the sleep won't trigger
            for file in files:
                logging.info('Processing: %s...'%file)
                self.process(file)
                logging.info('Deleting: %s...'%file)
                os.unlink(file)

            # Sleep a while before checking the directory again
            time.sleep(10)
    
    def process(self, file):
        """
        This function processes the file based on the file contents
        """

        # Factory for returning class for specific portal
        def Scraper(portal):
            for cls in Portal.__subclasses__():
                if cls.is_scraper_for(portal):
                    return cls(portal)
            raise ValueError

        # Open the request file and load the JSON
        with open(file) as f:
            c = f.read()
        
        params = json.loads(c)

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



