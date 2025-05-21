from db import db

class CatalogPosition(db.Model):
    __tablename__ = 'catalog_positions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    unit = db.Column(db.String(32), default='Stunde')
    price = db.Column(db.Float, nullable=False)
    vat = db.Column(db.Float, default=20.0)