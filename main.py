import flet as ft
import sqlite3
import datetime
import os

# --- DATABASE MANAGER (No changes needed) ---
class DatabaseManager:
    def __init__(self, db_name='mydata.db'):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name, check_same_thread=False)
        self.create_tables()
        self.init_sample_data()

    def _execute(self, query, params=()):
        with sqlite3.connect(self.db_name, check_same_thread=False) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor

    def _rows_to_dicts(self, rows):
        return [dict(row) for row in rows]

    def create_tables(self):
        self._execute('''CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, category TEXT, price REAL NOT NULL, stock INTEGER NOT NULL, supplier TEXT, size TEXT, age_range TEXT, color TEXT, material TEXT, condition TEXT)''')
        self._execute('''CREATE TABLE IF NOT EXISTS customers (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT, phone TEXT, total_purchases REAL DEFAULT 0, baby_name TEXT, baby_age TEXT)''')
        self._execute('''CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT NOT NULL, customer_name TEXT, product_name TEXT, quantity INTEGER, total REAL, size TEXT)''')

    def init_sample_data(self):
        if self._execute('SELECT COUNT(*) FROM products').fetchone()[0] == 0:
            products = [("Baby Onesie Set", "Bodysuits", 24.99, 17, "Baby Comfort Co", "0-3M", "0-3M", "Pink", "Cotton", "New"), ("Infant Sleep Gown", "Sleepwear", 18.99, 2, "Sleepy Baby", "3-6M", "3-6M", "Blue", "Organic Cotton", "New")]
            for p in products: self._execute('INSERT INTO products (name, category, price, stock, supplier, size, age_range, color, material, condition) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', p)
            customers = [("Emma Johnson", "emma.j@email.com", "123-456-7890", 0, "Lily", "3 months"), ("Sarah Williams", "sarah.w@email.com", "098-765-4321", 0, "Max", "8 months")]
            for c in customers: self._execute('INSERT INTO customers (name, email, phone, total_purchases, baby_name, baby_age) VALUES (?, ?, ?, ?, ?, ?)', c)
            self._execute("INSERT INTO sales (date, customer_name, product_name, quantity, total, size) VALUES ('2024-06-10', 'Emma Johnson', 'Baby Onesie Set', 1, 24.99, '0-3M')")
            self._execute('UPDATE customers SET total_purchases = 24.99 WHERE name = "Emma Johnson"')

    def get_all_products(self): return self._rows_to_dicts(self._execute('SELECT * FROM products ORDER BY name').fetchall())
    def get_product_by_id(self, product_id): return dict(self._execute('SELECT * FROM products WHERE id=?', (product_id,)).fetchone() or {})
    def add_product(self, data): self._execute('INSERT INTO products (name, category, price, stock, condition, age_range, size) VALUES (?, ?, ?, ?, ?, ?, ?)', (data['name'], data['category'], data['price'], data['stock'], data['condition'], data['age_range'], data['size']))
    def update_product(self, data): self._execute('UPDATE products SET name=?, category=?, price=?, stock=?, condition=?, age_range=?, size=? WHERE id=?', (data['name'], data['category'], data['price'], data['stock'], data['condition'], data['age_range'], data['size'], data['id']))
    def delete_product(self, product_id): self._execute('DELETE FROM products WHERE id=?', (product_id,))
    def get_all_customers(self): return self._rows_to_dicts(self._execute('SELECT * FROM customers ORDER BY name').fetchall())
    def get_customer_by_id(self, customer_id): return dict(self._execute('SELECT * FROM customers WHERE id=?', (customer_id,)).fetchone() or {})
    def add_customer(self, data): self._execute('INSERT INTO customers (name, email, phone, baby_name, baby_age) VALUES (?, ?, ?, ?, ?)', (data['name'], data['email'], data['phone'], data['baby_name'], data['baby_age']))
    def update_customer(self, data): self._execute('UPDATE customers SET name=?, email=?, phone=?, baby_name=?, baby_age=? WHERE id=?', (data['name'], data['email'], data['phone'], data['baby_name'], data['baby_age'], data['id']))
    def delete_customer(self, customer_id): self._execute('DELETE FROM customers WHERE id=?', (customer_id,))
    def get_all_sales(self): return self._rows_to_dicts(self._execute('SELECT * FROM sales ORDER BY id DESC').fetchall())
    def add_sale(self, sale_data):
        with sqlite3.connect(self.db_name, check_same_thread=False) as conn:
            try:
                cursor = conn.cursor(); cursor.execute('BEGIN TRANSACTION')
                cursor.execute('INSERT INTO sales (date, customer_name, product_name, quantity, total, size) VALUES (?, ?, ?, ?, ?, ?)', (sale_data['date'], sale_data['customer_name'], sale_data['product_name'], sale_data['quantity'], sale_data['total'], sale_data['size']))
                cursor.execute('UPDATE products SET stock = stock - ? WHERE name = ?', (sale_data['quantity'], sale_data['product_name']))
                cursor.execute('UPDATE customers SET total_purchases = total_purchases + ? WHERE name = ?', (sale_data['total'], sale_data['customer_name']))
                conn.commit()
            except sqlite3.Error as e: print(f"Database transaction failed: {e}"); conn.rollback()

