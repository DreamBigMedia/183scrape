

class DB:
    def __init__(self):
      """
      Configure database
      """



c.executemany(
      """INSERT INTO breakfast (name, spam, eggs, sausage, price)
      VALUES (%s, %s, %s, %s, %s)""",
      [
      ("Spam and Sausage Lover's Plate", 5, 1, 8, 7.95 ),
      ("Not So Much Spam Plate", 3, 2, 0, 3.95 ),
      ("Don't Wany ANY SPAM! Plate", 0, 4, 3, 5.95 )
      ] )

db = MySQLdb.connect("mysql.adboom.technology", "hirsh", "adboom123", "scraper")
>>> db.query("show databases")
>>> r = db.store_results()
r.fetch_row(rows = 0)

db.autocommit(true|false)


class CbmChargebacks:
    def __init__(self):
        self.id = 0
        self.cid = 0
        self.crm_id = 0
        self.upload_id = 0
        self.transaction_date = ''
        self.date_received = ''
        self.upload_date = ''
        self.case_number = ''
        self.card_number = ''
        self.card_type = ''
        self.mid = ''
        self.amount = ''
        self.order_id = 0
        self.completed = 0

    def load(self, id):
        pass