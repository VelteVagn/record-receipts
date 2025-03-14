#!/usr/bin/env python3

"""
This script is part of record_receipts.sh. It takes a CSV as an argument
and then logs its contents into a PSQL table. When new products that are
not present in the PSQL table "products", the user is prompted to give a
category the new product fits into. The script opens up for the
possibility of partially logging CSV which will result in new CSVs being
saved in ./data/archive. 

Usage:
    python3 src/log_csv.py yyyy-mm-ddThh_mm_ss.csv
"""

# imports:
import os
import sys
import psycopg2
import pandas as pd
from prompt_toolkit import prompt
from dotenv import load_dotenv


# function to exit the python script whilst saving the dataframe
def save_and_exit(dataframe, indices):
    registered_df = df.loc[indices]
    df.drop(index=indices, inplace=True)

    df.to_csv(f"{csv[:-4]}_modified.csv", index=False)
    registered_df.to_csv(f"{csv[:-4]}_registered.csv", index=False)
    sys.exit(2)


def get_categories(conn, list_cat):
    """
    If list_cat is false, simply returns a list of all categories. If
    list_cat is true, all the categories will be printed in 3 separate
    columns as well.
    """
    # make a list of all categories:
    list_categories = "SELECT category_name FROM categories ORDER BY category_name;"
    with conn.cursor() as cursor:
        cursor.execute(list_categories)
        categories = cursor.fetchall()
    categories = [c[0] for c in categories]

    # list all the categories in 3 columns:
    if list_cat:
        max_length = max([len(c) for c in categories])
        l = len(categories)
        remainder = l % 3
        iterations = int((l - remainder) / 3)
        for i in range(iterations):
            j = i * 3
            row_list = categories[j : j + 3]
            row_string = ""
            for k in row_list:
                space = 3 * " " + (max_length - len(k)) * " "
                row_string += k + space
            print(row_string)
        if remainder == 1:
            print(categories[-1])
        elif remainder == 2:
            space = 3 * " " + (max_length - len(categories[-2])) * " "
            print(categories[-2] + space + categories[-1])
    return categories


def unregistered_product(row, conn, indices, df, dt, empty_n=False):
    """
    Prompts the user what to do when new products that have not occurred before
    shows up.
    """

    # PSQL commands:
    insert_category = "INSERT INTO categories (category_name) VALUES (%s);"

    check_product_existence = (
        "SELECT EXISTS (SELECT 1 FROM products WHERE product_name = %s);"
    )

    find_category_id = "SELECT id FROM categories WHERE category_name = %s;"

    insert_product = "INSERT INTO products (product_name, category_id) VALUES (%s, %s);"

    find_product_id = "SELECT id FROM products WHERE product_name = %s;"

    insert_product_purchase = """
      INSERT INTO purchases
      (date, price, amount, product_id)
      VALUES (%s, %s, %s, %s);
    """

    # Prompt cases:
    with conn.cursor() as cursor:
        user_input = input().lower()
        if user_input == "n" or empty_n:
            print("Enter one of the existing categories or create a new one:")
            categories = get_categories(conn, list_cat=True)
            new_input = input().lower()
            new_input = new_input[0].upper() + new_input[1:]
            if not new_input in categories:
                cursor.execute(insert_category, (new_input,))
                conn.commit()
            cursor.execute(find_category_id, (new_input,))
            category_id = cursor.fetchone()[0]
            cursor.execute(insert_product, (row["Product"], category_id))
            conn.commit()
            cursor.execute(find_product_id, (row["Product"],))
            product_id = cursor.fetchone()[0]
            cursor.execute(
                insert_product_purchase, (dt, row["Price"], row["Amount"], product_id)
            )
            conn.commit()
            return True
        elif user_input[:2] == "n ":
            if len(user_input) == 2:
                return unregistered_product(row, indices, conn, df, dt, empty_n=True)
            category = user_input[2].upper() + user_input[3:]
            categories = get_categories(conn, list_cat=False)
            if not category in categories:
                cursor.execute(insert_category, (category,))
                conn.commit()
            cursor.execute(find_category_id, (category,))
            category_id = cursor.fetchone()[0]
            cursor.execute(insert_product, (row["Product"], category_id))
            conn.commit()
            cursor.execute(find_product_id, (row["Product"],))
            product_id = cursor.fetchone()[0]
            cursor.execute(
                insert_product_purchase, (dt, row["Price"], row["Amount"], product_id)
            )
            conn.commit()
            return True
        elif user_input == "s":
            return False
        elif user_input[0] == "m":
            if len(user_input) > 2:
                new_name = user_input[2:].upper()
            else:
                print("Please enter modified product name.")
                new_name = prompt(default=row["Product"]).upper()
            cursor.execute(check_product_existence, (new_name,))
            if not cursor.fetchone()[0]:
                row["Product"] = new_name
                print(f"Choose a category [n] to add {new_name} to a category.")
                return unregistered_product(row, conn, indices, df, dt)
            else:
                cursor.execute(find_product_id, (new_name,))
                product_id = cursor.fetchone()[0]
                cursor.execute(
                    insert_product_purchase,
                    (dt, row["Price"], row["Amount"], product_id),
                )
                conn.commit()
                return True
        elif user_input == "d":
            return True
        elif user_input in ("e", "exit", "exit()"):
            save_and_exit(df, indices)
        else:
            print("Please enter a valid input.")
            return unregistered_product(row, conn, indices, df, dt)


