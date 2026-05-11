"""
Database Module for Ethiosadat Furniture

This module handles all database connections, initialization,
and management for the application.
"""

import sqlite3
import os
from flask import g
from config import Config


def get_database_path():
    """
    Get the correct database path from Config.DATABASE_PATH.

    Returns:
        str: Database file path
    """
    return Config.DATABASE_PATH


def get_db():
    """
    Get database connection from Flask's g object.
    Creates a new connection if one doesn't exist.
    Falls back to a direct connection if outside request context.

    Returns:
        sqlite3.Connection: Database connection with row_factory set to sqlite3.Row
    """
    try:
        if "db" not in g:
            db_path = get_database_path()

            db_dir = os.path.dirname(db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)

            conn = sqlite3.connect(db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            g.db = conn

        if g.db is None:
            raise RuntimeError("g.db is None after assignment")

        return g.db

    except RuntimeError:
        # Outside request context — return a direct connection
        db_path = get_database_path()
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        return conn


def close_db(e=None):
    """
    Close database connection if it exists.
    Called at the end of each request.
    """
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """
    Initialize the database with all required tables.
    Creates tables if they don't exist and inserts default data.
    """
    db_path = get_database_path()

    # Ensure database directory exists
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        print(f"📁 Created database directory: {db_dir}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # ==================== CREATE TABLES ====================

    # Users table (must come first due to foreign keys)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            phone TEXT,
            address TEXT,
            city TEXT,
            is_admin INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    """)
    print("✅ Users table ready")

    # Categories table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            name_am TEXT,
            name_ar TEXT,
            description TEXT,
            icon TEXT,
            image TEXT,
            sort_order INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            parent_id INTEGER,
            FOREIGN KEY (parent_id) REFERENCES categories (id)
        )
    """)
    print("✅ Categories table ready")

    # Products table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            name_am TEXT,
            name_ar TEXT,
            name_en TEXT,
            description TEXT,
            description_am TEXT,
            description_ar TEXT,
            description_en TEXT,
            price REAL NOT NULL,
            compare_price REAL,
            cost REAL,
            sku TEXT UNIQUE,
            barcode TEXT,
            stock_quantity INTEGER DEFAULT 0,
            low_stock_threshold INTEGER DEFAULT 5,
            images TEXT,
            thumbnail TEXT,
            is_active INTEGER DEFAULT 1,
            is_featured INTEGER DEFAULT 0,
            is_new INTEGER DEFAULT 0,
            weight REAL,
            dimensions TEXT,
            material TEXT,
            color TEXT,
            views INTEGER DEFAULT 0,
            sales_count INTEGER DEFAULT 0,
            category_id INTEGER NOT NULL,
            meta_title TEXT,
            meta_description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories (id)
        )
    """)
    print("✅ Products table ready")

    # Cart Items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cart_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER DEFAULT 1,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    """)
    print("✅ Cart items table ready")

    # Orders table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            payment_status TEXT DEFAULT 'pending',
            payment_method TEXT,
            subtotal REAL NOT NULL,
            discount REAL DEFAULT 0,
            shipping_fee REAL DEFAULT 0,
            total REAL NOT NULL,
            shipping_address TEXT NOT NULL,
            shipping_city TEXT,
            shipping_phone TEXT,
            notes TEXT,
            tracking_number TEXT,
            estimated_delivery DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    print("✅ Orders table ready")

    # Order Items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price_at_time REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    """)
    print("✅ Order items table ready")

    # Advertisements table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS advertisements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            title_am TEXT,
            title_ar TEXT,
            description TEXT,
            description_am TEXT,
            description_ar TEXT,
            image TEXT NOT NULL,
            link TEXT,
            sort_order INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✅ Advertisements table ready")

    # Branches table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS branches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            name_am TEXT,
            name_ar TEXT,
            address TEXT NOT NULL,
            address_am TEXT,
            address_ar TEXT,
            phone TEXT,
            email TEXT,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            working_hours TEXT,
            image TEXT,
            sort_order INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1
        )
    """)
    print("✅ Branches table ready")

    # Notifications table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            title_am TEXT,
            title_ar TEXT,
            body TEXT NOT NULL,
            body_am TEXT,
            body_ar TEXT,
            image TEXT,
            link TEXT,
            target_audience TEXT DEFAULT 'all',
            sent_count INTEGER DEFAULT 0,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
    """)
    print("✅ Notifications table ready")

    # Settings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✅ Settings table ready")

    # ==================== INSERT DEFAULT DATA ====================

    # Insert default categories if table is empty
    cursor.execute("SELECT COUNT(*) FROM categories")
    if cursor.fetchone()[0] == 0:
        default_categories = [
            ("ሶፋ", "Sofa", "صوفا", "🛋️", 1),
            ("አልጋ", "Bed", "سرير", "🛏️", 2),
            ("መጅሊስ", "Mejlis", "مجلس", "🪑", 3),
            ("መጋረጃ", "Curtain", "ستارة", "🚪", 4),
            ("ቁምሳጥን", "Wardrobe", "خزانة", "🗄️", 5),
            ("ሌላ", "Other", "آخر", "📦", 6),
        ]
        cursor.executemany(
            "INSERT INTO categories (name, name_am, name_ar, icon, sort_order) VALUES (?, ?, ?, ?, ?)",
            default_categories,
        )
        print(f"✅ Added {len(default_categories)} default categories")

    # Insert default admin user if no users exist
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        from werkzeug.security import generate_password_hash

        admin_password_hash = generate_password_hash(
            "admin123456", method="pbkdf2:sha256"
        )
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, full_name, is_admin, is_active) VALUES (?, ?, ?, ?, ?, ?)",
            (
                "admin",
                "admin@ethiosadat.com",
                admin_password_hash,
                "Administrator",
                1,
                1,
            ),
        )
        print("✅ Default admin user created (username: admin, password: admin123456)")

    # Insert default settings if empty
    cursor.execute("SELECT COUNT(*) FROM settings")
    if cursor.fetchone()[0] == 0:
        default_settings = [
            ("site_name", "Ethiosadat Furniture"),
            ("site_name_am", "ኢትዮሳዳት ቤት ዕቃ"),
            ("site_name_ar", "إثيوصادات للأثاث"),
            ("site_email", "info@ethiosadat.com"),
            ("site_phone", "+251906020606"),
            ("whatsapp_number", "251906020606"),
            ("free_shipping_threshold", "5000"),
            ("shipping_cost", "200"),
            ("currency", "ETB"),
            ("default_language", "am"),
        ]
        cursor.executemany(
            "INSERT INTO settings (key, value) VALUES (?, ?)", default_settings
        )
        print(f"✅ Added {len(default_settings)} default settings")

    # Insert branches data
    cursor.execute("SELECT COUNT(*) FROM branches")
    if cursor.fetchone()[0] == 0:
        branches = [
            (
                "መሀል መርካቶ ማርስ",
                "ማርስ የገበያ ማእከል 2ኛ ፎቅ ሱቅ ቁጥር 230",
                9.0100,
                38.7450,
                "+251906020606",
                1,
            ),
            ("ቤተል", "ቢጫ ፎቅ ጎን", 9.0080, 38.7600, "+251906080606", 2),
            ("ፉሪ ኖክ", "ኖክ ማደያ ፊት ለፊት", 8.9900, 38.7300, "+251906090606", 3),
            ("ድሬዳዋ መስቀለኛ", "የሰይዶ ታክሲ ተራ ጋር", 9.5900, 41.8500, "+251906020606", 4),
            ("ድሬዳዋ ሞል", "ቢራ ሞል 1ኛ ፎቅ", 9.5950, 41.8550, "+251906080606", 5),
            ("አሶሳ", "የተባበሩት ማዲያ ፊትለፊት", 10.0700, 34.5300, "+251906090606", 6),
            ("ቡታጅራ", "ቄጤማ መናኸሪያ ጎን", 8.1200, 38.3700, "+251906020606", 7),
            ("ሽሬ", "ቶታል ማዲያ ፊትለፊት", 14.1000, 38.2800, "+251906080606", 8),
            ("ሰመራ", "", 11.7900, 41.0100, "+251906090606", 9),
        ]
        for branch in branches:
            cursor.execute(
                "INSERT INTO branches (name, address, latitude, longitude, phone, sort_order, is_active) VALUES (?, ?, ?, ?, ?, ?, 1)",
                branch,
            )
        print(f"✅ Added {len(branches)} branches")

    # ==================== CREATE INDEXES ====================

    # Product indexes
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_products_featured ON products(is_featured)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_products_created ON products(created_at)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_products_active ON products(is_active)"
    )

    # Order indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)")
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_orders_created ON orders(created_at)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_orders_number ON orders(order_number)"
    )

    # User indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")

    # Cart indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cart_user ON cart_items(user_id)")
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_cart_product ON cart_items(product_id)"
    )

    # Advertisement indexes
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_ads_active ON advertisements(is_active)"
    )

    print("✅ Indexes created")

    conn.commit()
    conn.close()

    print("=" * 50)
    print("✅ Database initialized successfully!")
    print(f"📁 Database path: {os.path.abspath(db_path)}")
    print("=" * 50)


