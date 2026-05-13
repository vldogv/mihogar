"""
Script de utilidad para generar hashes y verificar el setup.
Ejecutar dentro del contenedor: python -m app.core.setup_helpers
"""

from app.core.security import hash_password, hash_pin


def generate_seed_hashes():
    """Genera los hashes bcrypt para usar en seed.sql."""
    passwords = {
        "admin123": hash_password("admin123"),
        "maria123": hash_password("maria123"),
    }
    pins = {
        "1234": hash_pin("1234"),
    }

    print("\n══ Hashes para seed.sql ══")
    print("\nPasswords:")
    for plain, hashed in passwords.items():
        print(f"  {plain}: {hashed}")
    print("\nPINs:")
    for plain, hashed in pins.items():
        print(f"  {plain}: {hashed}")
    print()


if __name__ == "__main__":
    generate_seed_hashes()
