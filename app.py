from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, make_response, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import date, datetime
import os
from werkzeug.utils import secure_filename
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask import session, g
from datetime import timedelta

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

@app.route('/')
def index():
    return render_template('index.html')

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
        db.session.flush()
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

@app.route('/invoices/<int:invoice_id>/edit', methods=['GET', 'POST'])
def edit_invoice(invoice_id):
    from models import CatalogPosition
    catalog_positions = CatalogPosition.query.all()
    invoice = Invoice.query.get_or_404(invoice_id)
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
        InvoicePosition.query.filter_by(invoice_id=invoice.id).delete()
        db.session.flush()
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
                pos = InvoicePosition(name=name, quantity=quantity, gross=gross, vat=vat, net=net, invoice_id=invoice.id)
                db.session.add(pos)
                total_gross += gross * quantity
                total_net += net * quantity
        invoice.total_gross = total_gross
        invoice.total_net = total_net
        db.session.commit()
        flash('Rechnung erfolgreich aktualisiert!', 'success')
        return redirect(url_for('invoices'))
    today = invoice.date.isoformat() if invoice.date else date.today().isoformat()
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
    return render_template('invoice_form.html', invoice=invoice, customers=customers, today=today, catalog_positions=catalog_positions_dicts)

@app.route('/invoices/<int:invoice_id>/print')
def print_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    company = CompanySettings.query.first()
    # Versuche, das Rechnung-Template aus der DB zu laden
    template = PdfTemplate.query.filter_by(name="Rechnung").first()
    if template:
        from flask import render_template_string
        return render_template_string(template.content, invoice=invoice, company=company)
    # Fallback: statisches Template
    return render_template('invoice_print.html', invoice=invoice, company=company)

@app.route('/invoices/<int:invoice_id>/delete')
def delete_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    InvoicePosition.query.filter_by(invoice_id=invoice.id).delete()
    db.session.delete(invoice)
    db.session.commit()
    return redirect(url_for('invoices'))

@app.route('/company-settings', methods=['GET', 'POST'])
def company_settings():
    settings = CompanySettings.query.first()
    if not settings:
        settings = CompanySettings()
        db.session.add(settings)
        db.session.commit()
    if request.method == 'POST':
        settings.name = request.form['name']
        settings.street = request.form['street']
        settings.house_number = request.form['house_number']
        settings.postal_code = request.form['postal_code']
        settings.city = request.form['city']
        settings.country = request.form['country']
        settings.uid = request.form['uid']
        settings.firmenbuchnummer = request.form['firmenbuchnummer']
        settings.wirtschaftskammer = request.form['wirtschaftskammer']
        settings.iban = request.form['iban']
        settings.bic = request.form['bic']
        settings.bank = request.form['bank']
        settings.email = request.form['email']
        settings.phone = request.form['phone']
        settings.website = request.form['website']
        settings.notes = request.form['notes']
        settings.offer_number_prefix = request.form.get('offer_number_prefix', 'One-Offer-$id')
        settings.invoice_number_prefix = request.form.get('invoice_number_prefix', 'One-Inv-$id')
        if 'logo' in request.files and request.files['logo'].filename:
            logo = request.files['logo']
            filename = secure_filename(logo.filename)
            logo.save(os.path.join('instance', filename))
            settings.logo_filename = filename
        db.session.commit()
        flash('Firmendaten gespeichert!', 'success')
        return redirect(url_for('company_settings'))
    return render_template('company_settings.html', settings=settings)

@app.route('/instance/<filename>')
def uploaded_logo(filename):
    return send_from_directory('instance', filename)

