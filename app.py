from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import re

app = Flask(__name__)

# Path to SQLite database
DB_PATH = 'inventory.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# @app.route('/')
# def index():
#     return render_template('index.html')

@app.route('/')
def index():
    conn = get_db_connection()
    suppliers = conn.execute('SELECT * FROM Supplier').fetchall()  # Fetch all suppliers
    products = conn.execute('SELECT * FROM Product').fetchall()  # Fetch all suppliers
    conn.close()
    print(suppliers)
    return render_template('index.html', suppliers=suppliers, products=products)  # Pass suppliers to the template


@app.route('/product/add', methods=['POST'])
def add_product():
    name = request.form['name']
    description = request.form['description']
    category = request.form['category']
    price = request.form['price']
    stock_quantity = request.form['stock_quantity']
    supplier = request.form['supplier']

    if not name or not description or not category or not price or not stock_quantity:
        return render_template('index.html', message="All fields are required.")
    
    # Validate price and stock quantity
    try:
        price = float(price)
        stock_quantity = int(stock_quantity)
        if price <= 0 or stock_quantity < 0:
            return render_template('index.html', message="Price must be positive and stock quantity can't be negative.")
    except ValueError:
        return render_template('index.html', message="Invalid input for price or stock quantity.")
    
    conn = get_db_connection()
    # Check for duplicate product
    existing_product = conn.execute('SELECT * FROM Product WHERE name = ?', (name,)).fetchone()
    if existing_product:
        return render_template('index.html', message="Product already exists.")
    
    conn.execute('INSERT INTO Product (name, description, category, price, stock_quantity, supplier_id) VALUES (?, ?, ?, ?, ?, ?)',
                 (name, description, category, price, stock_quantity, supplier))
    conn.commit()
    conn.close()

    return render_template('index.html', message="Product added successfully!")

@app.route('/products')
def list_products():
    conn = get_db_connection()
    products = conn.execute('''
        SELECT Product.name, Product.description, Product.price, Product.stock_quantity, Supplier.name AS supplier_name
        FROM Product
        JOIN Supplier ON Product.supplier_id = Supplier.id
    ''').fetchall()
    conn.close()
    return render_template('product_list.html', products=products)


@app.route('/supplier/add', methods=['POST'])
def add_supplier():
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    address = request.form['address']

    # Validate email format
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, email):
        return render_template('index.html', message="Invalid email format.")
    
    # Validate phone number (should be 10 digits)
    if len(phone) != 10 or not phone.isdigit():
        return render_template('index.html', message="Phone number must be 10 digits.")
    
    # Check for duplicate supplier
    conn = get_db_connection()
    existing_supplier = conn.execute('SELECT * FROM Supplier WHERE email = ? OR phone = ?', (email, phone)).fetchone()
    if existing_supplier:
        return render_template('index.html', message="Supplier with this email or phone already exists.")

    conn.execute('INSERT INTO Supplier (name, email, phone, address) VALUES (?, ?, ?, ?)',
                 (name, email, phone, address))
    conn.commit()
    conn.close()

    return render_template('index.html', message="Supplier added successfully!")


@app.route('/suppliers')
def list_suppliers():
    conn = get_db_connection()
    suppliers = conn.execute('SELECT * FROM Supplier').fetchall()
    conn.close()
    return render_template('supplier_list.html', suppliers=suppliers)


@app.route('/saleorder/add', methods=['POST'])
def add_sale_order():
    product_id = request.form['product']
    quantity = request.form['quantity']
    sale_date = request.form['sale_date']
    status = 'Pending'
    
    # Validate quantity
    try:
        quantity = int(quantity)
    except ValueError:
        return render_template('index.html', message="Invalid quantity.")
    
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM Product WHERE id = ?', (product_id,)).fetchone()

    if not product:
        return render_template('index.html', message="Product not found.")
    
    if product['stock_quantity'] < quantity:
        return render_template('index.html', message="Not enough stock available.")
    
    total_price = product['price'] * quantity

    # Create sale order
    conn.execute('INSERT INTO SaleOrder (product_id, quantity, total_price, sale_date, status) VALUES (?, ?, ?, ?, ?)',
                 (product_id, quantity, total_price, sale_date, status))
    conn.execute('UPDATE Product SET stock_quantity = stock_quantity - ? WHERE id = ?', (quantity, product_id))
    conn.commit()
    conn.close()

    return render_template('index.html', message="Sale Order created successfully!")