# --- FLET APPLICATION ---
def main(page: ft.Page):
    page.title = "Store Management System"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 10
    
    db = DatabaseManager()
    
    def show_error_snackbar(message):
        page.snack_bar = ft.SnackBar(content=ft.Text(message, color=ft.Colors.WHITE), bgcolor=ft.Colors.ERROR)
        page.snack_bar.open = True
        page.update()

    content_area = ft.Column(expand=True, scroll=ft.ScrollMode.ADAPTIVE)

    # ==========================================================
    # FORM BUILDER FUNCTIONS
    # ==========================================================
    def build_product_form(switch_to_list_view, product_id=None):
        is_edit = product_id is not None
        product_data = db.get_product_by_id(product_id) if is_edit else {}
        name_input = ft.TextField(label="Product Name", value=product_data.get('name', ''))
        category_dd = ft.Dropdown(label="Category", options=[ft.dropdown.Option(cat) for cat in ['Bodysuits', 'Sleepwear', 'Outerwear', 'Dresses', 'Accessories']], value=product_data.get('category'))
        age_range_dd = ft.Dropdown(label="Age Range / Size", options=[ft.dropdown.Option(age) for age in ['Newborn', '0-3M', '3-6M', '6-9M', '9-12M', '12-18M', '18-24M', '3A', 'Toddler']], value=product_data.get('age_range'))
        price_input = ft.TextField(label="Price", value=str(product_data.get('price', '')), prefix_text="$", keyboard_type=ft.KeyboardType.NUMBER)
        stock_input = ft.TextField(label="Stock Quantity", value=str(product_data.get('stock', '')), keyboard_type=ft.KeyboardType.NUMBER)
        condition_new = ft.Checkbox(label="New", value=(product_data.get('condition', 'New') == 'New'))
        condition_used = ft.Checkbox(label="Used", value=(product_data.get('condition') == 'Gently Used'))

        def save(e):
            try:
                condition = 'Gently Used' if condition_used.value else 'New'
                new_data = {'name': name_input.value, 'category': category_dd.value, 'price': float(price_input.value), 'stock': int(stock_input.value), 'condition': condition, 'age_range': age_range_dd.value, 'size': age_range_dd.value}
                if is_edit: new_data['id'] = product_id; db.update_product(new_data)
                else: db.add_product(new_data)
                switch_to_list_view()
            except (ValueError, TypeError) as err: show_error_snackbar(f"Invalid input: {err}")
        
        return ft.Column(expand=True, spacing=15, scroll=ft.ScrollMode.ADAPTIVE, controls=[
            ft.Row([ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: switch_to_list_view()), ft.Text("Edit Item" if is_edit else "Add New Item", size=24, weight=ft.FontWeight.BOLD)]),
            name_input, category_dd, age_range_dd, price_input, stock_input, ft.Row([condition_new, condition_used]),
            ft.FilledButton("Save", on_click=save, width=200)
        ])
        
    def build_customer_form(switch_to_list_view, customer_id=None):
        is_edit = customer_id is not None
        customer_data = db.get_customer_by_id(customer_id) if is_edit else {}
        name_input = ft.TextField(label="Customer Name", value=customer_data.get('name', ''))
        email_input = ft.TextField(label="Email", value=customer_data.get('email', ''))
        phone_input = ft.TextField(label="Phone", value=customer_data.get('phone', ''))
        baby_name_input = ft.TextField(label="Baby's Name", value=customer_data.get('baby_name', ''))
        baby_age_input = ft.TextField(label="Baby's Age", value=customer_data.get('baby_age', ''))

        def save(e):
            new_data = {'name': name_input.value, 'email': email_input.value, 'phone': phone_input.value, 'baby_name': baby_name_input.value, 'baby_age': baby_age_input.value}
            if is_edit: new_data['id'] = customer_id; db.update_customer(new_data)
            else: db.add_customer(new_data)
            switch_to_list_view()

        return ft.Column(expand=True, spacing=15, scroll=ft.ScrollMode.ADAPTIVE, controls=[
            ft.Row([ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: switch_to_list_view()), ft.Text("Edit Customer" if is_edit else "Add New Customer", size=24, weight=ft.FontWeight.BOLD)]),
            name_input, email_input, phone_input, baby_name_input, baby_age_input,
            ft.FilledButton("Save", on_click=save, width=200)
        ])

    def build_sale_form(switch_to_list_view):
        all_customers = db.get_all_customers(); all_products = db.get_all_products()
        date_input = ft.TextField(label="Date", value=datetime.date.today().isoformat())
        customer_dd = ft.Dropdown(label="Select Customer", options=[ft.dropdown.Option(c['name']) for c in all_customers])
        product_dd = ft.Dropdown(label="Select Product", options=[ft.dropdown.Option(p['name']) for p in all_products if p['stock'] > 0])
        quantity_input = ft.TextField(label="Quantity", keyboard_type=ft.KeyboardType.NUMBER, value="1")

        def save(e):
            try:
                product_name = product_dd.value; quantity = int(quantity_input.value)
                product = next((p for p in all_products if p['name'] == product_name), None)
                if not product: show_error_snackbar("Please select a product."); return
                if quantity > product['stock']: show_error_snackbar(f"Not enough stock for {product_name}. Only {product['stock']} available."); return
                new_sale_data = {'date': date_input.value, 'customer_name': customer_dd.value, 'product_name': product_name, 'quantity': quantity, 'total': quantity * product['price'], 'size': product.get('size', 'N/A')}
                db.add_sale(new_sale_data); switch_to_list_view()
            except (ValueError, TypeError) as err: show_error_snackbar(f"Invalid input: {err}")

        return ft.Column(expand=True, spacing=15, scroll=ft.ScrollMode.ADAPTIVE, controls=[
            ft.Row([ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: switch_to_list_view()), ft.Text("Record New Sale", size=24, weight=ft.FontWeight.BOLD)]),
            date_input, customer_dd, product_dd, quantity_input,
            ft.FilledButton("Save", on_click=save, width=200)
        ])

    # ==========================================================
    # CONTENT BUILDER FUNCTIONS
    # ==========================================================
    def build_dashboard():
        products, customers, sales = db.get_all_products(), db.get_all_customers(), db.get_all_sales()
        total_products, total_customers, total_sales = len(products), len(customers), sum(s['total'] for s in sales)
        low_stock_items = len([p for p in products if p['stock'] <= 5])
        stats_cards = [
            ft.Card(col={"sm": 12, "md": 6, "lg": 3}, content=ft.Container(padding=15, content=ft.Column([ft.Text("Total Items"), ft.Text(str(total_products), size=24, weight=ft.FontWeight.BOLD)]))),
            ft.Card(col={"sm": 12, "md": 6, "lg": 3}, content=ft.Container(padding=15, content=ft.Column([ft.Text("Total Customers"), ft.Text(str(total_customers), size=24, weight=ft.FontWeight.BOLD)]))),
            ft.Card(col={"sm": 12, "md": 6, "lg": 3}, content=ft.Container(padding=15, content=ft.Column([ft.Text("Total Revenue"), ft.Text(f"${total_sales:.2f}", size=24, weight=ft.FontWeight.BOLD)]))),
            ft.Card(col={"sm": 12, "md": 6, "lg": 3}, content=ft.Container(padding=15, bgcolor=ft.Colors.ERROR_CONTAINER if low_stock_items > 0 else None, content=ft.Column([ft.Text("Low Stock Alerts"), ft.Text(str(low_stock_items), size=24, weight=ft.FontWeight.BOLD)]))),
        ]
        recent_sales_list = ft.Column(spacing=10, scroll=ft.ScrollMode.ADAPTIVE, expand=True)
        recent_sales_list.controls.append(ft.Text("Recent Sales", size=18, weight=ft.FontWeight.BOLD))
        for sale in sales[:5]: recent_sales_list.controls.append(ft.Container(padding=10, border_radius=ft.border_radius.all(10), bgcolor=ft.Colors.GREY_200, content=ft.Text(f"Sale #{sale['id']}: {sale['customer_name']} bought {sale['product_name']} (x{sale['quantity']}) for ${sale['total']:.2f}")))
        return ft.Column([ft.ResponsiveRow(controls=stats_cards), ft.Column([recent_sales_list], expand=True)], spacing=20, expand=True)

    def build_inventory(switch_to_form_callback):
        def delete_handler(product_id): db.delete_product(product_id); switch_to_page(1)
        products_list = ft.Column(spacing=10, scroll=ft.ScrollMode.ADAPTIVE, expand=True)
        for p in db.get_all_products():
            products_list.controls.append(ft.Container(padding=15, border_radius=ft.border_radius.all(10), bgcolor=ft.Colors.GREY_200,
                content=ft.ResponsiveRow(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                    ft.Column(col={"sm": 12, "md": 8}, controls=[ft.Text(f"{p['name']}", weight=ft.FontWeight.BOLD), ft.Text(f"Stock: {p['stock']}", color=ft.Colors.ERROR if p['stock'] <= 2 else ft.Colors.ON_SURFACE)]),
                    ft.Row(col={"sm": 12, "md": 4}, alignment=ft.MainAxisAlignment.END, controls=[
                        ft.IconButton(ft.Icons.EDIT, on_click=lambda _, pid=p['id']: switch_to_form_callback(pid)),
                        ft.IconButton(ft.Icons.DELETE_FOREVER, icon_color=ft.Colors.ERROR, on_click=lambda _, pid=p['id']: delete_handler(pid))])])))
        return products_list
        
    def build_sales():
        sales_list = ft.Column(spacing=10, scroll=ft.ScrollMode.ADAPTIVE, expand=True)
        for sale in db.get_all_sales(): sales_list.controls.append(ft.Container(padding=15, border_radius=ft.border_radius.all(10), bgcolor=ft.Colors.GREY_200, content=ft.Column([ft.Text(f"Sale #{sale['id']} - {sale['date']}", weight=ft.FontWeight.BOLD), ft.Text(f"Customer: {sale['customer_name']}"), ft.Text(f"Product: {sale['product_name']} (x{sale['quantity']}) - Total: ${sale['total']:.2f}") ])))
        return sales_list

    def build_customers(switch_to_form_callback):
        def delete_handler(customer_id): db.delete_customer(customer_id); switch_to_page(3)
        customers_list = ft.Column(spacing=10, scroll=ft.ScrollMode.ADAPTIVE, expand=True)
        for c in db.get_all_customers():
            customers_list.controls.append(ft.Container(padding=15, border_radius=ft.border_radius.all(10), bgcolor=ft.Colors.GREY_200, content=ft.ResponsiveRow(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                ft.Column(col={"sm": 12, "md": 8}, controls=[ft.Text(c['name'], weight=ft.FontWeight.BOLD), ft.Text(f"Total Spent: ${c.get('total_purchases', 0):.2f}")]),
                ft.Row(col={"sm": 12, "md": 4}, alignment=ft.MainAxisAlignment.END, controls=[
                    ft.IconButton(ft.Icons.EDIT, on_click=lambda _, cid=c['id']: switch_to_form_callback(cid)),
                    ft.IconButton(ft.Icons.DELETE_FOREVER, icon_color=ft.Colors.ERROR, on_click=lambda _, cid=c['id']: delete_handler(cid))])])))
        return customers_list

    # ==========================================================
    # MAIN NAVIGATION LOGIC
    # ==========================================================
    def switch_to_page(page_index, form_id=None):
        content_area.controls.clear()
        if page_index == 0: content_area.controls.append(build_dashboard())
        elif page_index == 1:
            if form_id is not None: content_area.controls.append(build_product_form(lambda: switch_to_page(1), form_id))
            else: content_area.controls.append(build_inventory(lambda fid: switch_to_page(1, fid)))
        elif page_index == 2:
            if form_id == "new": content_area.controls.append(build_sale_form(lambda: switch_to_page(2)))
            else: content_area.controls.append(build_sales())
        elif page_index == 3:
            if form_id is not None: content_area.controls.append(build_customer_form(lambda: switch_to_page(3), form_id))
            else: content_area.controls.append(build_customers(lambda cid: switch_to_page(3, cid)))
        rail.selected_index = page_index
        page.update()

    def add_button_clicked(e):
        current_index = rail.selected_index
        if current_index == 1: switch_to_page(1, "new")
        elif current_index == 2: switch_to_page(2, "new")
        elif current_index == 3: switch_to_page(3, "new")

    rail = ft.NavigationRail(
        selected_index=0, label_type=ft.NavigationRailLabelType.ALL, min_width=100,
        min_extended_width=200,
        leading=ft.FloatingActionButton(icon=ft.Icons.ADD, text="Add", on_click=add_button_clicked, shape=ft.RoundedRectangleBorder(radius=5)),
        group_alignment=-0.9,
        destinations=[
            ft.NavigationRailDestination(icon=ft.Icons.DASHBOARD_OUTLINED, selected_icon=ft.Icons.DASHBOARD, label="Dashboard"),
            ft.NavigationRailDestination(icon=ft.Icons.INVENTORY_2_OUTLINED, selected_icon=ft.Icons.INVENTORY_2, label="Inventory"),
            ft.NavigationRailDestination(icon=ft.Icons.POINT_OF_SALE_OUTLINED, selected_icon=ft.Icons.POINT_OF_SALE, label="Sales"),
            ft.NavigationRailDestination(icon=ft.Icons.PEOPLE_OUTLINE, selected_icon=ft.Icons.PEOPLE, label="Customers"),
        ],
        on_change=lambda e: switch_to_page(e.control.selected_index),
    )

    page.add(ft.Row([rail, ft.VerticalDivider(width=1), content_area], expand=True))
    switch_to_page(0)

if __name__ == '__main__':
    ft.app(target=main)
