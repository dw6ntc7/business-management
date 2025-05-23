#!/usr/bin/env python3
"""
Test-Skript um die neuen Nummernpräfixe zu demonstrieren
"""

from app import app, db, CompanySettings, generate_number

def test_generate_number():
    """Teste die generate_number Funktion"""
    print("=== Test der generate_number Funktion ===")
    
    # Test 1: Erste Nummer mit Standard-Präfix
    result = generate_number("One-Offer-$id", None)
    print(f"Erste Angebotsnummer: {result}")
    assert result == "One-Offer-0001"
    
    # Test 2: Nachfolgende Nummer
    result = generate_number("One-Offer-$id", "One-Offer-0005")
    print(f"Nach One-Offer-0005 kommt: {result}")
    assert result == "One-Offer-0006"
    
    # Test 3: Custom Präfix
    result = generate_number("Firma-Angebot-$id", "Firma-Angebot-0042")
    print(f"Nach Firma-Angebot-0042 kommt: {result}")
    assert result == "Firma-Angebot-0043"
    
    # Test 4: Custom Präfix ohne vorherige Nummer
    result = generate_number("MeinFirma-RNG-$id", None)
    print(f"Erste Nummer mit Custom-Präfix: {result}")
    assert result == "MeinFirma-RNG-0001"
    
    print("✅ Alle Tests erfolgreich!")

def show_current_settings():
    """Zeige die aktuellen Firmeneinstellungen"""
    print("\n=== Aktuelle Firmeneinstellungen ===")
    with app.app_context():
        settings = CompanySettings.query.first()
        if settings:
            print(f"Angebotsnummer-Präfix: {settings.offer_number_prefix}")
            print(f"Rechnungsnummer-Präfix: {settings.invoice_number_prefix}")
        else:
            print("Keine Firmeneinstellungen gefunden")

if __name__ == '__main__':
    test_generate_number()
    show_current_settings()
    print("\n=== Anleitung ===")
    print("1. Gehen Sie zu http://127.0.0.1:5000/company-settings")
    print("2. Ändern Sie die Präfixe, z.B.:")
    print("   - Angebotsnummer-Präfix: 'Meinefirma-Angebot-$id'")
    print("   - Rechnungsnummer-Präfix: 'MeineRG-$id'")
    print("3. Speichern Sie die Einstellungen")
    print("4. Erstellen Sie ein neues Angebot oder eine neue Rechnung")
    print("5. Die neuen Nummern verwenden jetzt Ihre benutzerdefinierten Präfixe!")
