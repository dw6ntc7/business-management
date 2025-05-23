#!/usr/bin/env python3
"""
Test-Skript zur Überprüfung der positions-Route und des Login-Checks
"""

from app import app

def test_protected_routes():
    """Überprüft, ob die positions-Route korrekt geschützt ist"""
    with app.test_client() as client:
        # Versuche, die positions-Route ohne Login zu besuchen
        response = client.get('/positions', follow_redirects=False)
        
        # Sollte zur Login-Seite umleiten
        print(f"Status-Code: {response.status_code}")
        
        if response.status_code == 302:
            print("✅ Die Route ist geschützt und leitet zur Login-Seite weiter.")
        else:
            print("❌ Die Route ist NICHT geschützt!")

if __name__ == '__main__':
    test_protected_routes()
