#!/Users/VetleTjora/miniconda3/bin/python3

import sys
import pandas as pd
import re

# get csv
receipt = sys.argv[1]

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

receipt_df = pd.read_csv(receipt)

for product in receipt_df['Product']:
   if re.match(product, r'.*?.*'):
      prod_list = list(product)
      for i in range(len(prod_list)):
         if prod_list[i] == '?':
            prod_list[i] = '_'
      ''.join(prod_list)   