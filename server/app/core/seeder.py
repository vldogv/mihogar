"""
Seeder de desarrollo — Se ejecuta al iniciar la app si ENV=development.
Crea/actualiza los datos seed con hashes bcrypt correctos.
"""

import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password, hash_pin


async def seed_dev_data():
    """Actualiza los hashes del seed SQL con valores correctos de bcrypt."""
    admin_hash = hash_password("admin123")
    maria_hash = hash_password("maria123")
    pin_hash = hash_pin("1234")

    async with AsyncSessionLocal() as session:
        try:
            # Check if owner exists
            result = await session.execute(
                text("SELECT id FROM owners WHERE email = 'admin@mihogar.com'")
            )
            owner = result.scalar_one_or_none()

            if not owner:
                print("[SEED] No se encontró el owner, los datos se crearán desde init.sql/seed.sql")
                return

            # Update hashes to proper bcrypt values
            await session.execute(
                text("UPDATE owners SET password_hash = :hash WHERE email = 'admin@mihogar.com'"),
                {"hash": admin_hash},
            )
            await session.execute(
                text("UPDATE usuarios_casa SET password_hash = :hash WHERE email = 'admin@mihogar.com'"),
                {"hash": admin_hash},
            )
            await session.execute(
                text("UPDATE usuarios_casa SET password_hash = :hash WHERE email = 'maria@mihogar.com'"),
                {"hash": maria_hash},
            )
            await session.execute(
                text("UPDATE usuarios_casa SET pin_hash = :hash WHERE nombre = 'Carlos Jr.'"),
                {"hash": pin_hash},
            )
            await session.commit()
            print("[SEED] Hashes actualizados correctamente")
            print(f"  → admin@mihogar.com / admin123")
            print(f"  → maria@mihogar.com / maria123")
            print(f"  → Carlos Jr. PIN: 1234")

        except Exception as e:
            print(f"[SEED] Error actualizando hashes: {e}")
            await session.rollback()
