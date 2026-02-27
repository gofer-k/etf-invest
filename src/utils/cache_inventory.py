import duckdb
from duckdb.sqltypes import DOUBLE, FLOAT, VARCHAR, DuckDBPyType

def parse_suffix(x: str):
  if x is None:
    return None
  x = str(x).strip().upper()
  if x.endswith("K"):
    return float(x[:-1]) * 1e3
  if x.endswith("M"):
    return float(x[:-1]) * 1e6
  if x.endswith("B"):
      return float(x[:-1]) * 1e9
  return float(x)

class CacheInventory:
    def __init__(self, db_path: str = ":memory:"):
      self.db_path = db_path
      self.table_price_name = "price"
      self.table_meta_name = "metadata"      
      self.meta_sequence = self._sequence_name(self.table_meta_name)
      self.price_sequence = self._sequence_name(self.table_price_name)
      self.open()
      self._init_db()        
        
    def _init_db(self,isToClose = False):   
        resutt = self.con.execute(
          f""" 
          CREATE TABLE IF NOT EXISTS {self.table_meta_name} (
            id INTEGER PRIMARY KEY DEFAULT nextval('{self.meta_sequence}'),
            symbol TEXT NOT NULL,
            exchange VARCHAR,
            currency VARCHAR,
            UNIQUE(id, symbol));
          """)
        result = self.con.execute(
          f""" 
          CREATE TABLE IF NOT EXISTS {self.table_price_name} (
            id INTEGER PRIMARY KEY DEFAULT nextval('{self.price_sequence}'),
            meta_id INTEGER NOT NULL,            
            date TIMESTAMP NOT NULL,
            open FLOAT,
            high FLOAT,
            low FLOAT,
            close FLOAT,
            volume FLOAT,
            UNIQUE(id, date),
            FOREIGN KEY (meta_id) REFERENCES {self.table_meta_name}(id)
          );
          """)
        if isToClose:
           self.close()

    def _add_symbol(self, symbol: str, isToClose = False):   
      row = self.con.execute(f"SELECT id FROM {self.table_meta_name} WHERE symbol = ?", [symbol]).fetchone()
      if row is None:
        row = self.con.execute(f"INSERT INTO {self.table_meta_name} (id, symbol) VALUES (nextval('{self.meta_sequence}'), ?)", [symbol]).fetchone()
        
      id_value = row[0]
   
      if isToClose:
        self.close()
      return id_value
      

    def import_from_csv(self, db_path: str, csv_path: str, symbol: str, timestamp_format: str = "%m/%d/%Y", isToClose = False):
      """
        Importuje dane OHLCV z pliku CSV do DuckDB.

        Parametry:
          db_path (str): ścieżka do pliku DuckDB (.duckdb)
          csv_path (str): ścieżka do pliku CSV
          timestamp_format (str): format timestampu (np. '%Y-%m-%d %H:%M:%S' lub 'auto')        
      """   
      ticket_id = self._add_symbol(symbol)
      self.con.create_function("parse_suffix", parse_suffix, parameters=[VARCHAR], return_type=FLOAT)     
      # epoch(STRPTIME(date::VARCHAR, '{timestamp_format}'))::INTEGER AS date,
      self.con.execute(
        f""" 
        INSERT INTO {self.table_price_name} 
        SELECT           
            nextval('{self.price_sequence}') AS id,
            {ticket_id} AS meta_id, 
            STRPTIME(date::VARCHAR, '{timestamp_format}') AS date,
            parse_suffix(REPLACE(open, ',', '')) AS open,
            parse_suffix(REPLACE(high, ',', '')) AS high,
            parse_suffix(REPLACE(low, ',', '')) AS low,
            parse_suffix(REPLACE(close, ',', '')) AS close,
            parse_suffix(REPLACE(volume, ',', '')) AS volume            
        FROM read_csv_auto(
            '{csv_path}', 
            HEADER=TRUE, 
            IGNORE_ERRORS=TRUE,
            types={{'date': 'VaRCHAR', 'open': 'VARCHAR', 'high': 'VARCHAR', 'low': 'VARCHAR', 'close': 'VARCHAR', 'volume': 'VARCHAR'}}
        )        
        """
      )

      if isToClose:
        self.close()

    
    def open(self):
       self.con = duckdb.connect(self.db_path)
       self._create_sequence(self.price_sequence)
       self._create_sequence(self.meta_sequence)

    def _sequence_name(self, name: str):
       return f"{name}_id_sequence"

    def _create_sequence(self, table_name: str):
      # DuckDB handles the check internally
      self.con.execute(f"CREATE SEQUENCE IF NOT EXISTS {table_name} START 1;")   

    def close(self):
      if self.con is not None:
        self.con.close()
        self.con = None


    def stat(self, isToClose = False):
      self.open()
      for table in [self.table_price_name, self.table_meta_name]:
        print("----{table} table stats:\nrow count:")
        print(self.con.execute(f"SELECT COUNT(*) FROM {table};").fetchone()[0])
        print("\nColumn stats:")
        print(self.con.execute(
            f"""
            SELECT column_name, data_type, FROM duckdb_columns()
            WHERE table_name = '{table}';
            """).fetchdf())
        print("\nStorage stats:")
        print(self.con.execute(f"""SELECT COUNT(*) FROM {table};""").fetchdf())
       
      if isToClose: 
        self.close()

    def get(self, key):
        return self.cache.get(key)

    def set(self, key, value):
        self.cache[key] = value

    def clear(self):
        self.cache.clear()