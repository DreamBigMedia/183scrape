"""
Global Payments Inc. Scraper
"""

import os
import sys
import time
import glob
import logging
import re
import time
import json
from StringIO import StringIO
import spynner
from portal import Portal
from db.upload import Upload

logging.basicConfig(filename='/var/log/scraper/watcher.log', level=logging.DEBUG)

class Mymerchinfo(Portal):
    """
    Handles scraping of this site.
    """
    
    # ----------------------------------------------------------------------
    # This is the column lookup of what we want to go into scraper table,
    # i.e., the data we're looking for from the scraped data.
    # This maps the scrape table field name  to Column Headings
    #  of the scraped data.
    # ----------------------------------------------------------------------
    _col_lookup = {'date_received':'Date Received',
                   'transaction_date':'Transaction Date',
                   'card_number':'Card Number',
                   'amount':'Amount',
                   'case_number':'Case Number',
                   'merchant_id':'Merchant #',
                   'messages':'Message'}
    
    @classmethod
    def is_scraper_for(cls, portal):
        """
        Factory checks to see if this is the correct portal scraper to return.
        If we want mymerchinfo, this is the right scraper!
        """
        return portal == 'global_payments'

    def setup(self, **params):
        """
        This initializes the class with all the parameters 
        it will need to scrape the site.
        """

        # Turn all the incoming kwargs to class variables
        params = params['params']
        for k, v in params.iteritems():
            setattr(self, k, v)
        
        # Login Page for this site
        self.login_page = 'https://mymerchinfo.com/eradmin/'

        # If max not specified, set to lots or records returned
        try:
            if not self.max_records > 0:
                self.max_records = 100
        except:
            logging.exception(sys.exc_info()[0])


    def run(self):
        """
        This function starts the scraping process...
        """

        logging.info('Starting scrape...')
        
        # Instantiate the virtual browser
        debug_stream = StringIO()
        user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.43 Safari/537.31"

        try:
            browser = spynner.Browser(debug_level = spynner.DEBUG, 
                                      debug_stream = debug_stream,
                                      user_agent = user_agent)
        except:
            logging.exception(sys.exc_info()[0])
            raise sys.exc_info()[0]

        # ----------------------------------------------------------------------
        # If we are running on my mac, we can watch the scraping.
        # NOTE: There was quite a set up process to get it configured to do this.
        #       Revisit possibility of creating a setup script to configure Macs.
        # 
        # The server doesn't support browser visibility.
        # ----------------------------------------------------------------------

        browser.create_webview()
        browser.show()

        # Load login page
        logging.info('Loading site login page...')
        
        def wait_load(self):
            return "Don't have a login?" in browser.html

        # Wait for login page
        logging.info('Try loading login page...')
        browser.load(self.login_page, 2, wait_callback=wait_load)
        browser.load_jquery(True)
        
        logging.info('Login page loaded...')
        logging.info('Setting login form fields...')
        browser.fill('input[name=username]', self.uid)
        browser.fill('input[name=password]', self.pwd)

        logging.info('Attempting login...')
        browser.click('input[value=Login]', wait_load=True)
        browser.wait(1)
        
        # Make sure the login was successful
        if 'Username and password combination is invalid.' in browser.html:
            logging.error('INCORRECT USER ID AND/OR PASSWORD!')
            raise (Exception, 'Incorrect User ID and/or password.  Cannot continue scrape.')
        
        logging.info('Login successsful...')
        logging.info('Loading Navigation page...')
        nextUrl = 'https://mymerchinfo.com/eradmin/showGaaLanding.do?reportType=GA'
        
        def wait_load(self):
            return 'For support please call:' in browser.html
        
        browser.load(nextUrl, 2, wait_callback=wait_load)
        
        # New page load jquery again
        # from here on out we'll will deal with the iframe
        browser.load_jquery(True)

        logging.info('Loading chargeback search form page...')
        browser.runjs("navigate('1_5_reportMenuDiv',2);")
        browser.wait(20)
        
        # TODO: Make sure that we have our search form page, otherwise, raise another exception.
        n = browser.runjs('$("input[name=MAX_RECORDS]", window.parent.frames[0].document).length;')
        if n == 0:
            logging.debug('Form did not load in time...')
            return
        
        
        # Set the query params
        logging.info('Setting chargeback search form parameters...')
        # Set the max_records field
        js = '$("input[name=MAX_RECORDS]", window.parent.frames[0].document).val("%s");' % self.max_records
        browser.runjs(js)
        
        # Set the date search type to BETWEEN
        js = '$("#RESOLVED_DATE_OP", window.parent.frames[0].document).val("BETWEEN");'
        browser.runjs(js)

        # Set the start_date field
        js = '$("#RESOLVED_DATE", window.parent.frames[0].document).val("%s");' % self.start_date
        browser.runjs(js)
        
        # Set the start_date field
        js = '$("#RESOLVED_DATE_END", window.parent.frames[0].document).val("%s");' % self.end_date
        browser.runjs(js)

        # Click the submit button
        logging.info('Running chargeback query...')
        
        # All we can do is run the query and wait some time.  
        # Callbacks are not supported on runjs function, unfortunately.
        #clickSubmit = 'var alink = $("a").filter(function(index) { return $(this).text() === "Submit"; }); alert(alink.href); alink.trigger("click");'
        clickSubmit = '$("form", window.parent.frames[0].document).trigger("submit");'
        browser.runjs(clickSubmit)
        # currently we wait 30 seconds plus one second for each 5 max_records
        browser.wait(60*1)
