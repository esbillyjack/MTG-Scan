"""
import sys
sys.path.append('.')

from backend.database import get_db, Scan

def main():
    try:
        db = next(get_db())
        scan = db.query(Scan).filter(Scan.id == 285).first()
        if scan:
            print("Scan 285 details:")
            print(scan.__dict__)
        else:
            print("No scan with ID 285 found.")
    except Exception as e:
        print(f"Error querying database: {str(e)}")

if __name__ == "__main__":
    main()
""" 