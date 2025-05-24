#!/usr/bin/env python3
"""
Update Rechnung template in database with latest QR code improvements
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import PdfTemplate
from db import db

def update_invoice_template():
    """Update the invoice template in database with latest content"""
    
    with app.app_context():
        # Read the current template file
        template_path = 'templates/invoice_template_streamlined.html'
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                new_content = f.read()
                
            print(f"📖 Template gelesen: {len(new_content)} Zeichen")
            
            # Find and update the Rechnung template
            template = PdfTemplate.query.filter_by(name='Rechnung').first()
            
            if template:
                old_length = len(template.content)
                template.content = new_content
                db.session.commit()
                
                print(f"✅ Template 'Rechnung' erfolgreich aktualisiert!")
                print(f"   Alte Länge: {old_length} Zeichen")
                print(f"   Neue Länge: {len(new_content)} Zeichen")
                print(f"   Differenz: {len(new_content) - old_length:+d} Zeichen")
                
                return True
            else:
                print("❌ Template 'Rechnung' nicht in Datenbank gefunden!")
                return False
                
        except FileNotFoundError:
            print(f"❌ Template-Datei nicht gefunden: {template_path}")
            return False
        except Exception as e:
            print(f"❌ Fehler beim Aktualisieren: {e}")
            return False

if __name__ == '__main__':
    success = update_invoice_template()
    sys.exit(0 if success else 1)
