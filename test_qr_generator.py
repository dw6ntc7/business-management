#!/usr/bin/env python3
"""
QR-Code Generator Test
Testet die QR-Code-Funktionalität außerhalb der Flask-App
"""

import qrcode
from PIL import Image
import os

def test_qr_basic():
    """Teste grundlegende QR-Code-Erstellung"""
    print("🔳 Teste grundlegende QR-Code-Erstellung...")
    
    # QR-Code erstellen
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data("https://google.com")
    qr.make(fit=True)
    
    # QR-Code als PIL Image erstellen
    qr_img = qr.make_image(fill_color="#0066cc", back_color=(255, 255, 255, 0))
    qr_img = qr_img.convert("RGBA")
    
    # Speichern
    qr_img.save("/home/matthias/trysqlite/test_qr_basic.png", format='PNG')
    print("✅ Grundlegender QR-Code erstellt: test_qr_basic.png")

def test_qr_with_logo():
    """Teste QR-Code mit Logo"""
    print("🔳 Teste QR-Code mit Logo...")
    
    logo_path = "/home/matthias/trysqlite/instance/MZM_only_logo_colored_V1.2.png"
    
    if not os.path.exists(logo_path):
        print("❌ Logo nicht gefunden, teste ohne Logo")
        test_qr_basic()
        return
    
    # QR-Code mit höherer Fehlerkorrektur für Logo
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data("https://example.com")
    qr.make(fit=True)
    
    # QR-Code als PIL Image erstellen
    qr_img = qr.make_image(fill_color="#000000", back_color=(255, 255, 255, 0))
    qr_img = qr_img.convert("RGBA")
    
    try:
        # Logo laden
        logo = Image.open(logo_path)
        logo = logo.convert("RGBA")
        
        # Logo-Größe berechnen
        logo_size = min(qr_img.size) // 5
        logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
        
        # Weißen Hintergrund für Logo erstellen
        logo_bg_size = logo_size + 20
        logo_bg = Image.new('RGBA', (logo_bg_size, logo_bg_size), (255, 255, 255, 255))
        
        # Logo zentriert auf weißem Hintergrund platzieren
        logo_bg_pos = ((logo_bg.size[0] - logo.size[0]) // 2, (logo_bg.size[1] - logo.size[1]) // 2)
        logo_bg.paste(logo, logo_bg_pos, logo)
        
        # Logo in die Mitte des QR-Codes einfügen
        qr_center = (qr_img.size[0] // 2, qr_img.size[1] // 2)
        logo_pos = (qr_center[0] - logo_bg.size[0] // 2, qr_center[1] - logo_bg.size[1] // 2)
        qr_img.paste(logo_bg, logo_pos, logo_bg)
        
        # Auf gewünschte Größe skalieren
        qr_img = qr_img.resize((400, 400), Image.Resampling.LANCZOS)
        
        # Speichern
        qr_img.save("/home/matthias/trysqlite/test_qr_with_logo.png", format='PNG')
        print("✅ QR-Code mit Logo erstellt: test_qr_with_logo.png")
        
    except Exception as e:
        print(f"❌ Fehler beim Logo-Hinzufügen: {e}")
        test_qr_basic()

def test_different_colors():
    """Teste verschiedene Farben"""
    print("🔳 Teste verschiedene Farben...")
    
    colors = [
        ("#ff0000", "rot"),
        ("#00ff00", "grün"), 
        ("#0000ff", "blau"),
        ("#ff6600", "orange"),
        ("#9900ff", "lila")
    ]
    
    for color, name in colors:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=4,
        )
        qr.add_data(f"https://example.com/{name}")
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color=color, back_color=(255, 255, 255, 0))
        qr_img = qr_img.convert("RGBA")
        qr_img = qr_img.resize((200, 200), Image.Resampling.LANCZOS)
        
        qr_img.save(f"/home/matthias/trysqlite/test_qr_{name}.png", format='PNG')
    
    print("✅ Farbige QR-Codes erstellt")

if __name__ == "__main__":
    print("🚀 Starte QR-Code Tests...")
    
    try:
        test_qr_basic()
        test_qr_with_logo()
        test_different_colors()
        
        print("\n🎉 Alle Tests erfolgreich!")
        print("📁 Erstellte Dateien:")
        print("   - test_qr_basic.png")
        print("   - test_qr_with_logo.png (falls Logo vorhanden)")
        print("   - test_qr_rot.png")
        print("   - test_qr_grün.png")
        print("   - test_qr_blau.png")
        print("   - test_qr_orange.png")
        print("   - test_qr_lila.png")
        
    except Exception as e:
        print(f"❌ Test fehlgeschlagen: {e}")
