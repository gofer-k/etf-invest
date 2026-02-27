import argparse

from src.utils.cache_inventory import CacheInventory
from src.utils.paths import OUTPUT_DIR

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ETF AI Agent CLI")
    parser.add_argument("--input_file", type=str, help="Importing file")
    parser.add_argument("--ticket", type=str, help="Ticket (symbol) name")
    return parser.parse_args()

def import_data() -> None:
    args = parse_args()
    if not args.input_file:
        raise ValueError("Input file CSV is required. Please provide it using --input_file argument.")
    if not args.ticket:
        raise ValueError("Ticket (symbol) name is required. Please provide it using --ticket argument.")
    
    db_path = OUTPUT_DIR / f"cache.db"
    cache = CacheInventory(db_path)
    cache.import_from_csv(db_path, args.input_file, args.ticket)
    cache.stat(isToClose=True)

if __name__ == "__main__":
    import_data()