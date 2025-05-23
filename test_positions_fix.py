#!/usr/bin/env python3
"""
Test-Skript zur Überprüfung und Behebung des Problems mit g.user auf der Positions-Seite
"""

from app import app, db, User
from flask import g, session

# Test-Funktion zur Überprüfung der g.user-Variable
def test_user_context():
    with app.app_context():
        with app.test_request_context('/positions'):
            user_id = 1  # Admin-User-ID
            user = User.query.get(user_id)
            if user:
                g.user = user
                print(f"Erfolgreich g.user gesetzt: {g.user.username} (Rolle: {g.user.role})")
                return True
            else:
                print("Fehler: User konnte nicht gefunden werden!")
                return False

if __name__ == '__main__':
    test_user_context()