"""
Inspect stored pas* password values for admin, usuario and gerente.

Usage:
    python scripts\inspect_pas.py

This script prints the stored `hashed_password` values (repr) and the associated parent rows
so you can verify whether they're plaintext or already hashed. DO NOT run this in production
without safeguards; it's intended for local debugging.
"""
from database import SessionLocal
from models import Admin, User, Manager


def main():
    db = SessionLocal()
    try:
        print('\n== Admins and their pasadmin values ==')
        admins = db.query(Admin).all()
        for a in admins:
            pas = getattr(a, 'pasadmin', None)
            print(f'admin.id={a.id} email={a.email!r} pasadmin_id={a.pasadmin_id!r} stored={repr(pas.hashed_password if pas else None)}')

        print('\n== Usuarios and their pasusuario values ==')
        users = db.query(User).all()
        for u in users:
            pas = getattr(u, 'pasusuario', None)
            print(f'user.id={u.id} email={u.email!r} pasusuario_id={u.pasusuario_id!r} stored={repr(pas.hashed_password if pas else None)}')

        print('\n== Gerentes and their pasgerente values ==')
        managers = db.query(Manager).all()
        for m in managers:
            pas = getattr(m, 'pasgerente', None)
            print(f'manager.id={m.id} email={m.email!r} pasgerente_id={m.pasgerente_id!r} stored={repr(pas.hashed_password if pas else None)}')

    finally:
        db.close()


if __name__ == '__main__':
    main()
