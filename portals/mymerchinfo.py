"""
Global Payments Inc. Scraper
"""

import os
import sys
import re
import spynner
from StringIO import StringIO
from portal import Portal

class Mymerchinfo(Portal):
    """
    Handles scraping of this site.
    
    Required params:
      path
      uid
      pwd
      portal
      max_records
    
    """
    # ----------------------------------------------------------------------
    # Mimic this user agent for this website.
    # ----------------------------------------------------------------------
    _user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.43 Safari/537.31"

    # ----------------------------------------------------------------------
    # Login Page for this scraper's site
    # ----------------------------------------------------------------------
    _login_page = 'https://mymerchinfo.com/eradmin/'

    # ----------------------------------------------------------------------
    # This is the column lookup of what we want to go into scraper table,
    # i.e., the data we're looking for from the scraped data.
    # This maps the scrape table field name  to Column Headings
    #  of the scraped data.
    # ----------------------------------------------------------------------
    _col_lookup = {'date_received':'Date Received',
                   'transaction_date':'Transaction Date',
                   'card_number':'Card Number',
                   # This scraper doesn't have card type, but we need the placeholder.
                   'card_type':'Card Type',
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
        

    def scrape(self):
        """
        This function should be the only one that changes between scrapers
        """
        
        # Instantiate the virtual browser
        try:
            browser = spynner.Browser(debug_level = spynner.DEBUG, 
                                      debug_stream = StringIO(),
                                      user_agent = self._user_agent)
        except:
            self.logger.exception(sys.exc_info()[0])
            raise sys.exc_info()[0]

        # ----------------------------------------------------------------------
        # If we are running on my mac, we can watch the scraping.
        # NOTE: There was quite a set up process to get it configured to do this.
        #       Revisit possibility of creating a setup script to configure Macs.
        # 
        # The server doesn't support browser visibility.
        # ----------------------------------------------------------------------
        if True:
            browser.create_webview()
            browser.show()
        
        # Load login page
        self.logger.info('Loading site login page...')
        
        def wait_load(self):
            return "Don't have a login?" in browser.html

        # Wait for login page
        self.logger.info('Try loading login page...')
        browser.load(self._login_page, 2, wait_callback=wait_load)
        browser.load_jquery(True)
        
        self.logger.info('Login page loaded...')
        self.logger.info('Setting login form fields...')
        browser.fill('input[name=username]', self.uid)
        browser.fill('input[name=password]', self.pwd)

        self.logger.info('Attempting login...')
        browser.click('input[value=Login]', wait_load=True)
        browser.wait(1)
        
        # Make sure the login was successful
        if 'Username and password combination is invalid.' in browser.html:
            self.logger.error('INCORRECT USER ID AND/OR PASSWORD!')
            raise (Exception, 'Incorrect User ID and/or password.  Cannot continue scrape.')
        
        self.logger.info('Login successsful...')
        self.logger.info('Loading Navigation page...')
        nextUrl = 'https://mymerchinfo.com/eradmin/showGaaLanding.do?reportType=GA'
        
        def wait_load(self):
            return 'For support please call:' in browser.html
        
        browser.load(nextUrl, 2, wait_callback=wait_load)
        
        # New page load jquery again
        # from here on out we'll will deal with the iframe
        browser.load_jquery(True)

        self.logger.info('Loading chargeback search form page...')
        browser.runjs("navigate('1_5_reportMenuDiv',2);")
        browser.wait(20)
        
        # TODO: Make sure that we have our search form page, otherwise, raise another exception.
        n = browser.runjs('$("input[name=MAX_RECORDS]", window.parent.frames[0].document).length;')
        if n == 0:
            self.logger.debug('Form did not load in time...')
            return
        
        
        # Set the query params
        self.logger.info('Setting chargeback search form parameters...')
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
        self.logger.info('Running chargeback query...')
        
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
            self.logger.info('Search parameters did not yield any results. Exiting.')
            self.error = True
            browser.close()
            return
        
        scraped_html = browser.runjs("$('td#ReportTD table tbody', window.parent.frames[0].document).html()")
        scraped_html = scraped_html.toString()
            
        self.logger.info('Records retrieved...')

        # ----------------------------------------------------------------------
        # Scrape the data
        # ----------------------------------------------------------------------
        self.logger.info('Saving scraped HTML...')

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

        # --------------------------------------------------
        # Convert data to a format that easy to manipulate, 
        # in this case, make tab delimited.
        # First, get rid of all new lines
        # --------------------------------------------------
        self.logger.info('Converting to TAB delimited data...')
        new_file = re.sub(r'\n|\r|\t', '', new_file)
        # Next, turn </tr> tags to \n
        new_file = re.sub(r'</tr>', r'\n', new_file)
        # Next, turn </td> in comma space
        new_file = re.sub(r'</td>', r'\t', new_file)
        # Next, remove any remaining tags
        new_file = re.sub(r'<[^>]*>', '', new_file)
        # Next, remove any remaining tags
        new_file = re.sub(r'&nbsp;', '', new_file)

        # --------------------------------------------------
        # Get the FIRST LINE and parse into FIELD NAMES
        # The first line contains the Fields
        # --------------------------------------------------
        first_line = new_file.split('\n', 1)[0]
        fields = first_line.split('\t')

        # --------------------------------------------------
        # This section de-duplicates the field names 
        # and appends with a number if they are duplicated.
        # 
        # We need to do this before making our dictionary 
        # (Python dictionary key values need to be unique)
        # --------------------------------------------------
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
        # the fields we need. (_col_lookup)
        # --------------------------------------------------
        self.logger.info('Extracting fields...')

        adata = []
        
        for line in new_file.split('\n'):
            d = dict(zip(fields, line.split('\t')))
            
            # --------------------------------------------------
            # Concatenate all the message fields on to the first one
            # --------------------------------------------------
            try:
                d['Message'] = '%s %s %s %s' % (d['Message'], d['Message 1'], d['Message 2'], d['Message 3'])
            except:
                # on the rows where we don't have the message fields, just pass.
                pass
                
            adata.append(d)
        
        # We can probably strip off the first row (column names)
        adata = adata[1:]
        # Strip off the last 3 non-record rows
        adata = adata[:-3]
        
        # The data is now clean.  We have all our rows and columns from the scraped
        # data and we can now transform it to just the data we need. 
        # Set data for transform function
        self.adata = adata
        
        