from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import date, datetime
import os

# ...existing code...

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

# ...existing code...
