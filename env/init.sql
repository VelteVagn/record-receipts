-- create table for categories
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    category_name TEXT UNIQUE NOT NULL
);

-- create table for products
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    product_name TEXT UNIQUE NOT NULL,
    category_id INT references categories(id) NOT NULL
);

-- create table for purchases
CREATE TABLE purchases (
    id SERIAL PRIMARY KEY,
    date TIMESTAMP NOT NULL,
    price NUMERIC(10,2) NOT NULL,
    amount INT NOT NULL,
    product_id INT references products(id) NOT NULL
);