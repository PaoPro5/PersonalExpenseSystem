-- =====================================================================
--  SISTEMA DI GESTIONE DELLE SPESE PERSONALI E DEL BUDGET
--  Script database per SQLite 3
--  Uso:  sqlite3 spese.db < database.sql
-- =====================================================================

-- In SQLite i vincoli FOREIGN KEY sono DISATTIVATI di default:
-- vanno attivati a ogni connessione (anche dal programma C++/Python).
PRAGMA foreign_keys = ON;

-- Rende lo script rieseguibile: elimina le tabelle se esistono
-- (ordine inverso rispetto alle dipendenze)
DROP TABLE IF EXISTS budget;
DROP TABLE IF EXISTS spese;
DROP TABLE IF EXISTS categorie;

-- =====================================================================
--  a) CREAZIONE TABELLE
-- =====================================================================

-- ---------------------------------------------------------------------
-- Tabella CATEGORIE: elenco delle categorie di spesa
-- ---------------------------------------------------------------------
CREATE TABLE categorie (
    id_categoria  INTEGER PRIMARY KEY AUTOINCREMENT,          -- PRIMARY KEY
    nome          TEXT    NOT NULL                            -- NOT NULL
                          UNIQUE COLLATE NOCASE               -- UNIQUE (no duplicati, anche con maiuscole diverse)
                          CHECK (length(trim(nome)) > 0)      -- CHECK: nome non vuoto
);

-- ---------------------------------------------------------------------
-- Tabella SPESE: singole spese registrate
-- ---------------------------------------------------------------------
CREATE TABLE spese (
    id_spesa      INTEGER PRIMARY KEY AUTOINCREMENT,          -- PRIMARY KEY
    data          TEXT    NOT NULL
                          CHECK (date(data) IS NOT NULL
                                 AND data = date(data)),      -- CHECK: data valida in formato YYYY-MM-DD
    importo       REAL    NOT NULL
                          CHECK (importo > 0),                -- CHECK: importo maggiore di zero
    id_categoria  INTEGER NOT NULL,
    descrizione   TEXT,                                       -- facoltativa (può essere NULL)
    FOREIGN KEY (id_categoria)                                -- FOREIGN KEY
        REFERENCES categorie (id_categoria)
        ON UPDATE CASCADE
        ON DELETE RESTRICT                                    -- non si può cancellare una categoria usata
);

-- ---------------------------------------------------------------------
-- Tabella BUDGET: limite di spesa mensile per categoria
-- ---------------------------------------------------------------------
CREATE TABLE budget (
    id_budget     INTEGER PRIMARY KEY AUTOINCREMENT,          -- PRIMARY KEY
    mese          TEXT    NOT NULL
                          CHECK (mese GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]'
                                 AND CAST(substr(mese, 6, 2) AS INTEGER) BETWEEN 1 AND 12),
                                                              -- CHECK: formato YYYY-MM, mese 01..12
    id_categoria  INTEGER NOT NULL,
    importo       REAL    NOT NULL
                          CHECK (importo > 0),                -- CHECK: budget maggiore di zero
    UNIQUE (mese, id_categoria),                              -- UNIQUE: un solo budget per mese+categoria
    FOREIGN KEY (id_categoria)                                -- FOREIGN KEY
        REFERENCES categorie (id_categoria)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

-- Indici per velocizzare i report
CREATE INDEX idx_spese_data      ON spese (data);
CREATE INDEX idx_spese_categoria ON spese (id_categoria);

-- =====================================================================
--  b) DATI DI ESEMPIO
-- =====================================================================

INSERT INTO categorie (nome) VALUES
    ('Alimentari'),
    ('Trasporti'),
    ('Casa'),
    ('Svago'),
    ('Salute');

INSERT INTO spese (data, importo, id_categoria, descrizione) VALUES
    ('2025-01-03',  85.40, 1, 'Spesa settimanale supermercato'),
    ('2025-01-10',  92.10, 1, 'Spesa settimanale supermercato'),
    ('2025-01-15',  25.00, 1, 'Pranzo'),
    ('2025-01-17', 118.00, 1, 'Spesa mensile scorte'),
    ('2025-01-05',  60.00, 2, 'Carburante'),
    ('2025-01-20',  35.00, 2, 'Abbonamento autobus'),
    ('2025-01-08', 450.00, 3, 'Affitto quota'),
    ('2025-01-25',  40.00, 4, 'Cinema e cena'),
    ('2025-02-02',  70.30, 1, 'Spesa settimanale supermercato'),
    ('2025-02-09',  65.00, 1, 'Spesa settimanale supermercato'),
    ('2025-02-04',  25.00, 2, 'Parcheggio'),
    ('2025-02-12',  18.50, 5, 'Farmacia'),
    ('2025-02-14',  55.00, 4, NULL);                          -- descrizione facoltativa

