"""
SISTEMA DI GESTIONE DELLE SPESE PERSONALI E DEL BUDGET
Applicazione console in Python 3 con database SQLite.

Equivalenze con la traccia (C++ -> Python):
    cout   -> print()
    cin    -> input()
    switch -> match / case   (Python 3.10+)

Avvio:  python src/main.py
"""

import sqlite3
from datetime import datetime
from pathlib import Path

# Percorsi: il database viene creato nella cartella principale del progetto
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "spese.db"
SQL_PATH = BASE_DIR / "sql" / "database.sql"


# =====================================================================
#  CONNESSIONE AL DATABASE
# =====================================================================
def connetti_database():
    """Apre la connessione; al primo avvio crea il DB da sql/database.sql."""
    nuovo_db = not DB_PATH.exists()
    conn = sqlite3.connect(DB_PATH)
    # In SQLite le chiavi esterne vanno attivate a ogni connessione
    conn.execute("PRAGMA foreign_keys = ON;")
    if nuovo_db:
        conn.executescript(SQL_PATH.read_text(encoding="utf-8"))
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.commit()
        print("Database creato e popolato con i dati di esempio.")
    return conn


# =====================================================================
#  FUNZIONI DI SUPPORTO (validazione input)
# =====================================================================
def data_valida(testo, formato):
    """Restituisce True se il testo rispetta il formato data indicato."""
    try:
        datetime.strptime(testo, formato)
        return True
    except ValueError:
        return False


def leggi_importo(messaggio):
    """Legge un numero decimale; restituisce None se non è un numero."""
    testo = input(messaggio).strip().replace(",", ".")
    try:
        return float(testo)
    except ValueError:
        return None


def trova_categoria(conn, nome):
    """SQL SELECT: restituisce l'id della categoria oppure None."""
    riga = conn.execute(
        "SELECT id_categoria FROM categorie WHERE nome = ?;", (nome,)
    ).fetchone()
    return riga[0] if riga else None


# =====================================================================
#  MODULO 1 - GESTIONE DELLE CATEGORIE
# =====================================================================
def gestione_categorie(conn):
    print("\n--- GESTIONE CATEGORIE ---")
    nome = input("Nome della categoria: ").strip()

    if nome == "":
        print("Errore: il nome della categoria non può essere vuoto.")
        return

    if trova_categoria(conn, nome) is not None:
        print("La categoria esiste già.")
        return

    conn.execute("INSERT INTO categorie (nome) VALUES (?);", (nome,))
    conn.commit()
    print("Categoria inserita correttamente.")


# =====================================================================
#  MODULO 2 - INSERIMENTO DI UNA SPESA
# =====================================================================
def inserisci_spesa(conn):
    print("\n--- INSERISCI SPESA ---")
    data = input("Data (YYYY-MM-DD): ").strip()
    importo = leggi_importo("Importo: ")
    categoria = input("Nome della categoria: ").strip()
    descrizione = input("Descrizione (facoltativa): ").strip()

    if not data_valida(data, "%Y-%m-%d"):
        print("Errore: data non valida (formato YYYY-MM-DD).")
        return

    if importo is None:
        print("Errore: l'importo deve essere un numero.")
        return

    if importo <= 0:
        print("Errore: l'importo deve essere maggiore di zero.")
        return

    id_categoria = trova_categoria(conn, categoria)
    if id_categoria is None:
        print("Errore: la categoria non esiste.")
        return

    conn.execute(
        "INSERT INTO spese (data, importo, id_categoria, descrizione) "
        "VALUES (?, ?, ?, ?);",
        (data, importo, id_categoria, descrizione if descrizione else None),
    )
    conn.commit()
    print("Spesa inserita correttamente.")


# =====================================================================
#  MODULO 3 - DEFINIZIONE DEL BUDGET MENSILE
# =====================================================================
def definisci_budget(conn):
    print("\n--- DEFINISCI BUDGET MENSILE ---")
    mese = input("Mese (YYYY-MM): ").strip()
    categoria = input("Nome della categoria: ").strip()
    importo = leggi_importo("Importo del budget: ")

    if not data_valida(mese, "%Y-%m") or len(mese) != 7:
        print("Errore: mese non valido (formato YYYY-MM).")
        return

    if importo is None or importo <= 0:
        print("Errore: il budget deve essere maggiore di zero.")
        return

    id_categoria = trova_categoria(conn, categoria)
    if id_categoria is None:
        print("Errore: la categoria non esiste.")
        return

    # Inserimento o aggiornamento (UPSERT) grazie al vincolo UNIQUE (mese, id_categoria)
    conn.execute(
        "INSERT INTO budget (mese, id_categoria, importo) VALUES (?, ?, ?) "
        "ON CONFLICT (mese, id_categoria) DO UPDATE SET importo = excluded.importo;",
        (mese, id_categoria, importo),
    )
    conn.commit()
    print("Budget mensile salvato correttamente.")


