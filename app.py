from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, make_response, send_file, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import date, datetime
import os
import base64
import tempfile
from werkzeug.utils import secure_filename
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask import session, g
from datetime import timedelta
import qrcode
from PIL import Image, ImageDraw

from db import db
from models import CatalogPosition

__all__ = ["app", "db"]

def generate_number(prefix_template, last_number_str):
    """Generiert eine neue Nummer basierend auf einem Präfix-Template und der letzten Nummer.
    
    Args:
        prefix_template: Template wie "One-Offer-$id" oder "Firma-Angebot-$id"
        last_number_str: Die letzte verwendete Nummer (z.B. "One-Offer-0042")
    
    Returns:
        Die neue Nummer (z.B. "One-Offer-0043")
    """
    if last_number_str:
        # Extrahiere die Nummer am Ende
        parts = last_number_str.split('-')
        try:
            last_num = int(parts[-1])
            new_num = last_num + 1
        except (ValueError, IndexError):
            new_num = 1
    else:
        new_num = 1
    
    # Ersetze $id durch die neue Nummer mit führenden Nullen
    return prefix_template.replace('$id', f"{new_num:04d}")

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')

db.init_app(app)
migrate = Migrate(app, db)

# Association tables for many-to-many relations
project_offer = db.Table('project_offer',
    db.Column('project_id', db.Integer, db.ForeignKey('project.id'), primary_key=True),
    db.Column('offer_id', db.Integer, db.ForeignKey('offer.id'), primary_key=True)
)

project_invoice = db.Table('project_invoice',
    db.Column('project_id', db.Integer, db.ForeignKey('project.id'), primary_key=True),
    db.Column('invoice_id', db.Integer, db.ForeignKey('invoice.id'), primary_key=True)
)

# Models
class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_type = db.Column(db.String(16), nullable=False, default='firma')  # 'firma' oder 'privat'
    # Firmenkunde
    name = db.Column(db.String(128))  # Firmenname
    contact_person = db.Column(db.String(128))
    contact_phone = db.Column(db.String(32))
    contact_email = db.Column(db.String(128))
    # Privatkunde
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    # Gemeinsame Felder (für beide Typen, auch Privatkunden)
    email = db.Column(db.String(128))
    phone = db.Column(db.String(32))
    street = db.Column(db.String(128))
    house_number = db.Column(db.String(16))
    postal_code = db.Column(db.String(16))
    city = db.Column(db.String(64))
    country = db.Column(db.String(64))
    notes = db.Column(db.Text)
    offers = db.relationship('Offer', backref='customer', lazy=True)
    invoices = db.relationship('Invoice', backref='customer', lazy=True)

class Offer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    offer_number = db.Column(db.String(32), unique=True, nullable=False)
    title = db.Column(db.String(128), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    total_gross = db.Column(db.Float, nullable=False)
    total_net = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)  # Angebotsdatum
    valid_until = db.Column(db.Date)  # Gültig bis
    status = db.Column(db.String(32), default='offen')  # Status: offen, angenommen, abgelehnt, abgelaufen
    notes = db.Column(db.Text)  # Interne Notizen
    positions = db.relationship('OfferPosition', backref='offer', lazy=True, cascade="all, delete-orphan")