#        browser.wait(30 + int(self.max_records) * .2)
        
        # TODO: Here, we want to check the page until we have the return data, 
        # so we don't have to use a timer.
        n = browser.runjs("$('td#ReportTD table tbody', window.parent.frames[0].document).length")
        if n == 0:
            logging.info('Search parameters did not yield any results.')
            return
        
        scraped_html = browser.runjs("$('td#ReportTD table tbody', window.parent.frames[0].document).html()")
        scraped_html = scraped_html.toString()
            
        logging.info('Records retrieved...')

        # ----------------------------------------------------------------------
        # Scrape the data
        # ----------------------------------------------------------------------
        logging.info('Saving scraped HTML...')

        # Save the original scrape data
        try:
            with open('/temp/temp.html', 'w') as f:
                f.write(scraped_html)
        except:
            logger.error(sys.exc_info()[0])


        # Now that we've scraped and have all the data we need, 
        # we can close the browser.
        browser.close()

        # --------------------------------------------------
        # Because the buffer contains a couple of undesired
        # read from file we just saved.  This will ensure
        # we have good string to perform our regex on.
        # --------------------------------------------------
        try:
            with open('/temp/temp.html', 'r') as f:
                new_file = f.read()
        except:
            logger.error(sys.exc_info()[0])

        logging.info('Converting to TAB delimited data...')
        # Convert to CSV
        # First, get rid of all new lines
        new_file = re.sub(r'\n|\r|\t', '', new_file)
        # Next, turn </tr> tags to \n
        new_file = re.sub(r'</tr>', r'\n', new_file)
        # Next, turn </td> in comma space
        new_file = re.sub(r'</td>', r'\t', new_file)
        # Next, remove any remaining tags
        new_file = re.sub(r'<[^>]*>', '', new_file)
        # Next, remove any remaining tags
        new_file = re.sub(r'&nbsp;', '', new_file)

        # Get the FIRST LINE and parse into FIELD NAMES
        # The first line contains the Fields
        first_line = new_file.split('\n', 1)[0]
        fields = first_line.split('\t')

        # This section de-duplicates the field names 
        # and appends with a number if they are duplicated.
        # 
        # We need to do this before making our dictionary 
        # (which require unique names)
        clean = []
        track = {}
        for f in fields:
            if f in clean:
                if f in track:
                    track[f] += 1
                else:
                    track[f] = 1

                f = "%s %d" % (f, track[f])

            clean.append(f)

        # Reset fields to clean
        fields = []
        fields = clean

        # --------------------------------------------------
        # Now that we have our data, we can extract just 
        # the fields we need.
        # Date Received, Transaction Date, Card Number, Amount, Case Number, Merchant #, and messages
        # --------------------------------------------------
        logging.info('Extracting fields...')

        data = []

        for line in new_file.split('\n'):
            d = dict(zip(fields, line.split('\t')))
            data.append(d)

        # Strip off the last 3 non-record rows
        data = data[:-3]

        # --------------------------------------------------
        # Trim down the data to only the fields we're looking for
        # And replace with canonical scraper table column name
        # --------------------------------------------------
        req_rows = []

        for rec in data:
            d = {}
            
            for k, v in self._col_lookup.iteritems():
                if rec.has_key(v):
                    d[k] = rec[v]
                else:
                    d[k] = ''
                
            req_rows.append(d)
        
        # --------------------------------------------------
        # Before saving the file we can either pickle the data
        # or turn it into JSON
        # --------------------------------------------------
        logging.info('Converting to JSON...')
        new_file = json.dumps(req_rows, sort_keys=True, indent=4, separators=(',', ': '))
        
        # --------------------------------------------------
        # Save the file
        # --------------------------------------------------
        logging.info('Saving data file...')

        # Split the file parts
        # path, filename = os.path.split(self.path)

        #remove the slashes
        path = re.sub(r'\\', '', self.path)

        logging.debug('path: ' + path)
        # If the path doesn't yet exist, create it
        # if not os.path.isfile(path):
        #     os.makedirs(path)

        # Get the time
        filename = time.strftime("%Y%m%d-%I:%M:%S") + ".json"

        # Write the file
        logging.info('Saving scraped file...')
        with open('%s/%s'%(path, filename), 'w') as f:
            f.write(new_file)

        # --------------------------------------------------
        # Send to processing for db upload
        # For now we still have our req_rows which we can send for uploading.
        # --------------------------------------------------
        logging.info('Uploading to database...')
        upload = Upload()
        upload.upload(req_rows)
        
        logging.info('----- DONE -----')

        
        
        
        
        
        
        
        
        




