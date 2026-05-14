"""
Customer Routes for Ethiosadat Furniture

This module contains all public-facing routes including:
- Home page
- Product listing and details
- Category pages
- About us
- Branches with Google Maps
- Contact page
- User authentication (login, register, profile)
- Order history
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from middleware.auth import user_login_required
from middleware.platform import get_platform, is_android_app
from database.db import get_db
from database.models import Product, Order
from werkzeug.security import generate_password_hash, check_password_hash
import re

customer_bp = Blueprint('customer', __name__)


# ==================== HOME PAGE ====================

@customer_bp.route('/')
def index():
    """Home page"""
    db = get_db()
    cursor = db.cursor()
    
    # Get featured products
    cursor.execute("""
        SELECT p.*, c.name as category_name 
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.is_active = 1 AND p.is_featured = 1
        ORDER BY p.id DESC
        LIMIT 8
    """)
    featured_products = cursor.fetchall()
    
    # Get new products
    cursor.execute("""
        SELECT p.*, c.name as category_name 
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.is_active = 1 AND p.is_new = 1
        ORDER BY p.id DESC
        LIMIT 8
    """)
    new_products = cursor.fetchall()
    
    # Get active advertisements (slider)
    cursor.execute("""
        SELECT * FROM advertisements 
        WHERE is_active = 1 
        AND (end_date IS NULL OR end_date > datetime('now'))
        ORDER BY sort_order ASC
    """)
    ads = cursor.fetchall()
    
    # Get categories for navigation
    cursor.execute("""
        SELECT * FROM categories 
        WHERE is_active = 1 
        ORDER BY sort_order ASC
    """)
    categories = cursor.fetchall()
    
    # Get platform for showing/hiding about section
    platform = get_platform()
    show_about = platform == 'desktop' or platform == 'mobile_browser'
    
    return render_template('customer/index.html',
                         featured_products=featured_products,
                         new_products=new_products,
                         ads=ads,
                         categories=categories,
                         show_about=show_about,
                         platform=platform)


# ==================== PRODUCT ROUTES ====================

@customer_bp.route('/products')
def products():
    """Product listing page"""
    category_id = request.args.get('category', type=int)
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    db = get_db()
    cursor = db.cursor()
    
    # Build query
    query = """
        SELECT p.*, c.name as category_name 
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.is_active = 1
    """
    params = []
    
    if category_id:
        query += " AND p.category_id = ?"
        params.append(category_id)
    
    if search:
        query += " AND (p.name LIKE ? OR p.name_am LIKE ? OR p.name_ar LIKE ?)"
        search_term = f'%{search}%'
        params.extend([search_term, search_term, search_term])
    
    # Get total count
    count_query = query.replace("p.*, c.name as category_name", "COUNT(*) as total")
    cursor.execute(count_query, params)
    total = cursor.fetchone()['total']
    
    # Add pagination
    query += " ORDER BY p.id DESC LIMIT ? OFFSET ?"
    params.extend([per_page, (page - 1) * per_page])
    
    cursor.execute(query, params)
    products = cursor.fetchall()
    
    # Get categories for filter
    cursor.execute("SELECT * FROM categories WHERE is_active = 1 ORDER BY sort_order")
    categories = cursor.fetchall()
    
    return render_template('customer/product_grid.html',
                         products=products,
                         categories=categories,
                         current_category=category_id,
                         search=search,
                         page=page,
                         total=total,
                         per_page=per_page)


@customer_bp.route('/product/<int:product_id>')
def product_detail(product_id):
    """Product detail page"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("""
        SELECT p.*, c.name as category_name, c.name_am as category_name_am
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.id = ? AND p.is_active = 1
    """, (product_id,))
    
    product = cursor.fetchone()
    
    if not product:
        flash('Product not found!', 'danger')
        return redirect(url_for('customer.products'))
    
    # Increment view count
    cursor.execute("UPDATE products SET views = views + 1 WHERE id = ?", (product_id,))
    db.commit()
    
    # Get related products (same category)
    cursor.execute("""
        SELECT * FROM products 
        WHERE category_id = ? AND id != ? AND is_active = 1
        ORDER BY id DESC
        LIMIT 4
    """, (product['category_id'], product_id))
    related_products = cursor.fetchall()
    
    # Get discount percentage
    discount = None
    if product['compare_price'] and product['compare_price'] > product['price']:
        discount = int(((product['compare_price'] - product['price']) / product['compare_price']) * 100)
    
    # Check if user is logged in for discount
    is_logged_in = session.get('user_id') is not None
    final_price = product['price']
    if is_logged_in:
        final_price = product['price'] * 0.9
    
    return render_template('customer/product_detail.html',
                         product=product,
                         related_products=related_products,
                         discount=discount,
                         final_price=round(final_price, 2),
                         is_logged_in=is_logged_in)


# ==================== CATEGORY ROUTES ====================

@customer_bp.route('/categories')
def categories():
    """Categories page"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("""
        SELECT c.*, COUNT(p.id) as product_count
        FROM categories c
        LEFT JOIN products p ON p.category_id = c.id AND p.is_active = 1
        WHERE c.is_active = 1
        GROUP BY c.id
        ORDER BY c.sort_order ASC
    """)
    
    categories = cursor.fetchall()
    
    return render_template('customer/categories.html', categories=categories)


# ==================== BRANCHES ROUTES ====================

@customer_bp.route('/branches')
def branches():
    """Branches page with Google Maps"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("""
        SELECT * FROM branches 
        WHERE is_active = 1 
        ORDER BY sort_order ASC
    """)
    
    branches = cursor.fetchall()
    
    # Get phone numbers from settings
    cursor.execute("SELECT key, value FROM settings")
    settings = {row['key']: row['value'] for row in cursor.fetchall()}
    
    phone_numbers = [
        settings.get('site_phone', '0906020606'),
        '0906080606',
        '0906090606'
    ]
    
    return render_template('customer/branches.html',
                         branches=branches,
                         phone_numbers=phone_numbers,
                         google_maps_api_key='')  # Free tier doesn't require API key


# ==================== ABOUT PAGE ====================

@customer_bp.route('/about')
def about():
    """About us page"""
    db = get_db()
    cursor = db.cursor()
    
    # Get company info from settings
    cursor.execute("SELECT key, value FROM settings")
    settings = {row['key']: row['value'] for row in cursor.fetchall()}
    
    return render_template('customer/about.html', settings=settings)


# ==================== CONTACT PAGE ====================

@customer_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact page"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        message = request.form.get('message', '').strip()
        
        if not name or not email or not message:
            flash('Please fill all required fields!', 'danger')
            return redirect(url_for('customer.contact'))
        
        # Save to database
        db = get_db()
        cursor = db.cursor()
        
        # Create contacts table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            INSERT INTO contacts (name, email, phone, message)
            VALUES (?, ?, ?, ?)
        """, (name, email, phone, message))
        
        db.commit()
        
        flash('Your message has been sent! We will contact you soon.', 'success')
        return redirect(url_for('customer.contact'))
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT key, value FROM settings")
    settings = {row['key']: row['value'] for row in cursor.fetchall()}
    
    return render_template('customer/contact.html', settings=settings)


