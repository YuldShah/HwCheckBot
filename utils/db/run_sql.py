from loader import db

def run_sql():
    """Allows user to enter and execute SQL commands interactively."""
    while True:
        sql = input("Enter SQL command (or type 'exit' to quit): ").strip()
        if sql.lower() == "exit":
            break
        result = db.execute_sql(sql)
        if isinstance(result, list):  # If SELECT query returns rows
            for row in result:
                print(row)
        else:
            print(result)  # For INSERT, UPDATE, DELETE, etc.

if __name__ == "__main__":
    run_sql()