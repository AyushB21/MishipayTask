import sqlite3

# Connect to the SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('inventory.db')

# Create Supplier table
conn.execute('''
CREATE TABLE IF NOT EXISTS Supplier (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT NOT NULL UNIQUE,
    address TEXT NOT NULL
);
''')

# Create Product table
conn.execute('''
CREATE TABLE IF NOT EXISTS Product (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    category TEXT NOT NULL,
    price REAL NOT NULL CHECK(price >= 0),
    stock_quantity INTEGER NOT NULL CHECK(stock_quantity >= 0),
    supplier_id INTEGER,
    FOREIGN KEY (supplier_id) REFERENCES Supplier(id)
);
''')

# Create SaleOrder table
conn.execute('''
CREATE TABLE IF NOT EXISTS SaleOrder (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER,
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    total_price REAL NOT NULL CHECK(total_price >= 0),
    sale_date TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('Pending', 'Completed', 'Cancelled')),
    FOREIGN KEY (product_id) REFERENCES Product(id)
);
''')

# Create StockMovement table
conn.execute('''
CREATE TABLE IF NOT EXISTS StockMovement (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER,
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    movement_type TEXT NOT NULL CHECK(movement_type IN ('In', 'Out')),
    movement_date TEXT NOT NULL,
    notes TEXT,
    FOREIGN KEY (product_id) REFERENCES Product(id)
);
''')

# Commit changes and close the connection
conn.commit()
conn.close()
