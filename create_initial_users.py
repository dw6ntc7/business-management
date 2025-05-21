# Skript zum Anlegen initialer User für das Business-Management-System
# Ausführen mit: flask shell < create_initial_users.py

from app import db, User

# Benutzerliste: (username, passwort, rolle)
users = [
    ("admin", "admin", "admin"),
    ("kollege1", "kollege1pass", "user"),
    ("kollege2", "kollege2pass", "user"),
    ("kollege3", "kollege3pass", "user"),
]

for username, password, role in users:
    if not User.query.filter_by(username=username).first():
        user = User(username=username, role=role)
        user.set_password(password)
        db.session.add(user)
        print(f"User {username} angelegt.")
    else:
        print(f"User {username} existiert bereits.")

db.session.commit()
print("Fertig.")