@app.route('/offers/<int:offer_id>/edit', methods=['GET', 'POST'])
def edit_offer(offer_id):
    from models import CatalogPosition
    catalog_positions = CatalogPosition.query.all()
    offer = Offer.query.get_or_404(offer_id)
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
        # Positionen aktualisieren: alte löschen, neue anlegen
        OfferPosition.query.filter_by(offer_id=offer.id).delete()
        db.session.flush()
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
                pos = OfferPosition(name=name, quantity=quantity, gross=gross, vat=vat, net=net, offer_id=offer.id)
                db.session.add(pos)
                total_gross += gross * quantity
                total_net += net * quantity
        offer.total_gross = total_gross
        offer.total_net = total_net
        db.session.commit()
        flash('Angebot erfolgreich aktualisiert!', 'success')
        return redirect(url_for('offers'))
    # GET: Formular mit bestehenden Daten füllen
    today = offer.date.isoformat() if offer.date else date.today().isoformat()
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
    return render_template('offer_form.html', customers=customers, offer=offer, today=today, catalog_positions=catalog_positions_dicts)

@app.route('/projects')
def projects():
    all_projects = Project.query.all()
    return render_template('projects.html', projects=all_projects)

@app.route('/projects/<int:project_id>')
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    return render_template('project_detail.html', project=project)

@app.route('/projects/new', methods=['GET', 'POST'])
def new_project():
    customers = Customer.query.all()
    offers = Offer.query.all()
    invoices = Invoice.query.all()
    categories_list = ['Foto', 'Video', 'Branding', 'Dokumente']
    if request.method == 'POST':
        name = request.form['name']
        date_val = datetime.strptime(request.form['date'], "%Y-%m-%d").date()
        customer_id = request.form['customer_id']
        categories = ','.join(request.form.getlist('categories'))
        offer_ids = request.form.getlist('offers')
        invoice_ids = request.form.getlist('invoices')
        project = Project(name=name, date=date_val, customer_id=customer_id, categories=categories)
        for oid in offer_ids:
            offer = Offer.query.get(int(oid))
            if offer:
                project.offers.append(offer)
        for iid in invoice_ids:
            invoice = Invoice.query.get(int(iid))
            if invoice:
                project.invoices.append(invoice)
        db.session.add(project)
        db.session.commit()
        return redirect(url_for('projects'))
    today = date.today().isoformat()
    return render_template('project_form.html', customers=customers, offers=offers, invoices=invoices, categories_list=categories_list, today=today)

@app.route('/projects/<int:project_id>/edit', methods=['GET', 'POST'])
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)
    customers = Customer.query.all()
    offers = Offer.query.all()
    invoices = Invoice.query.all()
    categories_list = ['Foto', 'Video', 'Branding', 'Dokumente']
    if request.method == 'POST':
        project.name = request.form['name']
        project.date = datetime.strptime(request.form['date'], "%Y-%m-%d").date()
        project.customer_id = request.form['customer_id']
        project.categories = ','.join(request.form.getlist('categories'))
        # Angebote und Rechnungen neu zuordnen
        project.offers = []
        project.invoices = []
        offer_ids = request.form.getlist('offers')
        invoice_ids = request.form.getlist('invoices')
        for oid in offer_ids:
            offer = Offer.query.get(int(oid))
            if offer:
                project.offers.append(offer)
        for iid in invoice_ids:
            invoice = Invoice.query.get(int(iid))
            if invoice:
                project.invoices.append(invoice)
        db.session.commit()
        return redirect(url_for('projects'))
    selected_categories = project.categories.split(',') if project.categories else []
    selected_offers = [o.id for o in project.offers]
    selected_invoices = [i.id for i in project.invoices]
    return render_template('project_form.html', project=project, customers=customers, offers=offers, invoices=invoices, categories_list=categories_list, selected_categories=selected_categories, selected_offers=selected_offers, selected_invoices=selected_invoices)

@app.route('/projects/<int:project_id>/delete')
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    return redirect(url_for('projects'))

