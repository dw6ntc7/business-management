#!/usr/bin/env python3
"""
Test des QR-Codes mit Logo ohne weißen Hintergrund
"""

import qrcode
from PIL import Image, ImageDraw
import os

def create_test_logo_variants():
    """Erstelle verschiedene Logo-Varianten zum Testen"""
    
    # Helles Logo (wird Schatten bekommen)
    light_logo = Image.new('RGBA', (100, 100), (0, 0, 0, 0))
    draw = ImageDraw.Draw(light_logo)
    draw.ellipse([10, 10, 90, 90], fill=(240, 240, 240, 255))  # Sehr heller Kreis
    draw.text((35, 40), "L", fill=(200, 200, 200, 255))  # Heller Text
    light_logo.save("/home/matthias/trysqlite/test_logo_light.png")
    
    # Dunkles Logo (kein Schatten nötig)
    dark_logo = Image.new('RGBA', (100, 100), (0, 0, 0, 0))
    draw = ImageDraw.Draw(dark_logo)
    draw.ellipse([10, 10, 90, 90], fill=(30, 30, 30, 255))  # Dunkler Kreis
    draw.text((35, 40), "D", fill=(255, 255, 255, 255))  # Weißer Text
    dark_logo.save("/home/matthias/trysqlite/test_logo_dark.png")
    
    # Buntes Logo
    colorful_logo = Image.new('RGBA', (120, 80), (0, 0, 0, 0))
    draw = ImageDraw.Draw(colorful_logo)
    draw.rounded_rectangle([0, 0, 120, 80], radius=15, fill=(255, 100, 50, 255))  # Orange
    draw.text((30, 30), "COLOR", fill=(255, 255, 255, 255))
    colorful_logo.save("/home/matthias/trysqlite/test_logo_colorful.png")
    
    print("✅ Test-Logo-Varianten erstellt:")
    print("   - test_logo_light.png (helles Logo)")
    print("   - test_logo_dark.png (dunkles Logo)")
    print("   - test_logo_colorful.png (buntes Logo)")

def test_qr_without_white_bg(logo_path, output_name):
    """Teste QR-Code mit Logo ohne weißen Hintergrund"""
    
    # QR-Code erstellen
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(f"https://example.com/test-{output_name}")
    qr.make(fit=True)
    
    # QR-Code mit transparentem Hintergrund
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
        
        # Freiraum schaffen
        margin = 15
        clear_width = new_width + (margin * 2)
        clear_height = new_height + (margin * 2)
        
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
        
        # Logo-Position
        logo_pos = (qr_center[0] - new_width // 2, qr_center[1] - new_height // 2)
        
        # Helligkeit prüfen für Schatten
        logo_array = list(logo.getdata())
        avg_brightness = sum(sum(pixel[:3]) for pixel in logo_array if len(pixel) >= 3) / (len(logo_array) * 3)
        
        print(f"Logo-Helligkeit: {avg_brightness:.1f}")
        
        if avg_brightness > 200:  # Helles Logo
            print("  -> Füge subtilen Schatten hinzu")
            # Schatten
            shadow = Image.new('RGBA', (new_width + 4, new_height + 4), (0, 0, 0, 0))
            
            for offset_x in range(-1, 2):
                for offset_y in range(-1, 2):
                    if offset_x != 0 or offset_y != 0:
                        shadow.paste(logo, (offset_x + 2, offset_y + 2), logo)
            
            shadow_data = list(shadow.getdata())
            shadow_darkened = []
            for pixel in shadow_data:
                if pixel[3] > 0:
                    shadow_darkened.append((0, 0, 0, min(80, pixel[3])))
                else:
                    shadow_darkened.append(pixel)
            shadow.putdata(shadow_darkened)
            
            shadow_pos = (qr_center[0] - shadow.width // 2, qr_center[1] - shadow.height // 2)
            qr_img.paste(shadow, shadow_pos, shadow)
        else:
            print("  -> Kein Schatten nötig (dunkles Logo)")
        
        # Logo direkt einfügen
        qr_img.paste(logo, logo_pos, logo)
        
        print(f"✅ Logo eingefügt ohne weißen Hintergrund")
    
    # Speichern
    output_path = f"/home/matthias/trysqlite/test_qr_no_white_{output_name}.png"
    qr_img.save(output_path, "PNG")
    print(f"✅ QR-Code gespeichert: {output_path}")

if __name__ == "__main__":
    print("🧪 Teste QR-Code mit Logo ohne weißen Hintergrund...")
    
    # Test-Logos erstellen
    create_test_logo_variants()
    
    print("\n📱 Erstelle QR-Codes ohne weiße Logo-Hintergründe:")
    
    # Verschiedene Logo-Varianten testen
    test_qr_without_white_bg("/home/matthias/trysqlite/test_logo_light.png", "light")
    test_qr_without_white_bg("/home/matthias/trysqlite/test_logo_dark.png", "dark") 
    test_qr_without_white_bg("/home/matthias/trysqlite/test_logo_colorful.png", "colorful")
    
    # Mit echtem Logo testen falls verfügbar
    real_logo_path = "/home/matthias/trysqlite/instance/MZM_only_logo_colored_V1.2.png"
    if os.path.exists(real_logo_path):
        test_qr_without_white_bg(real_logo_path, "real_mzm")
        print("✅ Test mit echtem MZM-Logo (ohne weißen Hintergrund)")
    
    print("\n🎉 Tests abgeschlossen!")
    print("📄 Erstellte QR-Codes ohne weiße Hintergründe:")
    print("   - test_qr_no_white_light.png")
    print("   - test_qr_no_white_dark.png")
    print("   - test_qr_no_white_colorful.png")
    if os.path.exists(real_logo_path):
        print("   - test_qr_no_white_real_mzm.png")
    
    print("\n💡 Das Logo wird jetzt direkt ohne weißen Hintergrund eingefügt!")
    print("   Helle Logos bekommen einen subtilen Schatten für besseren Kontrast.")
