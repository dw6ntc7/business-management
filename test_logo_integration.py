#!/usr/bin/env python3
"""
Test-Script um die verbesserte Logo-Integration im QR-Code zu testen
"""

import qrcode
from PIL import Image, ImageDraw
import os

def test_qr_with_logo_clearing():
    """Teste QR-Code mit Logo und korrektem Freiraum"""
    
    # Simuliere das Logo
    logo_path = "/home/matthias/trysqlite/instance/MZM_only_logo_colored_V1.2.png"
    
    if not os.path.exists(logo_path):
        print("❌ Logo-Datei nicht gefunden. Erstelle Test-Logo...")
        # Erstelle ein Test-Logo
        test_logo = Image.new('RGBA', (100, 100), (255, 0, 0, 255))  # Rotes Quadrat
        draw = ImageDraw.Draw(test_logo)
        draw.ellipse([20, 20, 80, 80], fill=(255, 255, 255, 255))  # Weißer Kreis
        test_logo.save("/home/matthias/trysqlite/test_logo.png")
        logo_path = "/home/matthias/trysqlite/test_logo.png"
    
    # QR-Code erstellen
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # Hohe Fehlerkorrektur für Logo
        box_size=10,
        border=4,
    )
    qr.add_data("https://example.com/test-with-logo")
    qr.make(fit=True)
    
    # QR-Code als PIL Image erstellen
    qr_color = '#000000'
    qr_img = qr.make_image(fill_color=qr_color, back_color='white')
    qr_img = qr_img.convert("RGBA")
    
    # Weißen Hintergrund durch Transparenz ersetzen
    data = qr_img.getdata()
    new_data = []
    for item in data:
        if item[0] >= 250 and item[1] >= 250 and item[2] >= 250:
            new_data.append((255, 255, 255, 0))  # Transparent
        else:
            new_data.append((item[0], item[1], item[2], 255))
    qr_img.putdata(new_data)
    
    print(f"✅ QR-Code erstellt: {qr_img.size}")
    
    # Logo hinzufügen
    try:
        logo = Image.open(logo_path)
        logo = logo.convert("RGBA")
        
        # Logo-Größe berechnen
        logo_size = min(qr_img.size) // 5
        logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
        
        # QR-Code-Zentrum berechnen
        qr_center = (qr_img.size[0] // 2, qr_img.size[1] // 2)
        
        # Bereich für Logo freiräumen
        clear_size = logo_size + 30
        clear_radius = clear_size // 2
        
        # Bereich im QR-Code transparent machen
        qr_data = list(qr_img.getdata())
        qr_width, qr_height = qr_img.size
        
        cleared_pixels = 0
        for y in range(qr_height):
            for x in range(qr_width):
                dx = x - qr_center[0]
                dy = y - qr_center[1]
                distance = (dx * dx + dy * dy) ** 0.5
                
                if distance <= clear_radius:
                    index = y * qr_width + x
                    qr_data[index] = (255, 255, 255, 0)  # Transparent
                    cleared_pixels += 1
        
        qr_img.putdata(qr_data)
        print(f"✅ {cleared_pixels} Pixel im Zentrum freigeräumt")
        
        # Logo-Hintergrund erstellen
        logo_bg_size = logo_size + 20
        logo_bg = Image.new('RGBA', (logo_bg_size, logo_bg_size), (0, 0, 0, 0))
        
        # Weißen Kreis als Hintergrund zeichnen
        draw = ImageDraw.Draw(logo_bg)
        circle_margin = 10
        draw.ellipse([circle_margin, circle_margin, logo_bg_size - circle_margin, logo_bg_size - circle_margin], 
                   fill=(255, 255, 255, 220))
        
        # Logo zentriert platzieren
        logo_bg_pos = ((logo_bg.size[0] - logo.size[0]) // 2, (logo_bg.size[1] - logo.size[1]) // 2)
        logo_bg.paste(logo, logo_bg_pos, logo if logo.mode == 'RGBA' else None)
        
        # Logo in QR-Code einfügen
        logo_pos = (qr_center[0] - logo_bg.size[0] // 2, qr_center[1] - logo_bg.size[1] // 2)
        qr_img.paste(logo_bg, logo_pos, logo_bg)
        
        print(f"✅ Logo eingefügt an Position {logo_pos}")
        
    except Exception as e:
        print(f"❌ Logo-Fehler: {e}")
        return False
    
    # QR-Code speichern
    output_path = "/home/matthias/trysqlite/test_qr_with_logo_cleared.png"
    qr_img.save(output_path, "PNG")
    
    print(f"✅ QR-Code mit Logo gespeichert: {output_path}")
    return True

def test_qr_without_logo():
    """Teste QR-Code ohne Logo zum Vergleich"""
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data("https://example.com/test-ohne-logo")
    qr.make(fit=True)
    
    qr_img = qr.make_image(fill_color='#0066cc', back_color='white')
    qr_img = qr_img.convert("RGBA")
    
    # Transparenz
    data = qr_img.getdata()
    new_data = []
    for item in data:
        if item[0] >= 250 and item[1] >= 250 and item[2] >= 250:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append((item[0], item[1], item[2], 255))
    qr_img.putdata(new_data)
    
    output_path = "/home/matthias/trysqlite/test_qr_without_logo.png"
    qr_img.save(output_path, "PNG")
    
    print(f"✅ QR-Code ohne Logo gespeichert: {output_path}")
    return True

if __name__ == "__main__":
    print("🧪 Teste QR-Code Logo-Integration...")
    
    print("\n1. Teste QR-Code ohne Logo:")
    test_qr_without_logo()
    
    print("\n2. Teste QR-Code mit Logo und Freiraum:")
    if test_qr_with_logo_clearing():
        print("\n🎉 Test erfolgreich!")
        print("📄 Überprüfe die erstellten Dateien:")
        print("   - test_qr_without_logo.png (ohne Logo)")
        print("   - test_qr_with_logo_cleared.png (mit Logo und Freiraum)")
    else:
        print("\n❌ Test fehlgeschlagen")