@app.route('/projects/<int:project_id>/datenschutz')
def project_datenschutz(project_id):
    project = Project.query.get_or_404(project_id)
    company = CompanySettings.query.first()
    customer = project.customer
    categories = [c.strip() for c in project.categories.split(',') if c.strip()]
    # Textbausteine je Kategorie
    kategorie_text = {
        'Foto': "Für die Durchführung von Fotoaufträgen werden personenbezogene Daten (z.B. Name, Kontaktdaten, Bildmaterial) ausschließlich zur Vertragserfüllung verarbeitet. Die Aufnahmen werden gemäß den gesetzlichen Vorgaben gespeichert und nicht ohne Einwilligung veröffentlicht.",
        'Video': "Für die Durchführung von Videoaufträge werden personenbezogene Daten (z.B. Name, Kontaktdaten, Videomaterial) ausschließlich zur Vertragserfüllung verarbeitet. Die Aufnahmen werden gemäß den gesetzlichen Vorgaben gespeichert und nicht ohne Einwilligung veröffentlicht.",
        'Branding': "Im Rahmen von Branding- und Designprojekten werden personenbezogene Daten (z.B. Name, Kontaktdaten, Logos, Designentwürfe) ausschließlich zur Vertragserfüllung verarbeitet.",
        'Dokumente': "Für die Erstellung und Bearbeitung von Dokumenten werden personenbezogene Daten (z.B. Name, Kontaktdaten, Text- und Bildmaterial) ausschließlich zur Vertragserfüllung verarbeitet."
    }
    kategorie_abschnitte = [kategorie_text[cat] for cat in categories if cat in kategorie_text]
    # Datenschutztext generieren
    datenschutz = f"""
DATENSCHUTZERKLÄRUNG FÜR DAS PROJEKT: {project.name}\n\n
Verantwortlicher:
{company.name}\n{company.street} {company.house_number}, {company.postal_code} {company.city}, {company.country}\nE-Mail: {company.email} | Telefon: {company.phone}

Kunde:
{customer.name or (customer.first_name + ' ' + customer.last_name)}\n{customer.street} {customer.house_number}, {customer.postal_code} {customer.city}, {customer.country}\nE-Mail: {customer.email} | Telefon: {customer.phone}

Zweck der Datenverarbeitung:
""" + '\n'.join(f"- {abschnitt}" for abschnitt in kategorie_abschnitte) + f"""

Rechtsgrundlage:
Die Verarbeitung erfolgt auf Grundlage von Art. 6 Abs. 1 lit. b DSGVO (Vertragserfüllung) sowie ggf. auf Basis gesetzlicher Aufbewahrungspflichten.

Weitergabe:
Eine Weitergabe an Dritte erfolgt nur, sofern dies zur Vertragserfüllung notwendig ist oder eine gesetzliche Verpflichtung besteht.

Speicherdauer:
Die Daten werden für die Dauer der gesetzlichen Aufbewahrungsfristen gespeichert. Bild- und Videomaterial wird nur mit Einwilligung veröffentlicht.

Betroffenenrechte:
Sie haben das Recht auf Auskunft, Berichtigung, Löschung, Einschränkung der Verarbeitung, Datenübertragbarkeit und Widerspruch. Beschwerden richten Sie an die Datenschutzbehörde.

Ort, Datum: ____________________________
Unterschrift Kunde: ____________________
Unterschrift Auftragnehmer: ____________
"""
    response = make_response(datenschutz)
    response.headers['Content-Type'] = 'text/plain; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename=Datenschutzerklaerung_Projekt_{project.id}.txt'
    return response