# =====================================================================
#  MODULO 4 - REPORT
# =====================================================================
def report_totale_per_categoria(conn):
    righe = conn.execute(
        "SELECT c.nome, SUM(s.importo) AS totale "
        "FROM categorie c JOIN spese s ON s.id_categoria = c.id_categoria "
        "GROUP BY c.id_categoria, c.nome "
        "ORDER BY totale DESC;"
    ).fetchall()

    print("\nCategoria".ljust(18, ".") + "Totale Speso")
    if not righe:
        print("Nessuna spesa registrata.")
    for nome, totale in righe:
        print(nome.ljust(17, ".") + f"{totale:.2f}")


def report_spese_vs_budget(conn):
    righe = conn.execute(
        "SELECT b.mese, c.nome, b.importo, COALESCE(SUM(s.importo), 0) AS speso "
        "FROM budget b "
        "JOIN categorie c ON c.id_categoria = b.id_categoria "
        "LEFT JOIN spese s ON s.id_categoria = b.id_categoria "
        "                 AND strftime('%Y-%m', s.data) = b.mese "
        "GROUP BY b.id_budget "
        "ORDER BY b.mese, c.nome;"
    ).fetchall()

    if not righe:
        print("\nNessun budget definito.")
    for mese, categoria, budget, speso in righe:
        # Confronto con il budget tramite if / else
        if speso > budget:
            stato = "SUPERAMENTO BUDGET"
        else:
            stato = "NEI LIMITI"
        print(f"\nMese: {mese}")
        print(f"Categoria: {categoria}")
        print(f"Budget: {budget:.2f}")
        print(f"Speso: {speso:.2f}")
        print(f"Stato: {stato}")


def report_elenco_spese(conn):
    righe = conn.execute(
        "SELECT s.data, c.nome, s.importo, COALESCE(s.descrizione, '') "
        "FROM spese s JOIN categorie c ON c.id_categoria = s.id_categoria "
        "ORDER BY s.data, s.id_spesa;"
    ).fetchall()

    print(f"\n{'Data':<12}{'Categoria':<14}{'Importo':>10}  Descrizione")
    print("-" * 62)
    if not righe:
        print("Nessuna spesa registrata.")
    for data, categoria, importo, descrizione in righe:
        print(f"{data:<12}{categoria:<14}{importo:>10.2f}  {descrizione}")


def visualizza_report(conn):
    while True:
        print("\n-------------------------")
        print("       MENU REPORT")
        print("-------------------------")
        print("1. Totale spese per categoria")
        print("2. Spese mensili vs budget")
        print("3. Elenco completo delle spese ordinate per data")
        print("4. Ritorna al menu principale")
        print("-------------------------")
        scelta = input("Inserisci la tua scelta: ").strip()

        match scelta:
            case "1":
                report_totale_per_categoria(conn)
            case "2":
                report_spese_vs_budget(conn)
            case "3":
                report_elenco_spese(conn)
            case "4":
                return
            case _:
                print("Scelta non valida. Riprovare.")


# =====================================================================
#  MENU PRINCIPALE
# =====================================================================
def main():
    print("Benvenuto nel Sistema di Gestione delle Spese Personali!")
    conn = connetti_database()

    while True:
        print("\n-------------------------")
        print(" SISTEMA SPESE PERSONALI")
        print("-------------------------")
        print("1. Gestione Categorie")
        print("2. Inserisci Spesa")
        print("3. Definisci Budget Mensile")
        print("4. Visualizza Report")
        print("5. Esci")
        print("-------------------------")
        scelta = input("Inserisci la tua scelta: ").strip()

        try:
            match scelta:
                case "1":
                    gestione_categorie(conn)
                case "2":
                    inserisci_spesa(conn)
                case "3":
                    definisci_budget(conn)
                case "4":
                    visualizza_report(conn)
                case "5":
                    print("Arrivederci!")
                    break
                case _:
                    print("Scelta non valida. Riprovare.")
        except sqlite3.Error as errore:
            # Rete di sicurezza: un errore del DB non deve chiudere il programma
            conn.rollback()
            print(f"Errore del database: {errore}")

    conn.close()


if __name__ == "__main__":
    main()
