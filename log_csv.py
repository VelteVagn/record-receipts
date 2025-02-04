#!/Users/VetleTjora/miniconda3/bin/python3

import sys
import psycopg2
import pandas as pd
from prompt_toolkit import promt

'''
Takes a csv with 3 columns named 'Product', 'Amount' and 'Price' and logs it into a psql table.
'''

def main():
   # get csv name
   csv = sys.argv[1]

   # get password
   pw = sys.argv[2]

   # connect to the postgreSQL database
   connection = psycopg2.connect(
      dbname='receipts_test',
      user='VetleTjora',
      password=pw,
      host='localhost',
      port='5433'
   )

   # extract time and date from the name
   time = list(csv[-12:-4])
   time = [':' if t=='_' else t for t in time]
   time = ''.join(time)
   date = pdf_name[-23:-13]

   # import csv
   csv = pd.read_csv('f./csv/{date}T{time}.csv')

   # PSQL cursor
   cursor = connection.cursor()

   # PSQL commands:
   check_product_existence = 'SELECT EXISTS (SELECT 1 FROM products WHERE product_name = %s);'

   check_category_existence = 'SELECT EXISTS (SELECT 1 FROM categories WHERE category_name = %s);'

   insert_category = 'INSERT INTO categories (category_name) VALUES (%s);'

   insert_product = 'INSERT INTO products (product_name, category_id) VALUES (%s, %s);'

   find_ids = 'SELECT id, category_id FROM products WHERE product_name = %s;'

   find_category_id = 'SELECT id FROM categories WHERE category_name = %s;'

   find_product_id = 'SELECT id FROM products WHERE product_name = %s;'

   check_existing_purchases = 'SELECT 1 FROM purchases WHERE date = %s LIMIT 1;'

   list_categories = 'SELECT category_name FROM categories ORDER BY category_name;'

   insert_product_purchase = '''
      INSERT INTO purchases
      (date, price, amount, product_id)
      VALUES (%s, %s, %s, %s);
   '''


 