INSERT INTO budget (mese, id_categoria, importo) VALUES
    ('2025-01', 1, 300.00),   -- Alimentari gennaio: verrà SUPERATO (320.50)
    ('2025-01', 2, 150.00),   -- Trasporti gennaio: nei limiti (95.00)
    ('2025-01', 4,  50.00),   -- Svago gennaio: nei limiti
    ('2025-02', 1, 250.00),
    ('2025-02', 4,  50.00);   -- Svago febbraio: verrà SUPERATO (55.00)

-- =====================================================================
--  c) DIMOSTRAZIONE DEI VINCOLI (istruzioni che DEVONO fallire)
--     Decommentare una riga alla volta per verificare l'errore.
-- =====================================================================
-- INSERT INTO categorie (nome) VALUES ('Alimentari');                 -- UNIQUE    -> errore
-- INSERT INTO categorie (nome) VALUES ('   ');                        -- CHECK     -> errore
-- INSERT INTO categorie (nome) VALUES (NULL);                         -- NOT NULL  -> errore
-- INSERT INTO spese (data, importo, id_categoria) VALUES ('2025-01-01', -5, 1);   -- CHECK importo
-- INSERT INTO spese (data, importo, id_categoria) VALUES ('2025-13-45', 10, 1);   -- CHECK data
-- INSERT INTO spese (data, importo, id_categoria) VALUES ('2025-01-01', 10, 99);  -- FOREIGN KEY
-- INSERT INTO budget (mese, id_categoria, importo) VALUES ('2025-01', 1, 400);    -- UNIQUE mese+categoria
-- DELETE FROM categorie WHERE id_categoria = 1;                       -- FOREIGN KEY (RESTRICT)

-- =====================================================================
--  d) QUERY USATE DAL PROGRAMMA  (? = parametro passato dal codice)
-- =====================================================================

-- MODULO 1 - verifica esistenza categoria / inserimento
-- SELECT id_categoria FROM categorie WHERE nome = ?;
-- INSERT INTO categorie (nome) VALUES (?);

-- MODULO 2 - inserimento spesa (categoria passata per nome)
-- INSERT INTO spese (data, importo, id_categoria, descrizione)
--     VALUES (?, ?, (SELECT id_categoria FROM categorie WHERE nome = ?), ?);

-- MODULO 3 - inserimento o aggiornamento budget (UPSERT)
-- INSERT INTO budget (mese, id_categoria, importo) VALUES (?, ?, ?)
--     ON CONFLICT (mese, id_categoria) DO UPDATE SET importo = excluded.importo;

-- REPORT 1 - Totale spese per categoria
SELECT c.nome                  AS categoria,
       ROUND(SUM(s.importo),2) AS totale_speso
FROM   categorie c
JOIN   spese s ON s.id_categoria = c.id_categoria
GROUP  BY c.id_categoria, c.nome
ORDER  BY totale_speso DESC;

-- REPORT 2 - Spese mensili vs budget
-- (lo stato può essere calcolato in SQL con CASE oppure nel programma con if/else)
SELECT b.mese,
       c.nome                              AS categoria,
       b.importo                           AS budget,
       ROUND(COALESCE(SUM(s.importo),0),2) AS speso,
       CASE WHEN COALESCE(SUM(s.importo),0) > b.importo
            THEN 'SUPERAMENTO BUDGET'
            ELSE 'NEI LIMITI' END          AS stato
FROM   budget b
JOIN   categorie c ON c.id_categoria = b.id_categoria
LEFT   JOIN spese s ON s.id_categoria = b.id_categoria
                   AND strftime('%Y-%m', s.data) = b.mese
GROUP  BY b.id_budget
ORDER  BY b.mese, c.nome;

-- REPORT 3 - Elenco completo delle spese ordinate per data
SELECT s.data,
       c.nome                       AS categoria,
       printf('%.2f', s.importo)    AS importo,
       COALESCE(s.descrizione, '')  AS descrizione
FROM   spese s
JOIN   categorie c ON c.id_categoria = s.id_categoria
ORDER  BY s.data, s.id_spesa;
