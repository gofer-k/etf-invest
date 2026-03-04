import csv

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
          UNIQUE(meta_id, date),
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
      
  def _build_header_mapping(self, csv_path: str):
    header_mapping = {}
    with open(csv_path, 'r', newline='', encoding='utf-8-sig') as f:
      reader = csv.reader(f)
      rows = list(reader)      
      if len(rows) == 1:
        raise ValueError("Now to supported header format")

      input_header = rows[0]
      # Process each row
      for item in input_header:
        item_norm = item.strip().lower()
        if item_norm in ("data", "date"):
            header_mapping[item] = "date"
        elif item_norm in ("otwarcie", "open"):
            header_mapping[item] = "open"
        elif item_norm in ("max", "max.", "high"):
            header_mapping[item] = "high"
        elif item_norm in ("min", "min.", "low"):
            header_mapping[item] = "low"
        elif item_norm in ("ostatnio", "closed", "close", "last"):
            header_mapping[item] = "close"
        elif item_norm in ("wol.", "wolumen", "volume"):
            header_mapping[item] = "volume"

    if len(header_mapping) != 6:
      ValueError("Error: Unrecognized header format")          

    return header_mapping    

  def _ignore_duplicates(self, csv_path: str, ticket_id: int, timestamp_format: str, mapping_header: dict):
    values_items = list(mapping_header.items())[1:]
    cols_sql = ",\n            ".join([
      f"parse_suffix(REPLACE(\"{csv_col}\", ',', '')) AS {db_col}" 
      for csv_col, db_col in values_items
    ])

    csv_types = {f"'{col}'": "VARCHAR" for col in mapping_header}
                #  ["Data", "Ostatnio", "Otwarcie", "Max.", "Min.", "Wol.", "Zmiana%"]}
    types_str = ", ".join([f"{k}: {v}" for k, v in csv_types.items()])
    return f"""
      INSERT OR IGNORE INTO {self.table_price_name} (id, meta_id, date, close, open, high, low, volume)
      SELECT           
          nextval('{self.price_sequence}') AS id,
          {ticket_id} AS meta_id, 
          STRPTIME("Data"::VARCHAR, '{timestamp_format}') AS date,
          {cols_sql}
      FROM read_csv_auto(
          '{csv_path}', 
          HEADER=TRUE, 
          IGNORE_ERRORS=TRUE,
          types={{{types_str}}}
      )
      """
    
  def _replace_records(self, csv_path: str, ticket_id: int, timestamp_format: str, mapping_header: dict):
    cols_sql = ",\n            ".join([
      f"parse_suffix(REPLACE(\"{csv_col}\", ',', '')) AS {db_col}" 
      for csv_col, db_col in mapping_header.items()
    ])

    csv_types = {f"'{col}'": "VARCHAR" for col in ["Data", "Ostatnio", "Otwarcie", "Max.", "Min.", "Wol.", "Zmiana%"]}
    types_str = ", ".join([f"{k}: {v}" for k, v in csv_types.items()])
    return """
      INSERT OR REPLACE INTO {self.table_price_name} (id, meta_id, date, close, open, high, low, volume)
      SELECT           
          nextval('{self.price_sequence}') AS id,
          {ticket_id} AS meta_id, 
          STRPTIME(date::VARCHAR, '{timestamp_format}') AS date,
          {cols_sql}          
      FROM read_csv_auto(
          '{csv_path}', 
          HEADER=TRUE, 
          IGNORE_ERRORS=TRUE,
          types={{{types_str}}}
      )
      """ 
    
  def import_ohlcv_csv(self, db_path: str, csv_path: str, symbol: str, timestamp_format: str = "%d.%m.%Y", isToClose = False):    
    """
      Importuje dane OHLCV z pliku CSV do DuckDB.

      Parametry:
        db_path (str): ścieżka do pliku DuckDB (.duckdb)
        csv_path (str): ścieżka do pliku CSV
        timestamp_format (str): format timestampu (np. '%Y-%m-%d %H:%M:%S' lub 'auto')        
    """   
    ticket_id = self._add_symbol(symbol)
    mapping = self._build_header_mapping(csv_path)
    self.con.create_function("parse_suffix", parse_suffix, parameters=[VARCHAR], return_type=FLOAT)     
    query = self._ignore_duplicates(csv_path, ticket_id, timestamp_format, mapping)
    self.con.execute(query)

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


  def stat(self, isToClose=False):
      self.open()
      try:
        for table in [self.table_meta_name, self.table_price_name]:
          print(f"\n{'='*20} {table.upper()} STATS {'='*20}")
          
          # 1. Row Count & Storage info
          res = self.con.execute(f"SELECT COUNT(*) as total_rows FROM {table}").fetchone()
          print(f"Total rows: {res[0]}")
          
          # 2. Advanced Column Statistics (DuckDB specific)
          # Funkcja SUMMARIZE zwraca: min, max, avg, std, null_percentage itp.
          print("\nColumn Detailed Stats:")
          print(self.con.execute(f"SUMMARIZE {table}").fetchdf())
          
          # 3. Schema info (Typy danych i klucze)
          print("\nSchema Info:")
          print(self.con.execute(f"""
              SELECT column_name, data_type, is_nullable, column_default
              FROM information_schema.columns
              WHERE table_name = '{table}'
              ORDER BY ordinal_position;
          """).fetchdf())      
      except Exception as e:
        print(f"Error gathering stats: {e}")
      finally:
        if isToClose:
          self.close()