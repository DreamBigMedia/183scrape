class Table(object):
    def __init__(self, conn, table):
        """
        Sets 
        """
        self.conn = conn
        self.table = table
        self.id = None
        self.columns = []
        
        # Get and set the keys
        sql = "show columns in %s" % self.table
        self.conn.query(sql)
        result = conn.store_result()
        record = result.fetch_row(0, how = 1)
        
        for rec in record:
            self.columns.append(rec['Field'])
            setattr(self, rec['Field'], None)
        
    def load(self, id):
        """
        Loads a single record
        """
        sql = " select * from %s where id = %s " % (self.table, id)
        self.conn.query(sql)
        result = conn.store_result()
        record = result.fetch_row(how = 1)
        
        for k, v in record[0].iteritems():
            setattr(self, k, v)
        
    def save(self):
        """
        Saves data back to table
        """
        vals = []
        sets = []
        for f in self.columns:
            vals.append(getattr(self, f))
            sets.append(" %s=%s ")
        
        if self.id > 0:
            sql = "update %s set ", ", ".join(sets), " where id = %s" % (self.table, self.id) 
        else:
            # sql = "insert into %s (", ", ".join(self.columns) , ") values (", 
            pass
            
        print sql 
        
        
    def delete(self):
        """
        Delete record from the database
        """
        pass

class Portal(Table):
    def __init__(self, conn):
        self.table = 'portals'
        super(self.__class__, self).__init__(conn, self.table)

import MySQLdb

#conn = MySQLdb.connect("mysql.adboom.technology", "hirsh", "adboom123", "scraper")
conn = MySQLdb.connect("localhost", "root", "adboom123", "adboomadmin")

t = Portal(conn)




