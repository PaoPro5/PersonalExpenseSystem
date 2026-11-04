# Personal Expense System

Sistema di gestione delle spese personali e del budget, con interfaccia a console.
Il programma è scritto in **Python 3** e usa un database relazionale **SQLite**.

Con il programma puoi:
- definire categorie di spesa
- registrare spese giornaliere
- impostare un budget mensile per categoria
- consultare report calcolati tramite query SQL

## Struttura del repository

```
PersonalExpenseSystem/
├── src/
│   └── main.py          # codice sorgente dell'applicazione
├── sql/
│   └── database.sql     # creazione tabelle, vincoli, dati di esempio, query
├── demo/
│   └── demo_video.mp4   # video dimostrativo
└── README.md
```

## Requisiti per l'esecuzione

- **Interprete:** Python **3.10 o superiore**, perché il menu usa `match`/`case`, l'equivalente Python dello `switch`.
  Puoi controllare la versione con `python --version`.
- **Librerie:** servono solo moduli della libreria standard Python, quindi non c'è niente da installare:
  - `sqlite3`: accesso al database SQLite
  - `datetime`: validazione delle date
  - `pathlib`: gestione dei percorsi dei file
- **Compilazione:** non serve, perché Python è un linguaggio interpretato.
- **(Facoltativo)** Puoi installare la CLI `sqlite3` per eseguire lo script SQL a mano.

## Istruzioni per eseguire il programma

1. Clona il repository, oppure scaricalo come ZIP da GitHub (**Code → Download ZIP**):
   ```
   git clone https://github.com/<nomeutente>/PersonalExpenseSystem.git
   ```
2. Entra nella cartella del progetto:
   ```
   cd PersonalExpenseSystem
   ```
3. Avvia il programma con il comando esatto:
   ```
   python src/main.py
   ```
   Su macOS/Linux, se `python` non è disponibile, usa `python3 src/main.py`.

Al primo avvio il programma crea il file `spese.db` nella cartella del progetto.
Lo fa eseguendo `sql/database.sql`, che crea le tabelle e inserisce i dati di esempio.
Per ripartire da zero basta cancellare `spese.db` e rilanciare il programma.

### Creazione manuale del database (facoltativa)

```
sqlite3 spese.db < sql/database.sql
```

## Utilizzo

```
-------------------------
 SISTEMA SPESE PERSONALI
-------------------------
1. Gestione Categorie
2. Inserisci Spesa
3. Definisci Budget Mensile
4. Visualizza Report
5. Esci
-------------------------
```

| Modulo | Input | Output |
|---|---|---|
| 1. Gestione Categorie | nome categoria | *Categoria inserita correttamente.* / *La categoria esiste già.* |
| 2. Inserisci Spesa | data (YYYY-MM-DD), importo, categoria, descrizione facoltativa | *Spesa inserita correttamente.* / messaggi di errore |
| 3. Definisci Budget | mese (YYYY-MM), categoria, importo | *Budget mensile salvato correttamente.* (inserisce o aggiorna) |
| 4. Visualizza Report | sottomenu 1–4 | totale per categoria, spese vs budget, elenco spese per data |

## Database

Il database ha tre tabelle: `categorie`, `spese` e `budget`. Le spese e i budget sono collegati alle categorie tramite chiave esterna.
Lo script `sql/database.sql` dichiara in modo esplicito i vincoli **PRIMARY KEY**, **FOREIGN KEY**, **CHECK**, **UNIQUE** e **NOT NULL**.

## Demo

Il video `demo/demo_video.mp4` mostra l'avvio del programma, l'uso dei menu, l'inserimento dei dati e la generazione dei report.
