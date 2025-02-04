#!/Users/VetleTjora/miniconda3/bin/python3

import pytesseract
import psycopg2
import sys
import pandas as pd
import subprocess
from prompt_toolkit import prompt

# get the name of the pdf
pdf_name = sys.argv[1]

# get the password
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
time = list(pdf_name[-12:-4])
time = [':' if t=='_' else t for t in time]
time = ''.join(time)
date = pdf_name[-23:-13]
date_time = f'{date} {time}'

# convert pdf to png
png = convert_from_path(pdf_name, dpi=250)

# convert png to string
string = ''
for page in png:
   string += pytesseract.image_to_string(page, lang='swe', config='--psm 6')

# replace ',' with '.'
string = list(string)
string = ['.' if letter == ',' else letter for letter in string]
string = ''.join(string)

# make list divided by new line
full_list = string.split('\n')

# find the total price from the receipt
read_total = None
read_amount = None
for line in full_list:
   if read_total is not None and read_amount is not None:
      break
   if line[:6] == 'Totalt' and line[-3:] == 'SEK':
      try:
         read_total = float(line[7:-4])
      except:
         pass
   elif line[:6] == 'Totalt' and line[-5:].lower() == 'varor':
      try:
         read_amount = int(line[7:-6])
      except:
         pass

# remove unwanted information
indices = []
for i in range(len(full_list)):
   if full_list[i] == 'FRYSVAROR BYTES EJ':
      indices.append(i+1)
   elif full_list[i][:6] == 'Totalt':
      indices.append(i)
   if len(indices) == 2:
      break

if len(indices) == 1:
   indices.append(-1)

groc_list = full_list[indices[0]:indices[1]]

# remove blanks
#l = len(groc_list)
#for i in range(l):
#   if groc_list[l-i-1] == '':
#      groc_list.pop(l-i-1)

# divide every line into single words
groc_word_list = [x.split(' ') for x in groc_list]

# make a list with elements [product, amount, price]
ordered_list = []
veggie_price = False
pant = 0.0
for x in groc_word_list:
   # correct cases of "xx. xx" to "xx.xx":
   try:
      if x[-2][-1] == '.':
         try:
            int(x[-2][:-1])
            decimal = x.pop()
            x[-1] += decimal
         except:
            pass
   except:
      pass
   try:
      if x[-1][0] == '.':
         try:
            int(x[-1][1:])
            decimal = x.pop()
            x[-1] += decimal
         except:
            pass
   except:
      pass
   # correct cases of "xx . xx" to "xx.xx"
   if len(x) > 2:
      if x[-2] == '.' and len(x[-1]) == 2:
         try:
            last = int(x[-1])
            first = int(x[-3])
            x.pop()
            x.pop()
            x[-1] = f'{first}.{last}'
         except:
            continue
   if veggie_price:
      try:
         ordered_list[-1][2] = float(x[-1])
         veggie_price = False
         continue
      except:
         continue
   # check if line is a product (products are BOLD as opposed to discounts and the like)
   try:
      int(x[0][0]) # making sure it's a product
      if not x[:2] == ['4', 'CHEESE']:
         x[0] = f'a{x[0]}'
   except:
      pass
   try:
      float(''.join(x)[-4:])
   except ValueError:
      if ''.join(x) == ''.join(x).upper():
         product = ''.join(x)
         ordered_list.append([product, 1, 0.0])
         veggie_price = True
         continue
   if x[0] != x[0].upper() and x[0] != 'Soda':
      try: # check if there's a discount or if it's irrelevant
         discount = abs(float(x[-1]))
         x_mod = ''.join(x[:-1])
         if x_mod[-5:] == 'kr/kg': # check if it's vegetable price or discount
            discount = -discount
         ordered_list[-1][2] -= discount # subtract the discount
         ordered_list[-1][2] = round(ordered_list[-1][2], 2) # remove round-off errors 
      finally:
         continue # avoid creating a new row
   # ignore pant (which is also capital letters)
   if x[0] == '+PANT':
      try:
         pant += float(x[-1])
      finally:
         continue
   # change Soda to SODA for consistency
   if x[0] == 'Soda':
      x[0] = 'SODA'

   product = ''
   amount = 1
   price = 0.0

   try:
      price += float(x[-1]) # tally the price if it exists
      x1 = x[:-1]
   except ValueError:
      x1 = x # otherwise it will be tallied next iteration
   for y in x1:
      try:
         i = y.index('st') # check if more than one purchase
         amount = int(y[:i]) # change the amount if there was
      except ValueError:
         try:
            int(y[:-1]) # check if there's some 380G bs 
            if len(y) <= 2: # might be 12 pack or something instead
               product += ' ' + y
         except ValueError:
            product += ' ' + y # add the product title 
   ordered_list.append([product[1:], amount, price]) # add a row to our table            

# make it into a dataframe
receipt_df = pd.DataFrame(ordered_list, columns=['Product', 'Amount', 'Price'])

# check if the data frame is empty
if receipt_df.empty:
   print('Error: Groceries unable to be read. Most likely the purchase was only one product. Try entering the purchase manually instead.')
   sys.exit(3)

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


indices = []


# function to exit the python script whilst saving the dataframe
def exit_and_save(partly_success=True):
   global receipt_df
   receipt_df.drop(index=indices)
   i = 1
   while True:
      if i == 1:
         version = ''
      else:
         version = str(i)
      try:
         csv_name = date + time + 'csv' + version + '.csv'
         receipt_df.to_csv(f'~/reciept/.temp_csv{csv_name}', mode='x')
         break
      except FileExistsError:
         i += 1
         pass
   if partly_success:
      sys.exit(2)
   else:
      sys.exit(3)