@app.route('/projects/<int:project_id>/datenschutz_pdf')
def project_datenschutz_pdf(project_id):
    project = Project.query.get_or_404(project_id)
    company = CompanySettings.query.first()
    customer = project.customer
    categories = [c.strip() for c in project.categories.split(',') if c.strip()]
    kategorie_text = {
        'Foto': "Für die Durchführung von Fotoaufträgen werden personenbezogene Daten (z.B. Name, Kontaktdaten, Bildmaterial) ausschließlich zur Vertragserfüllung verarbeitet. Die Aufnahmen werden gemäß den gesetzlichen Vorgaben gespeichert und nicht ohne Einwilligung veröffentlicht.",
        'Video': "Für die Durchführung von Videoaufträge werden personenbezogene Daten (z.B. Name, Kontaktdaten, Videomaterial) ausschließlich zur Vertragserfüllung verarbeitet. Die Aufnahmen werden gemäß den gesetzlichen Vorgaben gespeichert und nicht ohne Einwilligung veröffentlicht.",
        'Branding': "Im Rahmen von Branding- und Designprojekten werden personenbezogene Daten (z.B. Name, Kontaktdaten, Logos, Designentwürfe) ausschließlich zur Vertragserfüllung verarbeitet.",
        'Dokumente': "Für die Erstellung und Bearbeitung von Dokumenten werden personenbezogene Daten (z.B. Name, Kontaktdaten, Text- und Bildmaterial) ausschließlich zur Vertragserfüllung verarbeitet."
    }
    kategorie_abschnitte = [kategorie_text[cat] for cat in categories if cat in kategorie_text]
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 40
    p.setFont("Helvetica-Bold", 14)
    p.drawString(40, y, f"Datenschutzerklärung für das Projekt: {project.name}")
    y -= 30
    p.setFont("Helvetica", 10)
    p.drawString(40, y, "Verantwortlicher:")
    y -= 15
    p.setFont("Helvetica", 10)
    p.drawString(60, y, f"{company.name}")
    y -= 15
    p.drawString(60, y, f"{company.street} {company.house_number}, {company.postal_code} {company.city}, {company.country}")
    y -= 15
    p.drawString(60, y, f"E-Mail: {company.email} | Telefon: {company.phone}")
    y -= 25
    p.setFont("Helvetica", 10)
    p.drawString(40, y, "Kunde:")
    y -= 15
    p.drawString(60, y, f"{customer.name or (customer.first_name + ' ' + customer.last_name)}")
    y -= 15
    p.drawString(60, y, f"{customer.street} {customer.house_number}, {customer.postal_code} {customer.city}, {customer.country}")
    y -= 15
    p.drawString(60, y, f"E-Mail: {customer.email} | Telefon: {customer.phone}")
    y -= 25
    p.setFont("Helvetica-Bold", 11)
    p.drawString(40, y, "Zweck der Datenverarbeitung:")
    y -= 18
    p.setFont("Helvetica", 10)
    for abschnitt in kategorie_abschnitte:
        import textwrap
        for wrapped_line in textwrap.wrap(f"- {abschnitt}", 100):
            p.drawString(60, y, wrapped_line)
            y -= 13
        y -= 5
    y -= 10
    p.setFont("Helvetica-Bold", 11)
    p.drawString(40, y, "Rechtsgrundlage:")
    y -= 15
    p.setFont("Helvetica", 10)
    for wrapped_line in textwrap.wrap("Die Verarbeitung erfolgt auf Grundlage von Art. 6 Abs. 1 lit. b DSGVO (Vertragserfüllung) sowie ggf. auf Basis gesetzlicher Aufbewahrungspflichten.", 100):
        p.drawString(60, y, wrapped_line)
        y -= 13
    y -= 12
    p.setFont("Helvetica-Bold", 11)
    p.drawString(40, y, "Weitergabe:")
    y -= 15
    p.setFont("Helvetica", 10)
    for wrapped_line in textwrap.wrap("Eine Weitergabe an Dritte erfolgt nur, sofern dies zur Vertragserfüllung notwendig ist oder eine gesetzliche Verpflichtung besteht.", 100):
        p.drawString(60, y, wrapped_line)
        y -= 13
    y -= 12
    p.setFont("Helvetica-Bold", 11)
    p.drawString(40, y, "Speicherdauer:")
    y -= 15
    p.setFont("Helvetica", 10)
    for wrapped_line in textwrap.wrap("Die Daten werden für die Dauer der gesetzlichen Aufbewahrungsfristen gespeichert. Bild- und Videomaterial wird nur mit Einwilligung veröffentlicht.", 100):
        p.drawString(60, y, wrapped_line)
        y -= 13
    y -= 12
    p.setFont("Helvetica-Bold", 11)
    p.drawString(40, y, "Betroffenenrechte:")
    y -= 15
    p.setFont("Helvetica", 10)
    for wrapped_line in textwrap.wrap("Sie haben das Recht auf Auskunft, Berichtigung, Löschung, Einschränkung der Verarbeitung, Datenübertragbarkeit und Widerspruch. Beschwerden richten Sie an die Datenschutzbehörde.", 100):
        p.drawString(60, y, wrapped_line)
        y -= 13
    y -= 30
    # Unterschriftenbereich größer und Linien länger
    p.setFont("Helvetica", 12)
    p.drawString(40, y, "Ort, Datum: " + "_"*60)
    y -= 25
    p.setFont("Helvetica", 12)
    p.drawString(40, y, "Unterschrift Kunde: " + "_"*50)
    y -= 25
    p.setFont("Helvetica", 12)
    p.drawString(40, y, "Unterschrift Auftragnehmer: " + "_"*44)
    p.showPage()
    p.save()
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        mimetype='application/pdf',
        download_name=f"Datenschutzerklaerung_Projekt_{project_id}.pdf"
    )

