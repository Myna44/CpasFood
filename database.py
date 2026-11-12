import sqlite3
from pathlib import Path


DB_FILE = Path("menus.db")


def get_connection():
    return sqlite3.connect(DB_FILE)


def create_database():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bibliotheque (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categorie TEXT NOT NULL,
            nom TEXT NOT NULL,
            actif INTEGER NOT NULL DEFAULT 1
        )
    """)


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS menus (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_menu DATE NOT NULL UNIQUE,
            potage_id INTEGER,
            plat_a_id INTEGER,
            plat_b_id INTEGER,
            dessert_id INTEGER,

            FOREIGN KEY(potage_id)
                REFERENCES bibliotheque(id),

            FOREIGN KEY(plat_a_id)
                REFERENCES bibliotheque(id),

            FOREIGN KEY(plat_b_id)
                REFERENCES bibliotheque(id),

            FOREIGN KEY(dessert_id)
                REFERENCES bibliotheque(id)
        )
    """)


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS calendrier_fermetures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_debut DATE NOT NULL,
            date_fin DATE NOT NULL,
            type TEXT NOT NULL,
            libelle TEXT NOT NULL
        )
    """)


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS regles_report_menu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type_jour TEXT NOT NULL,
            decalage_jours INTEGER NOT NULL,
            actif INTEGER NOT NULL DEFAULT 1
        )
    """)


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parametres (
            cle TEXT PRIMARY KEY,
            valeur TEXT
        )
    """)


    conn.commit()
    conn.close()


if __name__ == "__main__":
    create_database()
    print("Base créée avec succès.")