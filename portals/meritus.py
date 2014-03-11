"""
Meritus Payment Scraper
"""

import os
import sys
import re
import math
import spynner
from StringIO import StringIO
from portal import Portal

class Meritus(Portal):
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
    # _user_agent = "Mozilla/5.0 (compatible; ABrowse 0.4; Syllable)"
    _user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.43 Safari/537.31"
    # _user_agent = "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:25.0) Gecko/20100101 Firefox/25.0"
    # _user_agent = "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)"
    # ----------------------------------------------------------------------
    # Login Page for this scraper's site
    # ----------------------------------------------------------------------
    _login_page = 'https://www.merituspayment.com/merchants/frmLogin.aspx'

    # ----------------------------------------------------------------------
    # This is the column lookup of what we want to go into scraper table,
    # i.e., the data we're looking for from the scraped data.
    # This maps the scrape table field name  to Column Headings
    #  of the scraped data.
    # Report DateTrans DateCase NoAuth CodeTrans TypeReasonCB TypeCard NoAmount
    # ----------------------------------------------------------------------
    _col_lookup = {'date_received':'Report Date',
                   'transaction_date':'Trans Date',
                   'card_number':'Card No',
                   # This scraper doesn't have card type, but we need the placeholder.
                   'card_type':'card_type',
                   'amount':'Amount',
                   'case_number':'Case No',
                   'merchant_id':'merchant_id',
                   'messages':'Reason',
                   'reason_code':'CB Type'}
    
    @classmethod
    def is_scraper_for(cls, portal):
        """
        Factory checks to see if this is the correct portal scraper to return.
        """
        return portal == 'meritus'
        

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
            return "Login ID:" in browser.html

        # Wait for login page
        self.logger.info('Try loading login page...')
        browser.load(self._login_page, 2, wait_callback=wait_load)
        browser.load_jquery(True)
        
        self.logger.info('Login page loaded...')
        self.logger.info('Setting login form fields...')
        browser.fill('input[name="ctl00$ContentPlaceHolder1$txtLoginID"]', self.uid)
        browser.fill('input[name="ctl00$ContentPlaceHolder1$txtPassword"]', self.pwd)
        
        self.logger.info('Attempting login...')
        browser.click('input[value="Log In"]', wait_load=True)
        
        # Make sure the login was successful
        if 'Invalid Username/Password.' in browser.html:
            self.logger.error('Incorrect User ID and/or password.  Cannot continue scrape.')
            self.error = True
            return
            # raise (Exception, 'Incorrect User ID and/or password.  Cannot continue scrape.')
        
        self.logger.info('Login successsful...')
        self.logger.info('Loading Summary page...')
        self.logger.info('Loading Chargeback page...')
        
        def wait_load(self):
            return 'CHARGEBACK DETAILS' in browser.html
            
        chargeback_page = "https://www.merituspayment.com/merchants/web/SecureReportForms/frmChargebackDetail.aspx?ct=0&dt=0&rd=0&"
        browser.load(chargeback_page)
        browser.load_jquery(True)

        # TEMP until we get params from DB
        self.date_from = '01/01/2012'
        self.date_to = '3/31/2014'
        
        # Required to add focus and class so it registers values with form is posted
        js = '$("#ContentPlaceHolder1_wdcFromDate").addClass("igte_Focus");'
        browser.runjs(js)
        
        js = '$("#ContentPlaceHolder1_wdcFromDate tbody tr td input").select().addClass("igte_InnerFocus").val("%s").keypress();' % self.date_from
        browser.runjs(js)
        
        browser.select('input[value="Search"]')
        browser.click('input[value="Search"]', wait_load=True)
        
        browser.wait(12)
        # browser.runjs('WebForm_DoPostBackWithOptions(new WebForm_PostBackOptions("ctl00$ContentPlaceHolder1$btnSearch", "", false, "", "frmChargebackDetail.aspx?ct=0&dt=0&rd=0", false, false))')
        browser.load_jquery(True)
        browser.wait(4)
        
        # Make sure there are records...
        if 'No Records Found...' in browser.html:
            self.logger.info('Search parameters did not yield any results. Exiting.')
            self.logger.info('----- DONE -----')
            return
        
        # --------------------------------------------------
        # Get the total number of records so we know how many pages
        # of 100 records per page we are going to scrape.
        # --------------------------------------------------
        num_recs = browser.runjs('$("span#ContentPlaceHolder1_lblRecordCount").html();')
        num_recs = num_recs.toString()
        
        self.logger.debug('num_recs: %s' % num_recs)
        
        pages = int(math.ceil(float(num_recs)/100))
        self.logger.debug('pages: %d' % pages)
        
        # --------------------------------------------------
        # Scrape the data
        # --------------------------------------------------
        browser.runjs('$("#ContentPlaceHolder1_cboPageSize").select().val("%s").change();' % '100')
        browser.wait(8)
        
        html = browser.runjs('$("table#ContentPlaceHolder1_grdCCChargebackDetail").html()').toString()
        
        # Get the rest of our pages
        for p in range(2, pages + 1):
            self.logger.info('Scraping page %d...' % p)
            browser.runjs("__doPostBack('ctl00$ContentPlaceHolder1$grdCCChargebackDetail','Page$%d');" % p)
            browser.wait(6)
            html += browser.runjs('$("table#ContentPlaceHolder1_grdCCChargebackDetail").html()').toString()
        
        # --------------------------------------------------
        # Now that we have all our HTML, let's clean it up...
        # --------------------------------------------------
        self.logger.info('Records retrieved...')
        self.logger.info('Saving scraped HTML...')

        # Save the original scrape data
        try:
            with open('/temp/temp.html', 'w') as f:
                f.write(html)
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
            self.logger.error(sys.exc_info()[0])
        
        # --------------------------------------------------
        # Convert data to a format that easy to manipulate, 
        # in this case, make tab delimited.
        # --------------------------------------------------
        self.logger.info('Converting to TAB delimited data...')
        # Next, turn many spaces to 1 space
        new_file = re.sub(r'(\s+)', ' ', new_file)
        # Get rid of all new lines and tabs
        new_file = re.sub(r'\n|\r|\t', '', new_file)
        # Next, turn </tr> tags to \n
        new_file = re.sub(r'</tr>', r'\n', new_file)
        # Next, turn </td> in comma space
        new_file = re.sub(r'</td>|</th>', r'\t', new_file)
        # Next, remove any remaining tags
        new_file = re.sub(r'<[^>]*>', '', new_file)
        # Next, remove any remaining tags
        new_file = re.sub(r'&nbsp;', '', new_file)
        
        # --------------------------------------------------
        # Get the FIRST LINE and parse into FIELD NAMES
        # The first line contains the Fields.
        # Strip whitespace from field names
        # --------------------------------------------------
        first_line = new_file.split('\n', 1)[0]
        fields = first_line.split('\t')
        
        stripped = []
        for field in fields:
            stripped.append(field.strip())
        
        fields = stripped
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
        
        self.logger.debug(fields)
        
        # --------------------------------------------------
        # Now that we have our data, we can extract just 
        # the fields we need. (_col_lookup)
        # --------------------------------------------------
        self.logger.info('Extracting fields...')

        adata = []
        
        for line in new_file.split('\n'):
            d = dict(zip(fields, line.split('\t')))
            adata.append(d)
        
        print adata
        
        # We can probably strip off the first row (column names)
        adata = adata[1:]
        # Strip off the last 3 non-record rows
#        adata = adata[:-3]
        
        # The data is now clean.  We have all our rows and columns from the scraped
        # data and we can now transform it to just the data we need. 
        # Set data for transform function
        self.adata = adata
        
        