# ==================== USER AUTHENTICATION ====================

@customer_bp.route('/login', methods=['GET', 'POST'])
def user_login():
    """User login page"""
    # If already logged in, redirect to home
    if session.get('user_id'):
        return redirect(url_for('customer.index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ? AND is_active = 1", (email,))
        user = cursor.fetchone()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['full_name']
            session['user_email'] = user['email']
            session['user_phone'] = user['phone']
            
            flash('Login successful!', 'success')
            
            # Redirect to next page or home
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('customer.index'))
        else:
            flash('Invalid email or password!', 'danger')
    
    return render_template('auth/user_login.html')


@customer_bp.route('/register', methods=['GET', 'POST'])
def user_register():
    """User registration page"""
    if session.get('user_id'):
        return redirect(url_for('customer.index'))
    
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        errors = []
        if not full_name:
            errors.append('Full name is required')
        if not email:
            errors.append('Email is required')
        elif not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            errors.append('Invalid email address')
        if not password:
            errors.append('Password is required')
        elif len(password) < 6:
            errors.append('Password must be at least 6 characters')
        if password != confirm_password:
            errors.append('Passwords do not match')
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return redirect(url_for('customer.user_register'))
        
        db = get_db()
        cursor = db.cursor()
        
        # Check if email exists
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            flash('Email already registered!', 'danger')
            return redirect(url_for('customer.user_register'))
        
        # Create user
        password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        cursor.execute("""
            INSERT INTO users (full_name, email, phone, password_hash, is_admin, is_active)
            VALUES (?, ?, ?, ?, 0, 1)
        """, (full_name, email, phone, password_hash))
        
        db.commit()
        user_id = cursor.lastrowid
        
        # Auto login
        session['user_id'] = user_id
        session['user_name'] = full_name
        session['user_email'] = email
        session['user_phone'] = phone
        
        flash('Registration successful! Welcome to Ethiosadat Furniture!', 'success')
        return redirect(url_for('customer.index'))
    
    return render_template('auth/user_register.html')


@customer_bp.route('/logout')
def user_logout():
    """User logout"""
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('user_email', None)
    session.pop('user_phone', None)
    
    flash('Logged out successfully!', 'success')
    return redirect(url_for('customer.index'))


# ==================== USER PROFILE ====================

@customer_bp.route('/profile')
@user_login_required
def user_profile():
    """User profile page"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    user = cursor.fetchone()

    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END) as delivered,
            SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
            SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled,
            SUM(total) as total_spent
        FROM orders WHERE user_id = ?
    """, (session['user_id'],))
    order_stats_row = cursor.fetchone()
    order_stats = dict(order_stats_row) if order_stats_row else {}

    cursor.execute("""
        SELECT * FROM orders
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 20
    """, (session['user_id'],))
    orders_raw = cursor.fetchall()
    orders = [dict(o) for o in orders_raw] if orders_raw else []

    return render_template('auth/user_profile.html', user=user, order_stats=order_stats, orders=orders)


