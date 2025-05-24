#!/usr/bin/env python3
"""
Test der proportionalen Logo-Integration im QR-Code
"""

import qrcode
from PIL import Image, ImageDraw
import os

def create_test_logos():
    """Erstelle verschiedene Test-Logos mit unterschiedlichen Proportionen"""
    
    # Quadratisches Logo
    square_logo = Image.new('RGBA', (100, 100), (0, 0, 0, 0))
    draw = ImageDraw.Draw(square_logo)
    draw.ellipse([10, 10, 90, 90], fill=(255, 0, 0, 255))  # Roter Kreis
    draw.text((35, 40), "SQ", fill=(255, 255, 255, 255))
    square_logo.save("/home/matthias/trysqlite/test_logo_square.png")
    
    # Rechteckiges Logo (breit)
    wide_logo = Image.new('RGBA', (150, 80), (0, 0, 0, 0))
    draw = ImageDraw.Draw(wide_logo)
    draw.rounded_rectangle([0, 0, 150, 80], radius=10, fill=(0, 128, 255, 255))  # Blauer Hintergrund
    draw.text((45, 30), "WIDE", fill=(255, 255, 255, 255))
    wide_logo.save("/home/matthias/trysqlite/test_logo_wide.png")
    
    # Rechteckiges Logo (hoch)
    tall_logo = Image.new('RGBA', (80, 150), (0, 0, 0, 0))
    draw = ImageDraw.Draw(tall_logo)
    draw.rounded_rectangle([0, 0, 80, 150], radius=10, fill=(0, 200, 100, 255))  # Grüner Hintergrund
    draw.text((20, 70), "TALL", fill=(255, 255, 255, 255))
    tall_logo.save("/home/matthias/trysqlite/test_logo_tall.png")
    
    print("✅ Test-Logos erstellt:")
    print("   - test_logo_square.png (100x100)")
    print("   - test_logo_wide.png (150x80)")  
    print("   - test_logo_tall.png (80x150)")

def test_proportional_qr_logo(logo_path, output_name):
    """Teste QR-Code mit proportionalem Logo"""
    
    # QR-Code erstellen
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(f"https://example.com/{output_name}")
    qr.make(fit=True)
    
    # QR-Code als PIL Image
    qr_color = '#000000'
    qr_img = qr.make_image(fill_color=qr_color, back_color='white')
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
    
    # Logo hinzufügen
    if os.path.exists(logo_path):
        logo = Image.open(logo_path)
        logo = logo.convert("RGBA")
        
        # Proportionale Skalierung
        max_logo_dimension = min(qr_img.size) // 4
        logo_width, logo_height = logo.size
        
        if logo_width > logo_height:
            new_width = max_logo_dimension
            new_height = int((logo_height * new_width) / logo_width)
        else:
            new_height = max_logo_dimension
            new_width = int((logo_width * new_height) / logo_height)
        
        logo = logo.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # QR-Code-Zentrum
        qr_center = (qr_img.size[0] // 2, qr_img.size[1] // 2)
        
        # Rechteckigen Freiraum erstellen
        margin = 15
        clear_width = new_width + (margin * 2)
        clear_height = new_height + (margin * 2)
        
        # Bereich freiräumen
        qr_data = list(qr_img.getdata())
        qr_width, qr_height = qr_img.size
        
        clear_left = qr_center[0] - clear_width // 2
        clear_right = qr_center[0] + clear_width // 2
        clear_top = qr_center[1] - clear_height // 2
        clear_bottom = qr_center[1] + clear_height // 2
        
        for y in range(qr_height):
            for x in range(qr_width):
                if (clear_left <= x <= clear_right and 
                    clear_top <= y <= clear_bottom):
                    index = y * qr_width + x
                    qr_data[index] = (255, 255, 255, 0)
        
        qr_img.putdata(qr_data)
        
        # Logo-Hintergrund
        bg_margin = 10
        logo_bg_width = new_width + (bg_margin * 2)
        logo_bg_height = new_height + (bg_margin * 2)
        logo_bg = Image.new('RGBA', (logo_bg_width, logo_bg_height), (0, 0, 0, 0))
        
        draw = ImageDraw.Draw(logo_bg)
        corner_radius = 8
        draw.rounded_rectangle(
            [0, 0, logo_bg_width, logo_bg_height],
            radius=corner_radius,
            fill=(255, 255, 255, 240)
        )
        
        # Logo platzieren
        logo_bg_pos = (bg_margin, bg_margin)
        logo_bg.paste(logo, logo_bg_pos, logo)
        
        # In QR-Code einfügen
        logo_pos = (qr_center[0] - logo_bg_width // 2, qr_center[1] - logo_bg_height // 2)
        qr_img.paste(logo_bg, logo_pos, logo_bg)
        
        print(f"✅ Logo ({logo.size}) proportional skaliert auf {new_width}x{new_height}")
    
    # Speichern
    output_path = f"/home/matthias/trysqlite/test_qr_{output_name}.png"
    qr_img.save(output_path, "PNG")
    print(f"✅ QR-Code gespeichert: {output_path}")

if __name__ == "__main__":
    print("🧪 Teste proportionale Logo-Integration...")
    
    # Test-Logos erstellen
    create_test_logos()
    
    print("\n📱 Erstelle QR-Codes mit verschiedenen Logo-Proportionen:")
    
    # Teste verschiedene Logo-Formate
    test_proportional_qr_logo("/home/matthias/trysqlite/test_logo_square.png", "proportional_square")
    test_proportional_qr_logo("/home/matthias/trysqlite/test_logo_wide.png", "proportional_wide")
    test_proportional_qr_logo("/home/matthias/trysqlite/test_logo_tall.png", "proportional_tall")
    
    # Teste mit dem echten Logo falls verfügbar
    real_logo_path = "/home/matthias/trysqlite/instance/MZM_only_logo_colored_V1.2.png"
    if os.path.exists(real_logo_path):
        test_proportional_qr_logo(real_logo_path, "proportional_real")
        print("✅ Test mit echtem MZM-Logo durchgeführt")
    
    print("\n🎉 Alle Tests abgeschlossen!")
    print("📄 Erstellte Dateien:")
    print("   - test_qr_proportional_square.png")
    print("   - test_qr_proportional_wide.png") 
    print("   - test_qr_proportional_tall.png")
    if os.path.exists(real_logo_path):
        print("   - test_qr_proportional_real.png")
