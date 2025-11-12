"""
Hash plaintext passwords stored in pasadmin, pasusuario, pasgerente using bcrypt (passlib).

Usage:
    python scripts\hash_pas.py

This script will:
- For each PasAdmin, PasUsuario, PasGerente row, if the stored `hashed_password` does not
  look like a bcrypt hash (heuristic: not starting with "$2"), it will replace it with
  a bcrypt hash using core.security.get_password_hash.

Important: make a DB backup before running this in a non-dev environment.
"""
from database import SessionLocal
from models import PasAdmin, PasUsuario, PasGerente
from core.security import get_password_hash


def looks_like_bcrypt(s: str) -> bool:
    if not s:
        return False
    return s.startswith('$2')


def main():
    db = SessionLocal()
    try:
        for Model in (PasAdmin, PasUsuario, PasGerente):
            rows = db.query(Model).all()
            for r in rows:
                old = r.hashed_password or ''
                if not looks_like_bcrypt(old):
                    new = get_password_hash(old)
                    print(f'Hashing {Model.__name__} id={r.id}: {repr(old)} -> {new[:60]}...')
                    r.hashed_password = new
        db.commit()
        print('Done. Committed changes to DB.')
    except Exception as e:
        print('Error during hashing:', e)
        db.rollback()
    finally:
        db.close()


if __name__ == '__main__':
    main()