@app.route('/saleorder/cancel/<int:order_id>', methods=['POST'])
def cancel_sale_order(order_id):
    conn = get_db_connection()
    order = conn.execute('SELECT * FROM SaleOrder WHERE id = ?', (order_id,)).fetchone()

    if not order or order['status'] == 'Cancelled':
        return render_template('index.html', message="Invalid order or already cancelled.")

    conn.execute('UPDATE SaleOrder SET status = "Cancelled" WHERE id = ?', (order_id,))
    conn.execute('UPDATE Product SET stock_quantity = stock_quantity + ? WHERE id = ?', (order['quantity'], order['product_id']))
    conn.commit()
    conn.close()

    return render_template('index.html', message="Sale order cancelled successfully!")


@app.route('/saleorder/complete/<int:order_id>', methods=['POST'])
def complete_sale_order(order_id):
    conn = get_db_connection()
    order = conn.execute('SELECT * FROM SaleOrder WHERE id = ?', (order_id,)).fetchone()

    if not order or order['status'] == 'Completed':
        return render_template('index.html', message="Invalid order or already completed.")

    conn.execute('UPDATE SaleOrder SET status = "Completed" WHERE id = ?', (order_id,))
    conn.execute('UPDATE Product SET stock_quantity = stock_quantity - ? WHERE id = ?', (order['quantity'], order['product_id']))
    conn.commit()
    conn.close()

    return render_template('index.html', message="Sale order completed successfully!")


@app.route('/saleorders')
def list_sale_orders():
    conn = get_db_connection()
    sale_orders = conn.execute('''
        SELECT SaleOrder.id, Product.name, SaleOrder.quantity, SaleOrder.total_price, SaleOrder.sale_date, SaleOrder.status
        FROM SaleOrder
        JOIN Product ON SaleOrder.product_id = Product.id
    ''').fetchall()
    conn.close()
    return render_template('saleorder_list.html', sale_orders=sale_orders)


@app.route('/stock_level')
def stock_level():
    conn = get_db_connection()
    products = conn.execute('SELECT name, stock_quantity FROM Product').fetchall()
    conn.close()
    return render_template('stock_level.html', products=products)


@app.route('/stockmovement/add', methods=['POST'])
def add_stock_movement():
    product_id = request.form['product']
    quantity = request.form['quantity']
    movement_type = request.form['movement_type']
    movement_date = request.form['movement_date']
    notes = request.form['notes']

    # Validate quantity
    try:
        quantity = int(quantity)
        if quantity <= 0:
            return render_template('index.html', message="Quantity must be greater than zero.")
    except ValueError:
        return render_template('index.html', message="Invalid input for quantity.")
    
    # Check stock movement type and adjust stock accordingly
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM Product WHERE id = ?', (product_id,)).fetchone()
    
    if not product:
        return render_template('index.html', message="Product not found.")
    
    if movement_type == 'In':
        conn.execute('UPDATE Product SET stock_quantity = stock_quantity + ? WHERE id = ?', (quantity, product_id))
    elif movement_type == 'Out':
        if product['stock_quantity'] < quantity:
            return render_template('index.html', message="Not enough stock available.")
        conn.execute('UPDATE Product SET stock_quantity = stock_quantity - ? WHERE id = ?', (quantity, product_id))

    conn.execute('INSERT INTO StockMovement (product_id, quantity, movement_type, movement_date, notes) VALUES (?, ?, ?, ?, ?)',
                 (product_id, quantity, movement_type, movement_date, notes))
    conn.commit()
    conn.close()

    return render_template('index.html', message="Stock movement recorded successfully!")


if __name__ == '__main__':
    app.run(debug=True)
