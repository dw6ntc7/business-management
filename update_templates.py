# Skript zum Aktualisieren der PDF-Vorlagen mit den neuen verschlankten Versionen
# Ausführen mit: python update_templates.py

from app import app, db, PdfTemplate

def update_templates():
    with app.app_context():
        # Lade die neuen Template-Inhalte
        with open('templates/offer_template_streamlined.html', 'r', encoding='utf-8') as f:
            offer_content = f.read()
        
        with open('templates/invoice_template_streamlined.html', 'r', encoding='utf-8') as f:
            invoice_content = f.read()
        
        # Aktualisiere Angebots-Template
        offer_template = PdfTemplate.query.filter_by(name='Angebot').first()
        if offer_template:
            offer_template.content = offer_content
            print("Angebots-Template aktualisiert")
        else:
            offer_template = PdfTemplate(name='Angebot', content=offer_content)
            db.session.add(offer_template)
            print("Angebots-Template erstellt")
        
        # Aktualisiere Rechnungs-Template
        invoice_template = PdfTemplate.query.filter_by(name='Rechnung').first()
        if invoice_template:
            invoice_template.content = invoice_content
            print("Rechnungs-Template aktualisiert")
        else:
            invoice_template = PdfTemplate(name='Rechnung', content=invoice_content)
            db.session.add(invoice_template)
            print("Rechnungs-Template erstellt")
        
        db.session.commit()
        print("Templates erfolgreich aktualisiert!")

        # Zeige Größenvergleich
        print("\nGrößenvergleich:")
        for template in PdfTemplate.query.all():
            print(f"{template.name}: {len(template.content)} Zeichen")

if __name__ == '__main__':
    update_templates()
