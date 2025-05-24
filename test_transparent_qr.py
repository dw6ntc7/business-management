#!/usr/bin/env python3
"""
Test-Script um die Transparenz der QR-Codes zu überprüfen
"""

import qrcode
from PIL import Image
import os

def test_transparent_qr():
    """Teste die QR-Code Erstellung mit transparentem Hintergrund"""
    
    # QR-Code erstellen
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data("https://example.com")
    qr.make(fit=True)
    
    # QR-Code als PIL Image erstellen mit transparentem Hintergrund
    qr_img = qr.make_image(fill_color='#000000', back_color='white')
    qr_img = qr_img.convert("RGBA")
    
    # Weißen Hintergrund durch Transparenz ersetzen
    data = qr_img.getdata()
    new_data = []
    for item in data:
        # Weiße oder fast weiße Pixel werden transparent
        if item[0] >= 250 and item[1] >= 250 and item[2] >= 250:
            new_data.append((255, 255, 255, 0))  # Komplett transparent
        else:
            # QR-Code Pixel mit voller Deckkraft beibehalten
            new_data.append((item[0], item[1], item[2], 255))
    qr_img.putdata(new_data)
    
    # QR-Code speichern
    output_path = "/home/matthias/trysqlite/test_transparent_qr.png"
    qr_img.save(output_path, "PNG")
    
    print(f"✅ Transparenter QR-Code erstellt: {output_path}")
    
    # Bild analysieren
    test_img = Image.open(output_path)
    test_img = test_img.convert("RGBA")
    
    # Prüfe ein paar Pixel im Hintergrund (sollten transparent sein)
    transparent_pixels = 0
    opaque_pixels = 0
    
    # Teste Pixel an den Ecken (sollten Hintergrund sein)
    test_positions = [(0, 0), (0, test_img.height-1), (test_img.width-1, 0), (test_img.width-1, test_img.height-1)]
    
    for x, y in test_positions:
        pixel = test_img.getpixel((x, y))
        if len(pixel) == 4:  # RGBA
            if pixel[3] == 0:  # Alpha ist 0 = transparent
                transparent_pixels += 1
            else:
                opaque_pixels += 1
        print(f"Pixel bei ({x}, {y}): {pixel}")
    
    print(f"📊 Ergebnis:")
    print(f"   Transparente Hintergrund-Pixel: {transparent_pixels}")
    print(f"   Nicht-transparente Hintergrund-Pixel: {opaque_pixels}")
    
    if transparent_pixels > 0:
        print("✅ Transparenz funktioniert!")
        return True
    else:
        print("❌ Keine Transparenz gefunden")
        return False

if __name__ == "__main__":
    success = test_transparent_qr()
    if success:
        print("\n🎉 Test erfolgreich - Transparenter Hintergrund funktioniert!")
    else:
        print("\n❌ Test fehlgeschlagen - Transparenz funktioniert nicht")
