import sqlite3
import hashlib
from passlib.context import CryptContext
import pandas as pd
from datetime import datetime
import os

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class DBManager:
    def __init__(self, db_path=None):
        if db_path is None:
            # Use a relative path from this file to find the database
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.db_path = os.path.join(base_dir, "database", "expense_tracker.db")
        else:
            self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """Initializes the database tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Transactions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    type TEXT NOT NULL, -- 'Income' or 'Expense'
                    category TEXT NOT NULL,
                    amount REAL NOT NULL,
                    date TEXT NOT NULL,
                    description TEXT,
                    is_deleted INTEGER DEFAULT 0,
                    deleted_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Migration: Add columns if they don't exist
            try:
                cursor.execute("ALTER TABLE transactions ADD COLUMN is_deleted INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass 
            
            try:
                cursor.execute("ALTER TABLE transactions ADD COLUMN deleted_at TIMESTAMP")
            except sqlite3.OperationalError:
                pass
            
            # Budgets table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS budgets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    category TEXT NOT NULL,
                    amount REAL NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE(user_id, category)
                )
            ''')
            
            # Categories table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    UNIQUE(user_id, name)
                )
            ''')
            conn.commit()
            self._seed_categories()

    def _seed_categories(self):
        """Seed default categories for new users if they don't have any."""
        # This is a bit tricky since we don't have a user_id here. 
        # Categories are per-user, so we'll handle seeding during signup/login or check on demand.
        pass

    def get_or_create_user_categories(self, user_id):
        default_cats = ["Food & Dining", "Transport", "Shopping", "Entertainment", "Utilities", "Health", "Salary", "Investment"]
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM categories WHERE user_id = ?", (user_id,))
            existing = [row[0] for row in cursor.fetchall()]
            
            if not existing:
                for cat in default_cats:
                    cursor.execute("INSERT OR IGNORE INTO categories (user_id, name) VALUES (?, ?)", (user_id, cat))
                conn.commit()
                return default_cats
            return existing

    def add_category(self, user_id, name):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO categories (user_id, name) VALUES (?, ?)", (user_id, name))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def delete_category(self, user_id, name, fallback="Other"):
        """Deletes a category and reassigns all its transactions/budgets to a fallback."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Ensure fallback exists
            cursor.execute("INSERT OR IGNORE INTO categories (user_id, name) VALUES (?, ?)", (user_id, fallback))
            # Reassign transactions
            cursor.execute("UPDATE transactions SET category = ? WHERE user_id = ? AND category = ?", (fallback, user_id, name))
            # Reassign budgets (if a budget for fallback already exists, we might sum them or just delete the old one)
            cursor.execute("DELETE FROM budgets WHERE user_id = ? AND category = ?", (user_id, name))
            # Delete category
            cursor.execute("DELETE FROM categories WHERE user_id = ? AND name = ?", (user_id, name))
            conn.commit()

    def rename_category(self, user_id, old_name, new_name):
        """Renames a category and updates all associated records."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                # Update category name
                cursor.execute("UPDATE categories SET name = ? WHERE user_id = ? AND name = ?", (new_name, user_id, old_name))
                # Update transactions
                cursor.execute("UPDATE transactions SET category = ? WHERE user_id = ? AND category = ?", (new_name, user_id, old_name))
                # Update budgets
                cursor.execute("UPDATE budgets SET category = ? WHERE user_id = ? AND category = ?", (new_name, user_id, old_name))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                # New name might already exist
                return False

    def merge_categories(self, user_id, source_name, target_name):
        """Merges all data from source category into target category and deletes source."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Reassign transactions
            cursor.execute("UPDATE transactions SET category = ? WHERE user_id = ? AND category = ?", (target_name, user_id, source_name))
            # Reassign budgets: if both have budgets, we can sum them or take the target's
            # For simplicity, we delete the source budget and let the user re-adjust
            cursor.execute("DELETE FROM budgets WHERE user_id = ? AND category = ?", (user_id, source_name))
            # Delete source category
            cursor.execute("DELETE FROM categories WHERE user_id = ? AND name = ?", (user_id, source_name))
            conn.commit()

    # --- Authentication Methods ---
    def create_user(self, username, password):
        hashed_pw = pwd_context.hash(password)
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False

    def verify_user(self, username, password):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, password FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            if user and pwd_context.verify(password, user[1]):
                return user[0] # Return user_id
            return None

    # --- Transaction Methods ---
    def add_transaction(self, user_id, t_type, category, amount, date, description):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO transactions (user_id, type, category, amount, date, description)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, t_type, category, amount, date, description))
            conn.commit()

    def get_transactions(self, user_id, include_deleted=False):
        query = "SELECT * FROM transactions WHERE user_id = ?"
        if not include_deleted:
            query += " AND is_deleted = 0"
        else:
            query += " AND is_deleted = 1"
        query += " ORDER BY date DESC"
        
        with self._get_connection() as conn:
            return pd.read_sql_query(query, conn, params=(user_id,))

    def delete_transaction(self, t_id, user_id):
        """Soft delete: moves transaction to trash."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE transactions 
                SET is_deleted = 1, deleted_at = CURRENT_TIMESTAMP 
                WHERE id = ? AND user_id = ?
            ''', (t_id, user_id))
            conn.commit()

    def restore_transaction(self, t_id, user_id):
        """Restores a soft-deleted transaction."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE transactions 
                SET is_deleted = 0, deleted_at = NULL 
                WHERE id = ? AND user_id = ?
            ''', (t_id, user_id))
            conn.commit()

    def hard_delete_transaction(self, t_id, user_id):
        """Permanently deletes a transaction."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM transactions WHERE id = ? AND user_id = ?", (t_id, user_id))
            conn.commit()

    def update_transaction(self, t_id, user_id, t_type, category, amount, date, description):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE transactions 
                SET type = ?, category = ?, amount = ?, date = ?, description = ?
                WHERE id = ? AND user_id = ?
            ''', (t_type, category, amount, date, description, t_id, user_id))
            conn.commit()

    # --- Budget Methods ---
    def set_budget(self, user_id, category, amount):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO budgets (user_id, category, amount)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, category) DO UPDATE SET amount = excluded.amount
            ''', (user_id, category, amount))
            conn.commit()

    def get_budgets(self, user_id):
        with self._get_connection() as conn:
            return pd.read_sql_query("SELECT category, amount FROM budgets WHERE user_id = ?", conn, params=(user_id,))
