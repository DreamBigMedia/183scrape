#!/usr/bin/python
# ----------------------------------------------------------------------
# My Merchant Info Scraper
#
# ----------------------------------------------------------------------

import os
import sys
import re
import logging
import time
import spynner
import argparse
from StringIO import StringIO

logging.basicConfig(filename='/var/log/scraper/scraper.log', level=logging.DEBUG)

class Scraper:
    def __init__(self):

        # Config
        self.debug_stream = StringIO()
        #bp = os.path.dirname(spynner.tests.__file__)
        # User Agent
        self.user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.43 Safari/537.31"
        
        # Login Page
        self.login_page = 'https://mymerchinfo.com/eradmin/'

        # Set up parser to handle CLI args
        parser = argparse.ArgumentParser(description='This module scrapes data from ' + self.login_page)
        parser.add_argument('--uid', dest='uid', help='Account login for site')
        parser.add_argument('--pwd', dest='pwd', help='Account password for site')
        parser.add_argument('--start_date', dest='start_date', help='Specifies start date in format d/m/Y')
        parser.add_argument('--end_date', dest='end_date', help='Specifies end date in format d/m/Y')
        parser.add_argument('--max_records', dest='max_records', help='The maximum number of records retrieved for dates requested.  To return ALL records, don\'t use this argument or set it to 0.')
        parser.add_argument('--path', dest='path', help='The path where the scrape file will be written to.')
        parser.add_argument('--osx', dest='osx', help='If running on OSX, you can watch the scraping in action if the OS has been configured to do so.')
        self.args = parser.parse_args()

        # If max not specified, set to lots
        if not self.args.max_records > 0:
            self.args.max_records = 10000;


    def run(self):
        """
        This function starts the scraping process...
        """

        logging.info('Starting...')
        
        # Instantiate the virtual browser
        browser = spynner.Browser(debug_level=spynner.DEBUG, 
                                  debug_stream=self.debug_stream, 
                                  user_agent=self.user_agent)

        browser.debug_level = spynner.DEBUG

        # If we are running on my mac, we can watch the scraping.
        # NOTE: There was quite a set up process to get it configured to do this.
        #       Revisit possibility of creating a setup script to configure Macs.
        # 
        # The server doesn't support browser visibility.
        if self.args.osx == 1:
            browser.create_webview()
            browser.show()

        # Load login page
        logging.info('Loading site login page...')
        browser.load(self.login_page)
        browser.load_jquery(True)

        logging.info('Setting login form fields...')
        browser.fill('input[name=username]', self.args.uid)
        browser.fill('input[name=password]', self.args.pwd)

        logging.info('Attempting login...')
        browser.click('input[value=Login]', wait_load=True) #, wait_load=True

        logging.info('Login successsful...')

        logging.info('Loading next page...')
        nextUrl = 'https://mymerchinfo.com/eradmin/showGaaLanding.do?reportType=GA'
        browser.load(nextUrl)

        browser.wait(4)

        logging.info('Loading chargeback search form page...')
        browser.runjs("navigate('1_5_reportMenuDiv',2);")
        browser.wait_load()
        browser.load_jquery(True)

        # Set the query params
        logging.info('Setting chargeback search form parameters...')
        # Set the max_records field
        js = '$("input[name=MAX_RECORDS]", window.parent.frames[0].document).val("%s");' % self.args.max_records
        browser.runjs(js)
        
        # Set the date search type to BETWEEN
        js = '$("#RESOLVED_DATE_OP", window.parent.frames[0].document).val("BETWEEN");'
        browser.runjs(js)

        # Set the start_date field
        js = '$("#RESOLVED_DATE", window.parent.frames[0].document).val("%s");' % self.args.start_date
        browser.runjs(js)
        
        # Set the start_date field
        js = '$("#RESOLVED_DATE_END", window.parent.frames[0].document).val("%s");' % self.args.end_date
        browser.runjs(js)

        # Click the submit button
        logging.info('Running chargeback query...')
        #clickSubmit = 'var alink = $("a").filter(function(index) { return $(this).text() === "Submit"; }); alert(alink.href); alink.trigger("click");'
        clickSubmit = '$("form", window.parent.frames[0].document).trigger("submit");'
        browser.runjs(clickSubmit)

        # TODO: Here, we want to check the page until we have the return data, so we don't
        # have to use a timer.

        browser.wait(40)
        logging.info('Records retrieved...')

        # ----------------------------------------------------------------------
        # Scrape the data
        # ----------------------------------------------------------------------
        logging.info('Scraping...')

        # Get our html.
        scraped_html = browser.runjs("$('td#ReportTD table tbody', window.parent.frames[0].document).html()")
        scraped_html = scraped_html.toString()

        logging.info('Saving scraped HTML...')
        # Save the original scrape data
        try:
            with open('/tmp/temp.html', 'w') as f:
                f.write(scraped_html)
        except:
            logger.error(sys.exc_info()[0])

        # Because the buffer contains a couple of undesired
        # read from file we just saved.  This will ensure
        # we have good string to perform our regex on.
        try:
            with open('/tmp/temp.html', 'r') as f:
                new_file = f.read()
        except:
            logger.error(sys.exc_info()[0])

        logging.info('Converting to TAB delimited txt file...')
        # Convert to CSV
        # First, get rid of all new lines
        new_file = re.sub(r'\n|\r|\t', '', new_file)
        # Next, turn </tr> tags to \n
        new_file = re.sub(r'</tr>', r'\n', new_file)
        # Next, turn </td> in comma space
        new_file = re.sub(r'</td>', '\t', new_file)
        # Next, remove any remaining tags
        new_file = re.sub(r'<[^>]*>', '', new_file)
        # Next, remove any remaining tags
        new_file = re.sub(r'&nbsp;', '', new_file)

        logging.info('Saving data file...')

        # Split the file parts
        # path, filename = os.path.split(self.args.path)

        #remove the slashes
        path = re.sub(r'\\', '', self.args.path)

        logging.debug('path: ' + path)
        # If the path doesn't yet exist, create it
        # if not os.path.isfile(path):
        #     os.makedirs(path)

        # Get the time
        filename = time.strftime("%Y%m%d-%I:%M:%S") + ".txt"

        # Write the file
        logging.info('Saving scraped file...')
        with open('%s/%s'%(path, filename), 'w') as f:
            f.write(new_file)

        browser.close()

        logging.info('----- DONE -----')

if __name__ == "__main__":
    
    scraper = Scraper()
    scraper.run()