@customer_bp.route('/profile/update', methods=['POST'])
@user_login_required
def update_profile():
    """Update user profile"""
    full_name = request.form.get('full_name', '').strip()
    phone = request.form.get('phone', '').strip()
    address = request.form.get('address', '').strip()
    city = request.form.get('city', '').strip()
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        UPDATE users SET 
            full_name = ?, phone = ?, address = ?, city = ?, 
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (full_name, phone, address, city, session['user_id']))
    
    db.commit()
    
    # Update session
    session['user_name'] = full_name
    session['user_phone'] = phone
    
    flash('Profile updated successfully!', 'success')
    return redirect(url_for('customer.user_profile'))


# ==================== ORDER ROUTES ====================

@customer_bp.route('/orders')
@user_login_required
def user_orders():
    """User order history"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("""
        SELECT * FROM orders 
        WHERE user_id = ? 
        ORDER BY id DESC
    """, (session['user_id'],))
    
    orders = cursor.fetchall()
    
    return render_template('auth/user_orders.html', orders=orders)


@customer_bp.route('/order/<int:order_id>')
@user_login_required
def order_detail(order_id):
    """Order detail page"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM orders WHERE id = ? AND user_id = ?", (order_id, session['user_id']))
    order = cursor.fetchone()
    
    if not order:
        flash('Order not found!', 'danger')
        return redirect(url_for('customer.user_orders'))
    
    # Get order items
    cursor.execute("""
        SELECT oi.*, p.name, p.name_am, p.name_ar, p.thumbnail
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        WHERE oi.order_id = ?
    """, (order_id,))
    
    items = cursor.fetchall()
    
    return render_template('auth/order_detail.html', order=order, items=items)


@customer_bp.route('/order-confirmation/<int:order_id>')
@user_login_required
def order_confirmation(order_id):
    """Order confirmation page after checkout"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM orders WHERE id = ? AND user_id = ?", (order_id, session['user_id']))
    order = cursor.fetchone()
    
    if not order:
        flash('Order not found!', 'danger')
        return redirect(url_for('customer.index'))
    
    # Get order items
    cursor.execute("""
        SELECT oi.*, p.name, p.name_am, p.name_ar, p.thumbnail
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        WHERE oi.order_id = ?
    """, (order_id,))
    
    items = cursor.fetchall()
    
    return render_template('auth/order_confirmation.html', order=order, items=items)


# ==================== ADMIN LOGIN (for reference) ====================

@customer_bp.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page (redirect to admin blueprint)"""
    return redirect(url_for('admin.admin_login'))


# ==================== SEARCH ROUTE ====================

@customer_bp.route('/search')
def search():
    """Search products"""
    query = request.args.get('q', '').strip()
    
    if not query:
        return redirect(url_for('customer.products'))
    
    db = get_db()
    cursor = db.cursor()
    
    search_term = f'%{query}%'
    cursor.execute("""
        SELECT p.*, c.name as category_name 
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.is_active = 1 
        AND (p.name LIKE ? OR p.name_am LIKE ? OR p.name_ar LIKE ?)
        ORDER BY p.id DESC
    """, (search_term, search_term, search_term))
    
    products = cursor.fetchall()
    
    return render_template('customer/search.html', products=products, query=query)


# ==================== FAQ PAGE ====================

@customer_bp.route('/faq')
def faq():
    """Frequently asked questions page"""
    return render_template('customer/faq.html')


# ==================== SHIPPING INFO ====================

@customer_bp.route('/shipping-info')
def shipping_info():
    """Shipping information page"""
    return render_template('customer/shipping_info.html')


# ==================== RETURNS POLICY ====================

@customer_bp.route('/returns')
def returns_policy():
    """Returns policy page"""
    return render_template('customer/returns.html')