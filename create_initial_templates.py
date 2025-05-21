# Skript zum Anlegen von PDF-Vorlagen für Angebot und Rechnung
# Ausführen mit: flask shell < create_initial_templates.py

from app import db, PdfTemplate

vorlagen = [
    ("Angebot", """<h2>Angebot {{ offer.offer_number }}</h2>\n<p>Kunde: {{ offer.customer.name or (offer.customer.first_name ~ ' ' ~ offer.customer.last_name) }}</p>\n<p>Datum: {{ offer.date.strftime('%d.%m.%Y') }}</p>\n<table border='1' cellpadding='5'>\n<tr><th>Bezeichnung</th><th>Menge</th><th>Brutto</th><th>Netto</th><th>MwSt (%)</th></tr>\n{% for pos in offer.positions %}\n<tr><td>{{ pos.name }}</td><td>{{ pos.quantity }}</td><td>{{ '%.2f'|format(pos.gross) }}</td><td>{{ '%.2f'|format(pos.net) }}</td><td>{{ '%.2f'|format(pos.vat) }}</td></tr>\n{% endfor %}\n</table>\n<p>Gesamt Brutto: {{ '%.2f'|format(offer.total_gross) }} €</p>\n<p>Gesamt Netto: {{ '%.2f'|format(offer.total_net) }} €</p>\n"""),
    ("Rechnung", """<h2>Rechnung {{ invoice.invoice_number }}</h2>\n<p>Kunde: {{ invoice.customer.name or (invoice.customer.first_name ~ ' ' ~ invoice.customer.last_name) }}</p>\n<p>Datum: {{ invoice.date.strftime('%d.%m.%Y') }}</p>\n<table border='1' cellpadding='5'>\n<tr><th>Bezeichnung</th><th>Menge</th><th>Brutto</th><th>Netto</th><th>MwSt (%)</th></tr>\n{% for pos in invoice.positions %}\n<tr><td>{{ pos.name }}</td><td>{{ pos.quantity }}</td><td>{{ '%.2f'|format(pos.gross) }}</td><td>{{ '%.2f'|format(pos.net) }}</td><td>{{ '%.2f'|format(pos.vat) }}</td></tr>\n{% endfor %}\n</table>\n<p>Gesamt Brutto: {{ '%.2f'|format(invoice.total_gross) }} €</p>\n<p>Gesamt Netto: {{ '%.2f'|format(invoice.total_net) }} €</p>\n""")
]

for name, content in vorlagen:
    if not PdfTemplate.query.filter_by(name=name).first():
        t = PdfTemplate(name=name, content=content)
        db.session.add(t)
        print(f"Vorlage '{name}' angelegt.")
    else:
        print(f"Vorlage '{name}' existiert bereits.")

db.session.commit()
print("Fertig.")