def main():
    # get csv name
    csv = sys.argv[1]

    # get connection variables from .env
    load_dotenv()
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_PASSWORD = os.getenv("DB_PASSWORD")

    # connect to the postgreSQL database
    try:
        connection = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
        )
    except psycopg2.OperationalError:
        sys.exit(3)

    # extract time and date from the name
    if csv[-9:] == "_edit.csv":
        time = csv[-17:-9]
        date = csv[-28:-18]
    else:
        time = csv[-12:-4]
        date = csv[-23:-13]
    time = list(time)
    time = [":" if t == "_" else t for t in time]
    time = "".join(time)
    date_time = f"{date} {time}"

    # import csv as dataframe:
    df = pd.read_csv(csv)

    # PSQL cursor:
    cursor = connection.cursor()

    # PSQL commands:
    check_product_existence = (
        "SELECT EXISTS (SELECT 1 FROM products WHERE product_name = %s);"
    )

    find_product_id = "SELECT id FROM products WHERE product_name = %s;"

    insert_product_purchase = """
      INSERT INTO purchases
      (date, price, amount, product_id)
      VALUES (%s, %s, %s, %s);
   """
    # loop through all rows in CSV:
    indices = []
    for index, row in df.iterrows():
        cursor.execute(check_product_existence, (row["Product"],))
        if cursor.fetchone()[0]:  # if product is previously registered
            cursor.execute(find_product_id, (row["Product"],))
            product_id = cursor.fetchone()[0]
            new_purchase = (date_time, row["Price"], row["Amount"], product_id)
            cursor.execute(insert_product_purchase, new_purchase)
            connection.commit()
            indices.append(index)
        else:
            print(
                f'"{row['Product']}" not found. Please register new entry (n), modify product name (m), skip this product (s), delete this product (d) or exit (e).'
            )
            if unregistered_product(row, connection, indices, df, date_time):
                indices.append(index)
    registered_df = df.loc[indices]

    # remove all successfully registered rows:
    df.drop(index=indices, inplace=True)

    # if all rows were successfully registered (and thus removed)
    # exit the script. Otherwise, save partial CSVs first:
    if df.empty:
        sys.exit(0)
    else:
        df.to_csv(f"data/archive/{csv[12:-4]}_mod.csv", index=False)
        registered_df.to_csv(f"data/archive/{csv[12:-4]}_reg.csv", index=False)
        sys.exit(2)


if __name__ == "__main__":
    main()