def init_db_app(app):
    """
    Initialize database within Flask app context.
    This function should be called when creating the Flask app.

    Args:
        app: Flask application instance
    """
    with app.app_context():
        init_db()


def get_db_stats():
    """
    Get database statistics for admin dashboard.

    Returns:
        dict: Statistics including counts of products, ads, orders
    """
    try:
        db = get_db()
        cursor = db.cursor()

        cursor.execute("SELECT COUNT(*) FROM products")
        products_count = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM advertisements")
        ads_count = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM orders")
        orders_count = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM categories")
        categories_count = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM users")
        users_count = cursor.fetchone()[0] or 0

        # Get pending orders count
        cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'pending'")
        pending_orders = cursor.fetchone()[0] or 0

        return {
            "products": products_count,
            "ads": ads_count,
            "orders": orders_count,
            "categories": categories_count,
            "users": users_count,
            "pending_orders": pending_orders,
        }
    except Exception as e:
        print(f"Error getting DB stats: {e}")
        return {
            "products": 0,
            "ads": 0,
            "orders": 0,
            "categories": 0,
            "users": 0,
            "pending_orders": 0,
        }


def commit_or_rollback(db=None):
    """
    Commit the current transaction, or rollback on failure.

    Args:
        db: Optional database connection. If not provided, uses get_db().

    Returns:
        bool: True if commit succeeded, False if rolled back.
    """
    if db is None:
        db = get_db()
    try:
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Transaction rolled back: {e}")
        return False


def test_connection():
    """
    Test database connection and return status.

    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        db_path = get_database_path()
        conn = sqlite3.connect(db_path)
        conn.close()
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False
