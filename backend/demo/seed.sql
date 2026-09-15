-- A tiny dataset so the demo has something to ask questions about.
-- Loaded once, on first start of the `demo` profile's Postgres.

CREATE TABLE customers (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    city        TEXT NOT NULL,
    signed_up   DATE NOT NULL
);

CREATE TABLE products (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    category    TEXT NOT NULL,
    unit_price  NUMERIC(10, 2) NOT NULL
);

CREATE TABLE orders (
    id           SERIAL PRIMARY KEY,
    customer_id  INTEGER NOT NULL REFERENCES customers(id),
    product_id   INTEGER NOT NULL REFERENCES products(id),
    quantity     INTEGER NOT NULL,
    ordered_at   DATE NOT NULL
);

INSERT INTO customers (name, city, signed_up) VALUES
    ('Aisha Khan',     'London',    '2024-01-15'),
    ('Ben Carter',     'London',    '2024-02-03'),
    ('Chen Wei',       'Singapore', '2024-02-19'),
    ('Diego Morales',  'Madrid',    '2024-03-07'),
    ('Elena Rossi',    'Milan',     '2024-04-22'),
    ('Farid Haddad',   'Dubai',     '2024-05-11'),
    ('Grace Okafor',   'Lagos',     '2024-06-30'),
    ('Hiro Tanaka',    'Tokyo',     '2024-07-18');

INSERT INTO products (name, category, unit_price) VALUES
    ('Standing Desk',      'Furniture',   449.00),
    ('Ergonomic Chair',    'Furniture',   329.50),
    ('Mechanical Keyboard','Peripherals',  129.99),
    ('27" Monitor',        'Displays',    319.00),
    ('USB-C Dock',         'Peripherals',  189.95),
    ('Desk Lamp',          'Lighting',     59.00);

INSERT INTO orders (customer_id, product_id, quantity, ordered_at) VALUES
    (1, 1, 1, '2024-03-01'), (1, 3, 2, '2024-03-01'), (1, 4, 2, '2024-08-12'),
    (2, 2, 1, '2024-03-14'), (2, 6, 3, '2024-09-02'),
    (3, 4, 1, '2024-04-05'), (3, 5, 1, '2024-04-05'), (3, 1, 1, '2024-10-19'),
    (4, 3, 1, '2024-05-21'), (4, 6, 1, '2024-05-21'),
    (5, 2, 2, '2024-06-08'), (5, 4, 1, '2024-11-03'),
    (6, 5, 2, '2024-07-14'), (6, 1, 1, '2024-07-14'),
    (7, 6, 4, '2024-08-27'), (7, 3, 1, '2024-12-01'),
    (8, 4, 3, '2024-09-30'), (8, 2, 1, '2024-09-30'), (8, 5, 1, '2025-01-08');