# ALLE Routen außer /login, /logout, /instance/<filename> und static schützen
PROTECTED_ROUTES = [
    'index', 'customers', 'new_customer', 'edit_customer', 'delete_customer',
    'offers', 'new_offer', 'edit_offer', 'print_offer',
    'invoices', 'new_invoice', 'edit_invoice', 'print_invoice', 'delete_invoice',
    'company_settings', 'projects', 'project_detail', 'new_project', 'edit_project', 'delete_project',
    'project_datenschutz', 'project_datenschutz_pdf',
    'positions', 'new_position', 'edit_position', 'delete_position'
]
for route in PROTECTED_ROUTES:
    view_func = app.view_functions.get(route)
    if view_func:
        app.view_functions[route] = login_required(view_func)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['token_expiry'] = (datetime.utcnow() + timedelta(hours=1)).isoformat()
            flash('Login erfolgreich!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Ungültiger Benutzername oder Passwort.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Abgemeldet.', 'info')
    return redirect(url_for('login'))

# --- User Management Routes (Admin only) ---
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
        if User.query.filter_by(username=username).first():
            flash('Benutzername existiert bereits.', 'danger')
            return redirect(url_for('new_user'))
        user = User(username=username, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Benutzer angelegt.', 'success')
        return redirect(url_for('users'))
    return render_template('user_form.html', user=None)

@app.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        password = request.form['password']
        role = request.form['role']
        if password:
            user.set_password(password)
        user.role = role
        db.session.commit()
        flash('Benutzer aktualisiert.', 'success')
        return redirect(url_for('users'))
    return render_template('user_form.html', user=user)

@app.route('/users/<int:user_id>/delete')
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == g.user.id:
        flash('Du kannst dich nicht selbst löschen.', 'danger')
        return redirect(url_for('users'))
    db.session.delete(user)
    db.session.commit()
    flash('Benutzer gelöscht.', 'success')
    return redirect(url_for('users'))

@app.route('/templates')
@admin_required
def templates():
    templates = PdfTemplate.query.all()
    return render_template('templates.html', templates=templates)

@app.route('/templates/new', methods=['GET', 'POST'])
@admin_required
def new_template():
    if request.method == 'POST':
        name = request.form['name']
        content = request.form['content']
        template = PdfTemplate(name=name, content=content)
        db.session.add(template)
        db.session.commit()
        flash('Vorlage erstellt!', 'success')
        return redirect(url_for('templates'))
    return render_template('edit_template.html', template=None)

@app.route('/templates/<int:template_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_template(template_id):
    template = PdfTemplate.query.get_or_404(template_id)
    if request.method == 'POST':
        template.content = request.form['content']
        db.session.commit()
        flash('Vorlage gespeichert!', 'success')
        return redirect(url_for('templates'))
    return render_template('edit_template.html', template=template)

@app.route('/templates/<int:template_id>/delete')
@admin_required
def delete_template(template_id):
    template = PdfTemplate.query.get_or_404(template_id)
    db.session.delete(template)
    db.session.commit()
    flash('Vorlage gelöscht.', 'success')
    return redirect(url_for('templates'))

@app.route('/offers/<int:offer_id>/delete')
def delete_offer(offer_id):
    offer = Offer.query.get_or_404(offer_id)
    db.session.delete(offer)
    db.session.commit()
    flash('Angebot wurde gelöscht.', 'success')
    return redirect(url_for('offers'))

@app.route('/offers/<int:offer_id>/convert', methods=['POST'])
def convert_offer_to_invoice(offer_id):
    offer = Offer.query.get_or_404(offer_id)
    if offer.status not in ['angenommen', 'abgelehnt', 'abgelaufen']:
        flash('Nur angenommene oder abgeschlossene Angebote können konvertiert werden.', 'danger')
        return redirect(url_for('offers'))
    # Prüfe, ob schon eine Rechnung existiert (optional, je nach Logik)
    existing_invoice = Invoice.query.filter_by(title=offer.title, customer_id=offer.customer_id, total_gross=offer.total_gross).first()
    if existing_invoice:
        flash('Für dieses Angebot existiert bereits eine Rechnung.', 'warning')
        return redirect(url_for('offers'))
    # Rechnungsnummer generieren basierend auf Firmeneinstellungen
    company_settings = CompanySettings.query.first()
    invoice_prefix = company_settings.invoice_number_prefix if company_settings and company_settings.invoice_number_prefix else "One-Inv-$id"
    
    last_invoice = Invoice.query.order_by(Invoice.id.desc()).first()
    last_number_str = last_invoice.invoice_number if last_invoice else None
    invoice_number = generate_number(invoice_prefix, last_number_str)
    invoice = Invoice(
        invoice_number=invoice_number,
        title=offer.title,
        customer_id=offer.customer_id,
        total_gross=offer.total_gross,
        total_net=offer.total_net,
        date=date.today(),
        due_date=None,
        status='offen',
        notes=offer.notes
    )
    db.session.add(invoice)
    db.session.flush()
    # Positionen übernehmen
    for pos in offer.positions:
        db.session.add(InvoicePosition(
            invoice_id=invoice.id,
            name=pos.name,
            quantity=pos.quantity,
            gross=pos.gross,
            vat=pos.vat,
            net=pos.net
        ))
    db.session.commit()
    flash('Angebot wurde in eine Rechnung konvertiert.', 'success')
    return redirect(url_for('invoices'))

@app.route('/positions')
@login_required
def positions():
    positions = CatalogPosition.query.all()
    return render_template('positions.html', positions=positions)

@app.route('/positions/new', methods=['GET', 'POST'])
@login_required
def new_position():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description')
        unit = request.form.get('unit', 'Stunde')
        price = float(request.form['price'])
        vat = float(request.form.get('vat', 20.0))
        pos = CatalogPosition(name=name, description=description, unit=unit, price=price, vat=vat)
        db.session.add(pos)
        db.session.commit()
        flash('Position gespeichert.', 'success')
        return redirect(url_for('positions'))
    return render_template('position_form.html')

@app.route('/positions/<int:position_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_position(position_id):
    pos = CatalogPosition.query.get_or_404(position_id)
    if request.method == 'POST':
        pos.name = request.form['name']
        pos.description = request.form.get('description')
        pos.unit = request.form.get('unit', 'Stunde')
        pos.price = float(request.form['price'])
        pos.vat = float(request.form.get('vat', 20.0))
        db.session.commit()
        flash('Position aktualisiert.', 'success')
        return redirect(url_for('positions'))
    return render_template('position_form.html', position=pos)

@app.route('/positions/<int:position_id>/delete')
@login_required
def delete_position(position_id):
    pos = CatalogPosition.query.get_or_404(position_id)
    db.session.delete(pos)
    db.session.commit()
    flash('Position gelöscht.', 'success')
    return redirect(url_for('positions'))

if __name__ == '__main__':
    app.run(debug=True)