# function to list all registered categories:
# IMPROVEMENT: Make one max_length for 1st row and one for 2nd row to make spacing more natural.

def get_categories(list_cat):
   cursor.execute(list_categories)
   categories = cursor.fetchall()
   categories = [c[0] for c in categories]
   if list_cat:
      max_length = max([len(c) for c in categories])
      l = len(categories)
      remainder = l % 3
      iterations = int((l - remainder)/3)
      for i in range(iterations):
         j = i*3
         row_list = categories[j:j+3]
         row_string = ''
         for k in row_list:
            space = 3*' ' + (max_length-len(k))*' '
            row_string += k + space
         print(row_string)
      if remainder == 1:
         print(categories[-1])
      elif remainder == 2:
         space = 3*' ' + (max_length-len(categories[-2]))*' '
         print(categories[-2] + space + categories[-1])
   return categories         

# function for user options if a product is not registered
# return True if successfully registered the product and purchase.
def unregistered_product(row):
   user_input = input().lower()
   if user_input == 'n':
      print('Enter one of the existing categories or create a new one:')
      categories = get_categories(list_cat=True)
      new_input = input().lower()
      new_input = new_input[0].upper() + new_input[1:]
      if not new_input in categories:
         cursor.execute(insert_category, (new_input,))
         connection.commit()
      cursor.execute(find_category_id, (new_input,))
      category_id = cursor.fetchone()[0]
      cursor.execute(insert_product, (row['Product'], category_id))
      connection.commit()
      cursor.execute(find_product_id, (row['Product'],))
      product_id = cursor.fetchone()[0]
      cursor.execute(insert_product_purchase, (date_time, row['Price'], row['Amount'], product_id))
      connection.commit()
      return True
   elif user_input[:2] == 'n ':
      if len(user_input) == 2:
         return unregistered_product(row)
      category = user_input[2].upper() + user_input[3:]
      categories = get_categories(list_cat=False)
      # should be made a function (because repetition):
      if not category in categories:
         cursor.execute(insert_category, (category,))
         connection.commit()
      cursor.execute(find_category_id, (category,))
      category_id = cursor.fetchone()[0]
      cursor.execute(insert_product, (row['Product'], category_id))
      connection.commit()
      cursor.execute(find_product_id, (row['Product'],))
      product_id = cursor.fetchone()[0]
      cursor.execute(insert_product_purchase, (date_time, row['Price'], row['Amount'], product_id))
      connection.commit()
      return True
      # end of "function".
   elif user_input == 's':
      return False
   elif user_input[0] == 'm':
      if len(user_input) > 2:
         new_name = user_input[2:].upper()
      else:
         print('Please enter modified product name.')
         new_name = prompt(default=row['Product']).upper()
      cursor.execute(check_product_existence, (new_name,))
      if not cursor.fetchone()[0]:
         row['Product'] = new_name
         print(f'Choose [n] to add {new_name} to a category.')
         return unregistered_product(row)
      else:
         cursor.execute(find_product_id, (new_name,))
         product_id = cursor.fetchone()[0]
         cursor.execute(insert_product_purchase, (date_time, row['Price'], row['Amount'], product_id))
         connection.commit()
         return True
   elif user_input == 'd':
      return True
   elif user_input in ('e', 'exit', 'exit()'):
      exit_and_save()
   else:
      print('Please enter a valid input.')
      return unregistered_product(row)

# function to add groceries (does this need to be a function?) !!!!!!!!!!!!!
def add_groceries():
   global indices, receipt_df
   for index, row in receipt_df.iterrows():
      cursor.execute(check_product_existence, (row['Product'],))
      if cursor.fetchone()[0]:                                      # if product is previously registered
         cursor.execute(find_product_id, (row['Product'],))
         product_id = cursor.fetchone()[0]
         new_purchase = (date_time, row['Price'], row['Amount'], product_id)
         cursor.execute(insert_product_purchase, new_purchase)
         connection.commit()
         indices.append(index)
      else:
         print(f'"{row['Product']}" not found. Please register new entry (n), modify product name (m), skip this product (s), delete this product (d) or exit (e).')
         if unregistered_product(row):
            indices.append(index)
   receipt_df.drop(index=indices)
         

# check for inconsistencies
calculated_total = receipt_df['Price'].sum() - pant
calculated_amount = receipt_df['Amount'].sum()

correct_price = False
correct_amount = False

if not read_total:
   print(f'Total price was not found on the receipt. Please make sure the price on the receipt is equal to {calculated_total}.')
   subprocess.call(['./open_receipt.sh', pdf_name, str(calculated_total)])
elif abs(read_total - calculated_total) >= 1:
   print(f'The price on the receipt is not equal to the calculated price.\nPrice on receipt: {read_total}\nSum of prices:    {calculated_total}')
else:
   correct_price = True

if not read_amount:
   print(f'Total amount was not found on the receipt. Please make sure the total amount on the receipt is equal to {calculated_total}.')
   subprocess.call(['./open_receipt.sh', pdf_name, str(calculated_amount)])
elif read_amount != calculated_amount:
   print(f'The amount on the receipt is not equal to the calculated amount.\nAmount on receipt: {read_amount}\nSum of amounts:    {calculated_amount}')
else:
   correct_amount = True

if correct_price and correct_amount:
   print('No red flags. Proceeding with the registration.')
else:
   print(receipt_df)
   exit_and_save(False) 

add_groceries()

sys.exit(0)

'''
REMINDERS:
--------------------------------
sys.exit(0) # successful exit
            # delete the OG receipt
sys.exit(1) # partly successful exit (csv saved with remaining purchases)
            # rename the OG receipt
sys.exit(2) # failed exit
            # leave the OG receipt be (or maybe rename?)

'''
