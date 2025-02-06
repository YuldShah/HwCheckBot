from loader import db

def show_tables():
    """Displays all tables in the database."""
    tables = db.get_tables()
    if tables:
        print("\nAvailable tables:")
        for table in tables:
            print(f" - {table}")
    else:
        print("No tables found in the database.")

def show_last_rows():
    """Shows the last N rows of a given table."""
    table = input("\nEnter table name: ").strip()
    n = input("Enter number of last rows to fetch: ").strip()

    if not n.isdigit():
        print("Error: Please enter a valid number.")
        return
    
    n = int(n)
    rows = db.get_last_n_rows(table, n)

    if isinstance(rows, str):  # Error message from SQL
        print(rows)
    elif rows:
        print(f"\nLast {n} rows from '{table}':")
        for row in rows:
            print(row)
    else:
        print(f"No records found in table '{table}'.")

def main():
    while True:
        print("\nDatabase Viewer Menu")
        print("1. Show tables")
        print("2. Show last N rows from a table")
        print("3. Exit")

        choice = input("\nChoose an option: ").strip()

        if choice == "1":
            show_tables()
        elif choice == "2":
            show_last_rows()
        elif choice == "3":
            print("Exiting...")
            break
        else:
            print("Invalid option. Please choose again.")

if __name__ == "__main__":
    main()
