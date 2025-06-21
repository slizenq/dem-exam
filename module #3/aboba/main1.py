import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import csv
import os
import sys

def get_script_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

SCRIPT_DIR = get_script_dir()

def create_database(db_file):
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS partners (
                partner_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                partner_type TEXT NOT NULL,
                rating INTEGER NOT NULL CHECK(rating >= 0),
                address TEXT,
                director_name TEXT,
                phone TEXT,
                email TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                product_type_id INTEGER NOT NULL,
                param1 REAL NOT NULL CHECK(param1 > 0),
                param2 REAL NOT NULL CHECK(param2 > 0)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales (
                sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
                partner_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL CHECK(quantity > 0),
                sale_date TEXT NOT NULL,
                FOREIGN KEY (partner_id) REFERENCES partners(partner_id) ON DELETE RESTRICT,
                FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE RESTRICT
            )
        ''')

        conn.commit()
        print(f"Database tables created successfully in {db_file}")
    except sqlite3.Error as e:
        print(f"Error creating database tables: {str(e)}")
        raise
    finally:
        conn.close()

def import_csv_data(db_file):
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        partner_headers = ['name', 'partner_type', 'rating', 'address', 'director_name', 'phone', 'email']
        product_headers = ['name', 'product_type_id', 'param1', 'param2']
        sales_headers = ['partner_id', 'product_id', 'quantity', 'sale_date']
        partners_inserted = 0
        products_inserted = 0
        sales_inserted = 0
        cursor.execute("SELECT partner_id FROM partners")
        valid_partner_ids = {row[0] for row in cursor.fetchall()}
        cursor.execute("SELECT product_id FROM products")
        valid_product_ids = {row[0] for row in cursor.fetchall()}
        partners_path = os.path.join(SCRIPT_DIR, 'partners.csv')
        if os.path.exists(partners_path):
            with open(partners_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                if not all(h in reader.fieldnames for h in partner_headers):
                    print(f"Error: partners.csv has incorrect headers. Expected: {partner_headers}, Found: {reader.fieldnames}")
                    raise ValueError("Incorrect headers in partners.csv")
                for row in reader:
                    try:
                        cursor.execute('''
                            INSERT OR IGNORE INTO partners (name, partner_type, rating, address, director_name, phone, email)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (row['name'], row['partner_type'], int(row['rating']), row['address'] or None,
                              row['director_name'] or None, row['phone'] or None, row['email'] or None))
                        if cursor.rowcount > 0:
                            partners_inserted += 1
                    except (ValueError, sqlite3.Error) as e:
                        print(f"Error importing row in partners.csv: {row}, Error: {str(e)}")
                        continue
            print(f"Imported {partners_inserted} rows from partners.csv")
        else:
            print(f"Warning: partners.csv not found at {partners_path}")
        cursor.execute("SELECT partner_id FROM partners")
        valid_partner_ids = {row[0] for row in cursor.fetchall()}
        products_path = os.path.join(SCRIPT_DIR, 'products.csv')
        if os.path.exists(products_path):
            with open(products_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                if not all(h in reader.fieldnames for h in product_headers):
                    print(f"Error: products.csv has incorrect headers. Expected: {product_headers}, Found: {reader.fieldnames}")
                    raise ValueError("Incorrect headers in products.csv")
                for row in reader:
                    try:
                        cursor.execute('''
                            INSERT OR IGNORE INTO products (name, product_type_id, param1, param2)
                            VALUES (?, ?, ?, ?)
                        ''', (row['name'], int(row['product_type_id']), float(row['param1']), float(row['param2'])))
                        if cursor.rowcount > 0:
                            products_inserted += 1
                    except (ValueError, sqlite3.Error) as e:
                        print(f"Error importing row in products.csv: {row}, Error: {str(e)}")
                        continue
            print(f"Imported {products_inserted} rows from products.csv")
        else:
            print(f"Warning: products.csv not found at {products_path}")

        cursor.execute("SELECT product_id FROM products")
        valid_product_ids = {row[0] for row in cursor.fetchall()}
        sales_path = os.path.join(SCRIPT_DIR, 'sales.csv')
        if os.path.exists(sales_path):
            with open(sales_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                if not all(h in reader.fieldnames for h in sales_headers):
                    print(f"Error: sales.csv has incorrect headers. Expected: {sales_headers}, Found: {reader.fieldnames}")
                    raise ValueError("Incorrect headers in sales.csv")
                for row in reader:
                    try:
                        partner_id = int(row['partner_id'])
                        product_id = int(row['product_id'])
                        if partner_id not in valid_partner_ids:
                            print(f"Skipping sale row with invalid partner_id={partner_id}: {row}")
                            continue
                        if product_id not in valid_product_ids:
                            print(f"Skipping sale row with invalid product_id={product_id}: {row}")
                            continue
                        cursor.execute('''
                            INSERT OR IGNORE INTO sales (partner_id, product_id, quantity, sale_date)
                            VALUES (?, ?, ?, ?)
                        ''', (partner_id, product_id, int(row['quantity']), row['sale_date']))
                        if cursor.rowcount > 0:
                            sales_inserted += 1
                    except (ValueError, sqlite3.Error) as e:
                        print(f"Error importing row in sales.csv: {row}, Error: {str(e)}")
                        continue
            print(f"Imported {sales_inserted} rows from sales.csv")
        else:
            print(f"Warning: sales.csv not found at {sales_path}")

        conn.commit()
        print("CSV data imported successfully.")
    except sqlite3.Error as e:
        print(f"Error importing CSV data: {str(e)}")
        raise
    except Exception as e:
        print(f"General error during CSV import: {str(e)}")
        raise
    finally:
        conn.close()

def initialize_database(db_file):
    try:
        create_database(db_file)
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM partners")
        partners_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM products")
        products_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM sales")
        sales_count = cursor.fetchone()[0]
        conn.close()

        print(f"Database state: partners={partners_count}, products={products_count}, sales={sales_count}")
        if partners_count == 0 or products_count == 0 or sales_count == 0:
            print("One or more tables are empty, importing CSV data.")
            import_csv_data(db_file)
        else:
            print("All tables contain data, preserving existing data.")
    except sqlite3.Error as e:
        print(f"Database initialization failed: {str(e)}")
        messagebox.showerror("Ошибка", f"Не удалось инициализировать базу данных: {str(e)}")
        raise
    except Exception as e:
        print(f"Unexpected error during database initialization: {str(e)}")
        raise

def table_exists(db_file, table_name):
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists
    except sqlite3.Error as e:
        print(f"Error checking table existence: {str(e)}")
        return False

class PartnerDialog(tk.Toplevel):
    def __init__(self, parent, db_file, partner_id=None):
        super().__init__(parent)
        self.parent = parent
        self.db_file = db_file
        self.partner_id = partner_id
        self.title("Редактировать партнера" if partner_id else "Добавить партнера")
        self.geometry("400x300")
        self.transient(parent)
        self.grab_set()
        self.init_ui()
        if partner_id:
            self.load_partner_data()

    def init_ui(self):
        frame = ttk.Frame(self, padding="10")
        frame.grid(row=0, column=0, sticky="nsew")

        ttk.Label(frame, text="Наименование:").grid(row=0, column=0, sticky="w", pady=2)
        self.name_input = ttk.Entry(frame)
        self.name_input.grid(row=0, column=1, sticky="ew", pady=2)

        ttk.Label(frame, text="Тип продукта:").grid(row=1, column=0, sticky="w", pady=2)
        self.type_input = ttk.Combobox(frame, values=["1 тип", "2 тип", "3 тип", "4 тип"], state="readonly")
        self.type_input.grid(row=1, column=1, sticky="ew", pady=2)
        self.type_input.set("тип материала")

        ttk.Label(frame, text="Мин. стоимость").grid(row=2, column=0, sticky="w", pady=2)
        self.rating_input = ttk.Entry(frame)
        self.rating_input.grid(row=2, column=1, sticky="ew", pady=2)

        ttk.Label(frame, text="Адрес:").grid(row=3, column=0, sticky="w", pady=2)
        self.address_input = ttk.Entry(frame)
        self.address_input.grid(row=3, column=1, sticky="ew", pady=2)

        ttk.Label(frame, text="Основной материал").grid(row=4, column=0, sticky="w", pady=2)
        self.director_input = ttk.Entry(frame)
        self.director_input.grid(row=4, column=1, sticky="ew", pady=2)

        ttk.Label(frame, text="Артикул").grid(row=5, column=0, sticky="w", pady=2)
        self.phone_input = ttk.Entry(frame)
        self.phone_input.grid(row=5, column=1, sticky="ew", pady=2)

        ttk.Label(frame, text="Email:").grid(row=6, column=0, sticky="w", pady=2)
        self.email_input = ttk.Entry(frame)
        self.email_input.grid(row=6, column=1, sticky="ew", pady=2)

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=7, column=0, columnspan=2, pady=10)
        ttk.Button(button_frame, text="Сохранить", command=self.save_partner).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Отмена", command=self.destroy).grid(row=0, column=1, padx=5)

        frame.columnconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

    def load_partner_data(self):
        try:
            if not table_exists(self.db_file, 'partners'):
                messagebox.showerror("Ошибка", "Таблица 'partners' не существует.", parent=self)
                return
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM partners WHERE partner_id = ?', (self.partner_id,))
            partner = cursor.fetchone()
            conn.close()

            if partner:
                self.name_input.insert(0, partner[1])
                self.type_input.set(partner[2])
                self.rating_input.insert(0, str(partner[3]))
                self.address_input.insert(0, partner[4] or "")
                self.director_input.insert(0, partner[5] or "")
                self.phone_input.insert(0, partner[6] or "")
                self.email_input.insert(0, partner[7] or "")
        except sqlite3.Error as e:
            print(f"Error loading partner data: {str(e)}")
            messagebox.showerror("Ошибка", f"Не удалось загрузить данные партнера: {str(e)}", parent=self)

    def save_partner(self):
        try:
            if not table_exists(self.db_file, 'partners'):
                messagebox.showerror("Ошибка", "Таблица 'partners' не существует.", parent=self)
                return
            name = self.name_input.get().strip()
            partner_type = self.type_input.get()
            rating = int(self.rating_input.get().strip())
            address = self.address_input.get().strip() or None
            director = self.director_input.get().strip() or None
            phone = self.phone_input.get().strip() or None
            email = self.email_input.get().strip() or None

            if not name or rating < 0:
                messagebox.showwarning("Ошибка",
                                      "Заполните обязательные поля: наименование и рейтинг (неотрицательный).",
                                      parent=self)
                return

            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            if self.partner_id:
                cursor.execute('''
                    UPDATE partners SET name = ?, partner_type = ?, rating = ?, address = ?,
                    director_name = ?, phone = ?, email = ? WHERE partner_id = ?
                ''', (name, partner_type, rating, address, director, phone, email, self.partner_id))
            else:
                cursor.execute('''
                    INSERT INTO partners (name, partner_type, rating, address, director_name, phone, email)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (name, partner_type, rating, address, director, phone, email))
            conn.commit()
            conn.close()
            self.parent.load_partners()
            self.destroy()
        except ValueError:
            messagebox.showwarning("Ошибка", "Стоимость не может быть пустой и отрицательной", parent=self)
        except sqlite3.Error as e:
            print(f"Error saving partner: {str(e)}")
            messagebox.showerror("Ошибка", f"Ошибка сохранения: {str(e)}", parent=self)
 
class MainWindow(tk.Tk):
    def __init__(self, db_file):
        super().__init__()
        self.db_file = db_file
        self.title("Учет материлов")
        self.geometry("1400x600")
        try:
            initialize_database(self.db_file)
        except sqlite3.Error:
            self.destroy()
            return
        self.init_ui()

    def init_ui(self):
        frame = ttk.Frame(self, padding="10")
        frame.grid(row=0, column=0, sticky="nsew")

        self.partners_table = ttk.Treeview(frame, columns=("ID", "Наименование", "Тип", "Мин. стоимость", "Адрес",
                                                          "Основной материал", "Артикул", "Email"), show="headings")
        headers = ["ID", "Наименование", "Тип", "Мин. стоимость", "Адрес", "Основной материал", "Артикул", "Email"]
        for header in headers:
            self.partners_table.heading(header, text=header)
            self.partners_table.column(header, width=100)
        self.partners_table.grid(row=0, column=0, sticky="nsew")
        self.partners_table.bind("<Double-1>", self.edit_partner)

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.partners_table.yview)
        self.partners_table.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=10)
        ttk.Button(button_frame, text="Добавить материалы", command=self.add_partner).grid(row=0, column=0, padx=5)

        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.load_partners()

    def load_partners(self):
        try:
            if not table_exists(self.db_file, 'partners'):
                messagebox.showerror("Ошибка", "Таблица 'partners' не существует.", parent=self)
                return
            for item in self.partners_table.get_children():
                self.partners_table.delete(item)

            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM partners')
            partners = cursor.fetchall()
            conn.close()

            print(f"Loaded {len(partners)} partners")
            for partner in partners:
                self.partners_table.insert("", "end", values=partner)
        except sqlite3.Error as e:
            print(f"Error loading partners: {str(e)}")
            messagebox.showerror("Ошибка", f"Не удалось загрузить список партнеров: {str(e)}", parent=self)
        except Exception as e:
            print(f"Unexpected error in load_partners: {str(e)}")
            messagebox.showerror("Ошибка", f"Неожиданная ошибка: {str(e)}", parent=self)

    def add_partner(self):
        PartnerDialog(self, self.db_file)

    def edit_partner(self, event):
        selected_item = self.partners_table.selection()
        if not selected_item:
            return
        partner_id = int(self.partners_table.item(selected_item)["values"][0])
        PartnerDialog(self, self.db_file, partner_id=partner_id)

    def view_sales(self):
        selected_item = self.partners_table.selection()
        if not selected_item:
            messagebox.showwarning("Ошибка", "Выберите партнера для просмотра истории продаж.", parent=self)
            return
        partner_id = int(self.partners_table.item(selected_item)["values"][0])
        print(f"Opening sales history for partner_id={partner_id}")
        SalesDialog(self, self.db_file, partner_id)

    
if __name__ == "__main__":
    app = MainWindow("partners.db")
    app.mainloop()