class OfferPosition(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    offer_id = db.Column(db.Integer, db.ForeignKey('offer.id'), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    gross = db.Column(db.Float, nullable=False)
    vat = db.Column(db.Float, nullable=False, default=20.0)
    net = db.Column(db.Float, nullable=False)

class InvoicePosition(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    gross = db.Column(db.Float, nullable=False)
    vat = db.Column(db.Float, nullable=False, default=20.0)
    net = db.Column(db.Float, nullable=False)

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(32), unique=True, nullable=False)
    title = db.Column(db.String(128), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    total_gross = db.Column(db.Float, nullable=False)
    total_net = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date)
    status = db.Column(db.String(32), default='offen')
    notes = db.Column(db.Text)
    positions = db.relationship('InvoicePosition', backref='invoice', lazy=True, cascade="all, delete-orphan")

class CompanySettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    street = db.Column(db.String(128))
    house_number = db.Column(db.String(16))
    postal_code = db.Column(db.String(16))
    city = db.Column(db.String(64))
    country = db.Column(db.String(64))
    uid = db.Column(db.String(32))  # UID-Nummer
    firmenbuchnummer = db.Column(db.String(32))
    wirtschaftskammer = db.Column(db.String(128))
    iban = db.Column(db.String(64))
    bic = db.Column(db.String(32))
    bank = db.Column(db.String(128))
    logo_filename = db.Column(db.String(256))
    email = db.Column(db.String(128))
    phone = db.Column(db.String(32))
    website = db.Column(db.String(128))
    notes = db.Column(db.Text)
    # Nummernpräfixe für Angebote und Rechnungen
    offer_number_prefix = db.Column(db.String(32), default="One-Offer-$id")
    invoice_number_prefix = db.Column(db.String(32), default="One-Inv-$id")
    
    # PDF Template Farben
    primary_color = db.Column(db.String(7), default="#667eea")     # Hauptfarbe für Akzente
    secondary_color = db.Column(db.String(7), default="#764ba2")   # Sekundärfarbe
    accent_color = db.Column(db.String(7), default="#4299e1")      # Akzentfarbe für wichtige Elemente
    text_color = db.Column(db.String(7), default="#2d3748")        # Haupttextfarbe

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    date = db.Column(db.Date, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    categories = db.Column(db.String(128), nullable=False)  # CSV: z.B. "Foto,Video"
    offers = db.relationship('Offer', secondary=project_offer, backref=db.backref('projects', lazy='dynamic'))
    invoices = db.relationship('Invoice', secondary=project_invoice, backref=db.backref('projects', lazy='dynamic'))
    customer = db.relationship('Customer')

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(32), default='user')  # z.B. 'admin', 'user'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class PdfTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)  # z.B. "Angebot", "Rechnung"
    content = db.Column(db.Text, nullable=False)

# Set user context for all requests and enforce authentication
@app.before_request
def load_user():
    # Skip authentication for login route and static files
    if request.endpoint and (request.endpoint == 'login' or request.endpoint.startswith('static')):
        return
    
    user_id = session.get('user_id')
    token_expiry = session.get('token_expiry')
    
    if user_id and token_expiry:
        try:
            # Check if token is still valid
            if datetime.utcnow() <= datetime.fromisoformat(token_expiry):
                g.user = User.query.get(user_id)
                if g.user:
                    return  # User is authenticated, continue
            else:
                # Token expired, clear session
                session.clear()
                flash('Session abgelaufen. Bitte erneut anmelden.', 'warning')
        except:
            session.clear()
    
    # No valid session - redirect to login
    g.user = None
    return redirect(url_for('login'))

# Login-Required Decorator

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        token_expiry = session.get('token_expiry')
        if not user_id or not token_expiry:
            return redirect(url_for('login'))
        if datetime.utcnow() > datetime.fromisoformat(token_expiry):
            session.clear()
            flash('Session abgelaufen. Bitte erneut anmelden.', 'warning')
            return redirect(url_for('login'))
        g.user = User.query.get(user_id)
        return f(*args, **kwargs)
    return decorated_function

# --- Admin-Only Decorator ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('login'))
        user = User.query.get(user_id)
        if not user or user.role != 'admin':
            flash('Nur für Admins zugänglich.', 'danger')
            return redirect(url_for('index'))
        g.user = user
        return f(*args, **kwargs)
    return decorated_function

# ===== AUTHENTICATION ROUTES =====

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            # Set session with expiry (24 hours)
            session['user_id'] = user.id
            session['token_expiry'] = (datetime.utcnow() + timedelta(hours=24)).isoformat()
            flash(f'Willkommen, {user.username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Ungültiger Benutzername oder Passwort.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Sie wurden erfolgreich abgemeldet.', 'info')
    return redirect(url_for('login'))

# Debug Routes
@app.route('/debug-qr')
def debug_qr():
    return send_from_directory('.', 'debug_qr.html')

# ===== MAIN ROUTES =====

@app.route('/')
def index():
    # Dashboard-Statistiken sammeln
    total_customers = Customer.query.count()
    total_offers = Offer.query.count()
    total_invoices = Invoice.query.count()
    total_projects = Project.query.count()
    
    # Letzte Aktivitäten
    recent_offers = Offer.query.order_by(Offer.date.desc()).limit(5).all()
    recent_invoices = Invoice.query.order_by(Invoice.date.desc()).limit(5).all()
    recent_projects = Project.query.order_by(Project.date.desc()).limit(5).all()
    
    # Angebote nach Status
    offers_open = Offer.query.filter_by(status='offen').count()
    offers_accepted = Offer.query.filter_by(status='angenommen').count()
    offers_rejected = Offer.query.filter_by(status='abgelehnt').count()
    offers_expired = Offer.query.filter_by(status='abgelaufen').count()
    
    # Rechnungen nach Status
    invoices_open = Invoice.query.filter_by(status='offen').count()
    invoices_paid = Invoice.query.filter_by(status='bezahlt').count()
    invoices_overdue = Invoice.query.filter_by(status='überfällig').count()
    
    # Umsatz-Statistiken
    total_offer_value = sum([offer.total_gross for offer in Offer.query.all()])
    total_invoice_value = sum([invoice.total_gross for invoice in Invoice.query.all()])
    paid_invoice_value = sum([invoice.total_gross for invoice in Invoice.query.filter_by(status='bezahlt').all()])
    
    # Zahlungsfortschritt berechnen
    payment_percentage = (paid_invoice_value / total_invoice_value * 100) if total_invoice_value > 0 else 0
    
    return render_template('index.html', 
                         total_customers=total_customers,
                         total_offers=total_offers,
                         total_invoices=total_invoices,
                         total_projects=total_projects,
                         recent_offers=recent_offers,
                         recent_invoices=recent_invoices,
                         recent_projects=recent_projects,
                         offers_open=offers_open,
                         offers_accepted=offers_accepted,
                         offers_rejected=offers_rejected,
                         offers_expired=offers_expired,
                         invoices_open=invoices_open,
                         invoices_paid=invoices_paid,
                         invoices_overdue=invoices_overdue,
                         total_offer_value=total_offer_value,
                         total_invoice_value=total_invoice_value,
                         paid_invoice_value=paid_invoice_value,
                         payment_percentage=payment_percentage)

@app.route('/qr-test')
def qr_test():
    """Test-Route für QR-Code Funktionalität"""
    return render_template('qr_test.html')

@app.route('/customers')
def customers():
    all_customers = Customer.query.all()
    return render_template('customers.html', customers=all_customers)

@app.route('/customers/new', methods=['GET', 'POST'])
def new_customer():
    if request.method == 'POST':
        customer_type = request.form['customer_type']
        if customer_type == 'firma':
            name = request.form['name']
            contact_person = request.form['contact_person']
            contact_phone = request.form['contact_phone']
            contact_email = request.form['contact_email']
            first_name = None
            last_name = None
        else:
            name = None
            contact_person = None
            contact_phone = None
            contact_email = None
            first_name = request.form['first_name']
            last_name = request.form['last_name']
        email = request.form['email']
        phone = request.form['phone']
        street = request.form['street']
        house_number = request.form['house_number']
        postal_code = request.form['postal_code']
        city = request.form['city']
        country = request.form['country']
        notes = request.form['notes']
        customer = Customer(
            customer_type=customer_type,
            name=name,
            contact_person=contact_person,
            contact_phone=contact_phone,
            contact_email=contact_email,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            street=street,
            house_number=house_number,
            postal_code=postal_code,
            city=city,
            country=country,
            notes=notes
        )
        db.session.add(customer)
        db.session.commit()
        return redirect(url_for('customers'))
    return render_template('customer_form.html')

@app.route('/customers/<int:id>/edit', methods=['GET', 'POST'])
def edit_customer(id):
    customer = Customer.query.get_or_404(id)
    if request.method == 'POST':
        customer_type = request.form['customer_type']
        customer.customer_type = customer_type
        if customer_type == 'firma':
            customer.name = request.form['name']
            customer.contact_person = request.form['contact_person']
            customer.contact_phone = request.form['contact_phone']
            customer.contact_email = request.form['contact_email']
            customer.first_name = None
            customer.last_name = None
        else:
            customer.name = None
            customer.contact_person = None
            customer.contact_phone = None
            customer.contact_email = None
            customer.first_name = request.form['first_name']
            customer.last_name = request.form['last_name']
        customer.email = request.form['email']
        customer.phone = request.form['phone']
        customer.street = request.form['street']
        customer.house_number = request.form['house_number']
        customer.postal_code = request.form['postal_code']
        customer.city = request.form['city']
        customer.country = request.form['country']
        customer.notes = request.form['notes']
        db.session.commit()
        return redirect(url_for('customers'))
    return render_template('customer_form.html', customer=customer)

@app.route('/customers/<int:id>/delete')
def delete_customer(id):
    customer = Customer.query.get_or_404(id)
    # Prüfe, ob noch Rechnungen oder Angebote existieren
    if customer.invoices and len(customer.invoices) > 0:
        flash('Kunde kann nicht gelöscht werden: Es existieren noch Rechnungen für diesen Kunden.', 'danger')
        return redirect(url_for('customers'))
    if customer.offers and len(customer.offers) > 0:
        flash('Kunde kann nicht gelöscht werden: Es existieren noch Angebote für diesen Kunden.', 'danger')
        return redirect(url_for('customers'))
    db.session.delete(customer)
    db.session.commit()
    flash('Kunde wurde gelöscht.', 'success')
    return redirect(url_for('customers'))

@app.route('/offers')
def offers():
    all_offers = Offer.query.all()
    return render_template('offers.html', offers=all_offers)

@app.route('/offers/new', methods=['GET', 'POST'])
def new_offer():
    from models import CatalogPosition
    catalog_positions = CatalogPosition.query.all()
    customers = Customer.query.all()
    if request.method == 'POST':
        # Angebotsnummer generieren basierend auf Firmeneinstellungen
        company_settings = CompanySettings.query.first()
        offer_prefix = company_settings.offer_number_prefix if company_settings and company_settings.offer_number_prefix else "One-Offer-$id"
        
        last_offer = Offer.query.order_by(Offer.id.desc()).first()
        last_number_str = last_offer.offer_number if last_offer else None
        offer_number = generate_number(offer_prefix, last_number_str)
        title = request.form['title']
        customer_id = request.form['customer_id']
        offer_date = datetime.strptime(request.form['date'], "%Y-%m-%d").date()
        valid_until = request.form.get('valid_until')
        if valid_until:
            valid_until = datetime.strptime(valid_until, "%Y-%m-%d").date()
        else:
            valid_until = None
        status = request.form.get('status', 'offen')
        notes = request.form.get('notes')
        positions = []
        total_gross = 0
        total_net = 0
        for key in request.form:
            if key.startswith('positions[') and key.endswith('][name]'):
                idx = key.split('[')[1].split(']')[0]
                name = request.form[f'positions[{idx}][name]']
                quantity = float(request.form.get(f'positions[{idx}][quantity]', 1))
                gross = float(request.form.get(f'positions[{idx}][gross]', 0))
                vat = float(request.form.get(f'positions[{idx}][vat]', 20))
                net = gross / (1 + vat/100)
                positions.append(OfferPosition(name=name, quantity=quantity, gross=gross, vat=vat, net=net))
                total_gross += gross * quantity
                total_net += net * quantity
        offer = Offer(
            offer_number=offer_number,
            title=title,
            customer_id=customer_id,
            total_gross=total_gross,
            total_net=total_net,
            date=offer_date,
            valid_until=valid_until,
            status=status,
            notes=notes
        )
        db.session.add(offer)
        db.session.flush()  # offer.id verfügbar machen
        for pos in positions:
            pos.offer_id = offer.id
            db.session.add(pos)
        db.session.commit()
        return redirect(url_for('offers'))
    today = date.today().isoformat()
    catalog_positions_dicts = [
        {
            'id': pos.id,
            'name': pos.name,
            'description': pos.description,
            'unit': pos.unit,
            'price': pos.price,
            'vat': pos.vat
        } for pos in catalog_positions
    ]
    return render_template('offer_form.html', customers=customers, offer=None, today=today, catalog_positions=catalog_positions_dicts)

@app.route('/offers/<int:offer_id>/print')
def print_offer(offer_id):
    offer = Offer.query.get_or_404(offer_id)
    company = CompanySettings.query.first()
    # Versuche, das Angebot-Template aus der DB zu laden
    template = PdfTemplate.query.filter_by(name="Angebot").first()
    if template:
        # Template aus DB als Jinja2-Template rendern
        from flask import render_template_string
        return render_template_string(template.content, offer=offer, company=company)
    # Fallback: statisches Template
    return render_template('offer_print.html', offer=offer, company=company)

@app.route('/invoices')
def invoices():
    all_invoices = Invoice.query.all()
    return render_template('invoices.html', invoices=all_invoices)

@app.route('/invoices/new', methods=['GET', 'POST'])
def new_invoice():
    from models import CatalogPosition
    catalog_positions = CatalogPosition.query.all()
    customers = Customer.query.all()
    if request.method == 'POST':
        # Rechnungsnummer generieren basierend auf Firmeneinstellungen
        company_settings = CompanySettings.query.first()
        invoice_prefix = company_settings.invoice_number_prefix if company_settings and company_settings.invoice_number_prefix else "One-Inv-$id"
        
        last_invoice = Invoice.query.order_by(Invoice.id.desc()).first()
        last_number_str = last_invoice.invoice_number if last_invoice else None
        invoice_number = generate_number(invoice_prefix, last_number_str)
        
        title = request.form['title']
        customer_id = request.form['customer_id']
        invoice_date = datetime.strptime(request.form['date'], "%Y-%m-%d").date()
        due_date = request.form.get('due_date')
        if due_date:
            due_date = datetime.strptime(due_date, "%Y-%m-%d").date()
        else:
            due_date = None
        status = request.form.get('status', 'offen')
        notes = request.form.get('notes')
        
        positions = []
        total_gross = 0
        total_net = 0
        for key in request.form:
            if key.startswith('positions[') and key.endswith('][name]'):
                idx = key.split('[')[1].split(']')[0]
                name = request.form[f'positions[{idx}][name]']
                quantity = float(request.form.get(f'positions[{idx}][quantity]', 1))
                gross = float(request.form.get(f'positions[{idx}][gross]', 0))
                vat = float(request.form.get(f'positions[{idx}][vat]', 20))
                net = gross / (1 + vat/100)
                positions.append(InvoicePosition(name=name, quantity=quantity, gross=gross, vat=vat, net=net))
                total_gross += gross * quantity
                total_net += net * quantity
        
        invoice = Invoice(
            invoice_number=invoice_number,
            title=title,
            customer_id=customer_id,
            total_gross=total_gross,
            total_net=total_net,
            date=invoice_date,
            due_date=due_date,
            status=status,
            notes=notes
        )
        db.session.add(invoice)
        db.session.flush()  # invoice.id verfügbar machen
        for pos in positions:
            pos.invoice_id = invoice.id
            db.session.add(pos)
        db.session.commit()
        return redirect(url_for('invoices'))
    
    today = date.today().isoformat()
    catalog_positions_dicts = [
        {
            'id': pos.id,
            'name': pos.name,
            'description': pos.description,
            'unit': pos.unit,
            'price': pos.price,
            'vat': pos.vat
        } for pos in catalog_positions
    ]
    return render_template('invoice_form.html', customers=customers, invoice=None, today=today, catalog_positions=catalog_positions_dicts)

@app.route('/invoices/<int:invoice_id>/print')
def print_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    company = CompanySettings.query.first()
    # Versuche, das Rechnung-Template aus der DB zu laden
    template = PdfTemplate.query.filter_by(name="Rechnung").first()
    if template:
        # Template aus DB als Jinja2-Template rendern
        from flask import render_template_string
        return render_template_string(template.content, invoice=invoice, company=company)
    # Fallback: streamlined Template verwenden
    return render_template('invoice_template_streamlined.html', invoice=invoice, company=company)

@app.route('/invoices/<int:invoice_id>/edit', methods=['GET', 'POST'])
def edit_invoice(invoice_id):
    from models import CatalogPosition
    invoice = Invoice.query.get_or_404(invoice_id)
    catalog_positions = CatalogPosition.query.all()
    customers = Customer.query.all()
    if request.method == 'POST':
        invoice.title = request.form['title']
        invoice.customer_id = request.form['customer_id']
        invoice.date = datetime.strptime(request.form['date'], "%Y-%m-%d").date()
        due_date = request.form.get('due_date')
        if due_date:
            invoice.due_date = datetime.strptime(due_date, "%Y-%m-%d").date()
        else:
            invoice.due_date = None
        invoice.status = request.form.get('status', 'offen')
        invoice.notes = request.form.get('notes')
        
        # Alte Positionen löschen
        for pos in invoice.positions:
            db.session.delete(pos)
        
        # Neue Positionen hinzufügen
        positions = []
        total_gross = 0
        total_net = 0
        for key in request.form:
            if key.startswith('positions[') and key.endswith('][name]'):
                idx = key.split('[')[1].split(']')[0]
                name = request.form[f'positions[{idx}][name]']
                quantity = float(request.form.get(f'positions[{idx}][quantity]', 1))
                gross = float(request.form.get(f'positions[{idx}][gross]', 0))
                vat = float(request.form.get(f'positions[{idx}][vat]', 20))
                net = gross / (1 + vat/100)
                positions.append(InvoicePosition(name=name, quantity=quantity, gross=gross, vat=vat, net=net, invoice_id=invoice.id))
                total_gross += gross * quantity
                total_net += net * quantity
        
        invoice.total_gross = total_gross
        invoice.total_net = total_net
        
        for pos in positions:
            db.session.add(pos)
        
        db.session.commit()
        return redirect(url_for('invoices'))
    
    catalog_positions_dicts = [
        {
            'id': pos.id,
            'name': pos.name,
            'description': pos.description,
            'unit': pos.unit,
            'price': pos.price,
            'vat': pos.vat
        } for pos in catalog_positions
    ]
    return render_template('invoice_form.html', customers=customers, invoice=invoice, catalog_positions=catalog_positions_dicts)

@app.route('/invoices/<int:invoice_id>/delete')
def delete_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    db.session.delete(invoice)
    db.session.commit()
    flash('Rechnung wurde gelöscht.', 'success')
    return redirect(url_for('invoices'))

# Offer Edit/Delete Routes
@app.route('/offers/<int:offer_id>/edit', methods=['GET', 'POST'])
def edit_offer(offer_id):
    from models import CatalogPosition
    offer = Offer.query.get_or_404(offer_id)
    catalog_positions = CatalogPosition.query.all()
    customers = Customer.query.all()
    if request.method == 'POST':
        offer.title = request.form['title']
        offer.customer_id = request.form['customer_id']
        offer.date = datetime.strptime(request.form['date'], "%Y-%m-%d").date()
        valid_until = request.form.get('valid_until')
        if valid_until:
            offer.valid_until = datetime.strptime(valid_until, "%Y-%m-%d").date()
        else:
            offer.valid_until = None
        offer.status = request.form.get('status', 'offen')
        offer.notes = request.form.get('notes')
        
        # Alte Positionen löschen
        for pos in offer.positions:
            db.session.delete(pos)
        
        # Neue Positionen hinzufügen
        positions = []
        total_gross = 0
        total_net = 0
        for key in request.form:
            if key.startswith('positions[') and key.endswith('][name]'):
                idx = key.split('[')[1].split(']')[0]
                name = request.form[f'positions[{idx}][name]']
                quantity = float(request.form.get(f'positions[{idx}][quantity]', 1))
                gross = float(request.form.get(f'positions[{idx}][gross]', 0))
                vat = float(request.form.get(f'positions[{idx}][vat]', 20))
                net = gross / (1 + vat/100)
                positions.append(OfferPosition(name=name, quantity=quantity, gross=gross, vat=vat, net=net, offer_id=offer.id))
                total_gross += gross * quantity
                total_net += net * quantity
        
        offer.total_gross = total_gross
        offer.total_net = total_net
        
        for pos in positions:
            db.session.add(pos)
        
        db.session.commit()
        return redirect(url_for('offers'))
    
    catalog_positions_dicts = [
        {
            'id': pos.id,
            'name': pos.name,
            'description': pos.description,
            'unit': pos.unit,
            'price': pos.price,
            'vat': pos.vat
        } for pos in catalog_positions
    ]
    return render_template('offer_form.html', customers=customers, offer=offer, catalog_positions=catalog_positions_dicts)

@app.route('/offers/<int:offer_id>/delete')
def delete_offer(offer_id):
    offer = Offer.query.get_or_404(offer_id)
    db.session.delete(offer)
    db.session.commit()
    flash('Angebot wurde gelöscht.', 'success')
    return redirect(url_for('offers'))

# Project Routes
@app.route('/projects')
def projects():
    all_projects = Project.query.all()
    return render_template('projects.html', projects=all_projects)

@app.route('/projects/new', methods=['GET', 'POST'])
def new_project():
    customers = Customer.query.all()
    if request.method == 'POST':
        name = request.form['name']
        customer_id = request.form['customer_id']
        project_date = datetime.strptime(request.form['date'], "%Y-%m-%d").date()
        categories = request.form['categories']
        
        project = Project(
            name=name,
            customer_id=customer_id,
            date=project_date,
            categories=categories
        )
        db.session.add(project)
        db.session.commit()
        return redirect(url_for('projects'))
    
    today = date.today().isoformat()
    return render_template('project_form.html', customers=customers, project=None, today=today)

@app.route('/projects/<int:project_id>')
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    return render_template('project_detail.html', project=project)

@app.route('/projects/<int:project_id>/edit', methods=['GET', 'POST'])
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)
    customers = Customer.query.all()
    if request.method == 'POST':
        project.name = request.form['name']
        project.customer_id = request.form['customer_id']
        project.date = datetime.strptime(request.form['date'], "%Y-%m-%d").date()
        project.categories = request.form['categories']
        db.session.commit()
        return redirect(url_for('projects'))
    
    return render_template('project_form.html', customers=customers, project=project)

@app.route('/projects/<int:project_id>/delete')
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    flash('Projekt wurde gelöscht.', 'success')
    return redirect(url_for('projects'))

# Company Settings
@app.route('/company-settings', methods=['GET', 'POST'])
def company_settings():
    settings = CompanySettings.query.first()
    if not settings:
        settings = CompanySettings()
        db.session.add(settings)
        db.session.commit()
    
    if request.method == 'POST':
        settings.name = request.form.get('name')
        settings.street = request.form.get('street')
        settings.house_number = request.form.get('house_number')
        settings.postal_code = request.form.get('postal_code')
        settings.city = request.form.get('city')
        settings.country = request.form.get('country')
        settings.uid = request.form.get('uid')
        settings.firmenbuchnummer = request.form.get('firmenbuchnummer')
        settings.wirtschaftskammer = request.form.get('wirtschaftskammer')
        settings.iban = request.form.get('iban')
        settings.bic = request.form.get('bic')
        settings.bank = request.form.get('bank')
        settings.email = request.form.get('email')
        settings.phone = request.form.get('phone')
        settings.website = request.form.get('website')
        settings.notes = request.form.get('notes')
        settings.offer_number_prefix = request.form.get('offer_number_prefix', 'One-Offer-$id')
        settings.invoice_number_prefix = request.form.get('invoice_number_prefix', 'One-Inv-$id')
        
        # PDF Template Farben
        settings.primary_color = request.form.get('primary_color', '#667eea')
        settings.secondary_color = request.form.get('secondary_color', '#764ba2')
        settings.accent_color = request.form.get('accent_color', '#4299e1')
        settings.text_color = request.form.get('text_color', '#2d3748')
        
        # Logo-Upload
        if 'logo' in request.files:
            logo_file = request.files['logo']
            if logo_file and logo_file.filename:
                filename = secure_filename(logo_file.filename)
                logo_path = os.path.join(app.instance_path, filename)
                logo_file.save(logo_path)
                settings.logo_filename = filename
        
        db.session.commit()
        flash('Firmeneinstellungen wurden gespeichert.', 'success')
        return redirect(url_for('company_settings'))
    
    return render_template('company_settings.html', settings=settings)

# Positions/Catalog
@app.route('/positions')
def positions():
    all_positions = CatalogPosition.query.all()
    return render_template('positions.html', positions=all_positions)

@app.route('/positions/new', methods=['GET', 'POST'])
def new_position():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description')
        unit = request.form.get('unit', 'Stk.')
        price = float(request.form['price'])
        vat = float(request.form.get('vat', 20.0))
        
        position = CatalogPosition(
            name=name,
            description=description,
            unit=unit,
            price=price,
            vat=vat
        )
        db.session.add(position)
        db.session.commit()
        flash('Position wurde hinzugefügt.', 'success')
        return redirect(url_for('positions'))
    
    return render_template('position_form.html')

@app.route('/positions/<int:position_id>/edit', methods=['GET', 'POST'])
def edit_position(position_id):
    position = CatalogPosition.query.get_or_404(position_id)
    if request.method == 'POST':
        position.name = request.form['name']
        position.description = request.form.get('description')
        position.unit = request.form.get('unit', 'Stk.')
        position.price = float(request.form['price'])
        position.vat = float(request.form.get('vat', 20.0))
        db.session.commit()
        flash('Position wurde aktualisiert.', 'success')
        return redirect(url_for('positions'))
    
    return render_template('position_form.html', position=position)

@app.route('/positions/<int:position_id>/delete')
def delete_position(position_id):
    position = CatalogPosition.query.get_or_404(position_id)
    db.session.delete(position)
    db.session.commit()
    flash('Position wurde gelöscht.', 'success')
    return redirect(url_for('positions'))

# Instance files (for logo uploads)
@app.route('/instance/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.instance_path, filename)

# ===== ADMIN ROUTES =====

@app.route('/users')
@admin_required
def users():
    all_users = User.query.all()
    return render_template('users.html', users=all_users)

@app.route('/users/new', methods=['GET', 'POST'])
@admin_required
def new_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            flash('Benutzername bereits vorhanden.', 'error')
            return render_template('user_form.html')
        
        user = User(username=username, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Benutzer wurde erstellt.', 'success')
        return redirect(url_for('users'))
    
    return render_template('user_form.html')

@app.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user.role = request.form['role']
        password = request.form.get('password')
        if password:
            user.set_password(password)
        db.session.commit()
        flash('Benutzer wurde aktualisiert.', 'success')
        return redirect(url_for('users'))
    
    return render_template('user_form.html', user=user)

@app.route('/users/<int:user_id>/delete')
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == g.user.id:
        flash('Sie können sich nicht selbst löschen.', 'error')
        return redirect(url_for('users'))
    
    db.session.delete(user)
    db.session.commit()
    flash('Benutzer wurde gelöscht.', 'success')
    return redirect(url_for('users'))

@app.route('/templates')
@admin_required
def templates():
    all_templates = PdfTemplate.query.all()
    return render_template('templates.html', templates=all_templates)

@app.route('/templates/<int:template_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_template(template_id):
    template = PdfTemplate.query.get_or_404(template_id)
    if request.method == 'POST':
        template.content = request.form['content']
        db.session.commit()
        flash('Template wurde aktualisiert.', 'success')
        return redirect(url_for('templates'))
    
    return render_template('edit_template.html', template=template)

# ===== END ADMIN ROUTES =====

@app.route('/dynamic-colors.css')
def dynamic_colors_css():
    """Dynamische CSS-Datei mit benutzerdefinierten Farben aus den Company Settings"""
    company = CompanySettings.query.first()
    
    # Standardfarben als Fallback
    primary_color = company.primary_color if company and company.primary_color else '#667eea'
    secondary_color = company.secondary_color if company and company.secondary_color else '#764ba2'
    accent_color = company.accent_color if company and company.accent_color else '#4299e1'
    text_color = company.text_color if company and company.text_color else '#2d3748'
    
    css_content = f"""
:root {{
   --primary-color: {primary_color};
   --secondary-color: {secondary_color};
   --accent-color: {accent_color};
   --text-color: {text_color};
   
   /* Dynamische Verläufe basierend auf benutzerdefinierten Farben */
   --primary-gradient: linear-gradient(135deg, {primary_color} 0%, {secondary_color} 100%);
   --accent-gradient: linear-gradient(135deg, {accent_color} 0%, {primary_color} 100%);
   --success-gradient: linear-gradient(135deg, {accent_color} 0%, {secondary_color} 100%);
}}

/* Screen Styles Override */
@media screen {{
   body.pdf-template {{
      background: var(--primary-gradient) !important;
   }}

   .document-header {{
      background: var(--text-color) !important;
   }}

   .document-header::before {{
      background: var(--primary-gradient) !important;
   }}

   .info-card::before {{
      background: var(--primary-gradient) !important;
   }}

   .info-card.customer-card::before {{
      background: var(--accent-gradient) !important;
   }}

   .meta-section {{
      background: var(--primary-gradient) !important;
   }}

   .modern-table thead {{
      background: var(--primary-gradient) !important;
   }}

   .summary-total {{
      background: var(--primary-gradient) !important;
   }}

   .signatures-section {{
      background-image: linear-gradient(white, white), var(--success-gradient) !important;
   }}

   .notes-section {{
      border-image: var(--accent-gradient) 1 !important;
   }}

   .download-btn {{
      background: var(--success-gradient) !important;
   }}

   .status-offen {{
      background: linear-gradient(135deg, #ffecd2 0%, {accent_color} 100%) !important;
      color: {text_color} !important;
   }}

   .status-angenommen, .status-bezahlt {{
      background: var(--success-gradient) !important;
   }}

   .status-abgelehnt, .status-überfällig {{
      background: var(--accent-gradient) !important;
   }}
}}

/* Print Styles Override */
@media print {{
   .document-header {{
      background: var(--primary-gradient) !important;
   }}

   .info-card::before {{
      background: var(--primary-gradient) !important;
   }}

   .info-card.customer-card::before {{
      background: var(--accent-gradient) !important;
   }}

   .meta-section {{
      background: var(--primary-gradient) !important;
   }}

   .modern-table thead {{
      background: var(--primary-gradient) !important;
   }}

   .summary-total {{
      background: var(--primary-gradient) !important;
   }}

   .footer-section {{
      background: {text_color} !important;
   }}

   .signatures-section {{
      border: 2px solid {accent_color} !important;
   }}

   .notes-section {{
      border-left: 3px solid {accent_color} !important;
   }}
}}
"""
    
    response = app.response_class(css_content, mimetype='text/css')
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# ===== QR-CODE GENERATOR =====

@app.route('/qr-generator')
@login_required
def qr_generator():
    """QR-Code Generator Seite"""
    company = CompanySettings.query.first()
    return render_template('qr_generator.html', company=company)

@app.route('/qr-generator/generate', methods=['POST'])
@login_required
def generate_qr_code():
    """QR-Code generieren und als Base64 zurückgeben"""
    try:
        url = request.form.get('url')
        include_logo = 'include_logo' in request.form
        qr_color = request.form.get('qr_color', '#000000')
        size = int(request.form.get('size', 400))
        
        if not url:
            return jsonify({'success': False, 'error': 'URL ist erforderlich'})
        
        # QR-Code erstellen
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H if include_logo else qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        # QR-Code als PIL Image erstellen mit transparentem Hintergrund
        qr_img = qr.make_image(fill_color=qr_color, back_color='white')
        qr_img = qr_img.convert("RGBA")
        
        # Weißen Hintergrund durch Transparenz ersetzen
        data = qr_img.getdata()
        new_data = []
        for item in data:
            # Weiße oder fast weiße Pixel werden transparent
            if item[0] >= 250 and item[1] >= 250 and item[2] >= 250:
                new_data.append((255, 255, 255, 0))  # Komplett transparent
            else:
                # QR-Code Pixel mit voller Deckkraft beibehalten
                new_data.append((item[0], item[1], item[2], 255))
        qr_img.putdata(new_data)
        
        # Logo hinzufügen wenn gewünscht
        if include_logo:
            company = CompanySettings.query.first()
            if company and company.logo_filename:
                logo_path = os.path.join(app.instance_path, company.logo_filename)
                if os.path.exists(logo_path):
                    try:
                        logo = Image.open(logo_path)
                        
                        # Sicherheitscheck für Bildgröße
                        max_logo_size = 500  # Maximale Logo-Größe in Pixeln
                        if logo.size[0] > max_logo_size or logo.size[1] > max_logo_size:
                            # Logo verkleinern falls es zu groß ist
                            logo.thumbnail((max_logo_size, max_logo_size), Image.Resampling.LANCZOS)
                        
                        logo = logo.convert("RGBA")
                        
                        # Logo-Größe berechnen, dabei Proportionen beibehalten
                        # Maximale Größe: etwa 1/4 der QR-Code-Größe
                        max_logo_dimension = min(qr_img.size) // 4
                        
                        # Logo proportional skalieren
                        logo_width, logo_height = logo.size
                        if logo_width > logo_height:
                            # Breiteres Logo: Breite auf max_logo_dimension setzen
                            new_width = max_logo_dimension
                            new_height = int((logo_height * new_width) / logo_width)
                        else:
                            # Höheres oder quadratisches Logo: Höhe auf max_logo_dimension setzen
                            new_height = max_logo_dimension
                            new_width = int((logo_width * new_height) / logo_height)
                        
                        logo = logo.resize((new_width, new_height), Image.Resampling.LANCZOS)
                        
                        # QR-Code-Zentrum berechnen
                        qr_center = (qr_img.size[0] // 2, qr_img.size[1] // 2)
                        
                        # Rechteckigen Bereich für Logo freiräumen (mit Rand)
                        margin = 15  # Rand um das Logo
                        clear_width = new_width + (margin * 2)
                        clear_height = new_height + (margin * 2)
                        
                        # Bereich im QR-Code transparent machen (rechteckig)
                        qr_data = list(qr_img.getdata())
                        qr_width, qr_height = qr_img.size
                        
                        clear_left = qr_center[0] - clear_width // 2
                        clear_right = qr_center[0] + clear_width // 2
                        clear_top = qr_center[1] - clear_height // 2
                        clear_bottom = qr_center[1] + clear_height // 2
                        
                        for y in range(qr_height):
                            for x in range(qr_width):
                                # Prüfen ob Pixel im rechteckigen Logo-Bereich liegt
                                if (clear_left <= x <= clear_right and 
                                    clear_top <= y <= clear_bottom):
                                    # Pixel im Logo-Bereich transparent machen
                                    index = y * qr_width + x
                                    qr_data[index] = (255, 255, 255, 0)  # Transparent
                        
                        # Modifizierte Daten zurück ins Bild setzen
                        qr_img.putdata(qr_data)
                        
                        # Logo direkt ohne Hintergrund einfügen
                        # Nur einen subtilen Schatten/Kontur hinzufügen falls nötig
                        
                        # Logo-Position berechnen
                        logo_pos = (qr_center[0] - new_width // 2, qr_center[1] - new_height // 2)
                        
                        # Prüfen ob das Logo bereits einen guten Kontrast hat
                        # Wenn das Logo sehr hell ist, fügen wir einen subtilen Schatten hinzu
                        logo_array = list(logo.getdata())
                        avg_brightness = sum(sum(pixel[:3]) for pixel in logo_array if len(pixel) >= 3) / (len(logo_array) * 3)
                        
                        if avg_brightness > 200:  # Helles Logo - subtiler Schatten
                            # Schatten-Layer erstellen
                            shadow = Image.new('RGBA', (new_width + 4, new_height + 4), (0, 0, 0, 0))
                            shadow_draw = ImageDraw.Draw(shadow)
                            
                            # Sehr subtiler schwarzer Schatten
                            for offset_x in range(-1, 2):
                                for offset_y in range(-1, 2):
                                    if offset_x != 0 or offset_y != 0:
                                        shadow.paste(logo, (offset_x + 2, offset_y + 2), logo)
                            
                            # Schatten abdunkeln
                            shadow_data = list(shadow.getdata())
                            shadow_darkened = []
                            for pixel in shadow_data:
                                if pixel[3] > 0:  # Nicht-transparente Pixel
                                    shadow_darkened.append((0, 0, 0, min(80, pixel[3])))  # Dunkler Schatten
                                else:
                                    shadow_darkened.append(pixel)
                            shadow.putdata(shadow_darkened)
                            
                            # Schatten zuerst einfügen
                            shadow_pos = (qr_center[0] - shadow.width // 2, qr_center[1] - shadow.height // 2)
                            qr_img.paste(shadow, shadow_pos, shadow)
                        
                        # Logo direkt einfügen
                        qr_img.paste(logo, logo_pos, logo)
                    except Exception as e:
                        print(f"Logo-Fehler: {e}")
                        # QR-Code ohne Logo fortsetzen
                else:
                    print(f"Logo-Datei nicht gefunden: {logo_path}")
            else:
                print("Kein Logo in Firmeneinstellungen oder CompanySettings nicht gefunden")
        
        # Auf gewünschte Größe skalieren
        qr_img = qr_img.resize((size, size), Image.Resampling.LANCZOS)
        
        # Als Base64 encodieren für Anzeige
        buffer = BytesIO()
        qr_img.save(buffer, format='PNG')
        buffer.seek(0)
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        # QR-Code temporär speichern für Download
        # Sicherstellen, dass instance-Verzeichnis existiert
        os.makedirs(app.instance_path, exist_ok=True)
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png', dir=app.instance_path)
        qr_img.save(temp_file.name, format='PNG')
        temp_filename = os.path.basename(temp_file.name)
        
        return jsonify({
            'success': True,
            'image_url': f'data:image/png;base64,{img_str}',
            'download_url': f'/qr-generator/download/{temp_filename}'
        })
        
    except Exception as e:
        print(f"QR-Code Generierungsfehler: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/qr-generator/download/<filename>')
@login_required
def download_qr_code(filename):
    """QR-Code zum Download bereitstellen"""
    try:
        file_path = os.path.join(app.instance_path, filename)
        if not os.path.exists(file_path):
            flash('Datei nicht gefunden', 'error')
            return redirect(url_for('qr_generator'))
        
        def cleanup_temp_file():
            """Temporäre Datei nach Download löschen"""
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except:
                pass
        
        response = send_from_directory(app.instance_path, filename, as_attachment=True, download_name='qr-code.png')
        
        # Cleanup nach einer Minute (gibt dem Browser Zeit zum Download)
        import threading
        timer = threading.Timer(60.0, cleanup_temp_file)
        timer.start()
        
        return response
    except Exception as e:
        flash('Fehler beim Download', 'error')
        return redirect(url_for('qr_generator'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
