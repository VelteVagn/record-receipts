#!/Users/VetleTjora/miniconda3/bin/python3

import numpy as np
from PIL import Image
import pytesseract
import psycopg2
import getpass

pw = getpass.getpass(prompt='Password:')

# connect to the postgreSQL database
connection = psycopg2.connect(
   dbname='receipts_test',
   user='VetleTjora',
   password=pw,
   host='localhost',
   port='5433'
)

# Helper functions:

def confirm(msg, function, redo_msg=''):
   '''
   Universal confirmation function. Prints the message msg, waits for input 'y', 'n', or 'exit' from the user. Returns True if 'y', calls and returns the function if 'n' and calls exit() if 'exit'.
   '''
   print('\n' + msg)
   user_input = input().lower()
   if user_input == 'y':
      return True
   elif user_input == 'n':
      print('\n' + redo_msg)
      return function()
   elif user_input == 'exit' or user_input == 'exit()':
      exit()
   else:
      return confirm(msg, function, redo_msg)

def is_nat(s):
   '''
   Checks if a string is strictly an integer. That is 'n' where n is an integer greater or equal to 0.
   '''
   if not isinstance(s, (str, int)):
      print('Input should be string or integer')
      return False
   elif isinstance(s, int):
      return True
   else:
      try:
         [int(i) for i in list(s)]
         return True
      except:
         return False

def is_date_time(s, mode):
   ''' Checks if the string s is in a valid date or time format depending on the mode. '''
   if mode != 'd' and mode != 't':
      raise ValueError('mode must be "d" or "t" for date or time, respectively.')
   if mode == 'd':
      divider = '-'
   else:
      divider = ':'
   l = s.split(divider)
   try:
      a, b, c = [int(i) for i in l]
   except:
      return False
   if len(l) != 3:
      return False
   if len(l[1]) != 2 or len(l[2]) != 2:
      return False
   if mode == 'd':
      if len(l[0]) != 4:
         return False
      if b > 12 or c > 31:
         return False
      if b < 1 or c < 1:
         return False
   else:
      if len(l[0]) != 2:
         return False
      if a > 23 or b > 59 or c > 59:
         return False
   return all([is_nat(n) for n in l])

# load image
def load_receipt():
   '''Loads the receipt called new_receipt.png.'''
   receipt_name = 'new_receipt.png'
   try:
      return Image.open(receipt_name)
   except:
      print('Error: receipt not found.')
      exit()
image = load_receipt()

# extract text
text = pytesseract.image_to_string(image, lang='swe')

# replace ',' with '.'
text = list(text)
text = ['.' if letter == ',' else letter for letter in text]
text = ''.join(text)

# make list divided by new line
text_list = text.split('\n')

# find date and time
date, time = None, None
text_list.reverse() # time and date are at the bottom of the receipt

for line in text_list:
   if date is not None and time is not None:
      break
   words = line.split(' ')
   for word in words:
      if date is None and is_date_time(word, 'd'):
         date = word
         continue
      if time is None and is_date_time(word, 't'):
         time = word
      if date is not None and time is not None:
         break
text_list.reverse()

# time not found
def request_time():
   ''' Asks for user input to register a time of purchase. '''
   global time
   time_input = input().lower()
   if time_input == 'exit' or time_input == 'exit()':
      exit()
   if is_date_time(time_input, 't'):
      msg = f'\nRegister time: {time_input}? [y/n]'
      redo_msg = '\nPlease insert a time. [HH:MM:SS]'
      c = confirm(msg, request_time, redo_msg)
      if c == True:
         time = time_input
   else:
      print('\nPlease provide valid time. [HH:MM:SS]')
      return request_time()

# date not found
def request_date():
   ''' Asks user for input to register a date of purchase. '''
   global date
   date_input = input().lower()
   if date_input == 'exit' or date_input == 'exit()':
      exit()
   if is_date_time(date_input, 'd'):
      msg = f'\nIs {date_input} the correct date? [y/n]'
      redo_msg = '\nPlease input valid date [YYYY-MM-DD].'
      c = confirm(msg, request_date, redo_msg)
      if c == True:
         date = date_input
   else:
      print('\nPlease input valid date [YYYY-MM-DD].')
      return request_date()

# check whether time was found or not
if time is not None:
   confirm(f'Is {time} the correct time? [y/n]', request_time, 'Please enter valid time [HH:MM:SS].')
else:
   print('No time found. Please provide the time of purchase [HH:MM:SS].')
   request_time()

# check whether date was found or not
if date is not None:
   confirm(f'Is {date} the correct date? [y/n]', request_date, 'Please input valid date [YYYY-MM-DD].')
else:
   print('No date found. Please provide the date of purchase [YYYY-MM-DD].')
   request_date()

# time and date
date_time = f'{date} {time}' 

# find the total price from the receipt
total_price = None
for line in text_list:
   if total_price is not None:
      break
   if line[:6] == 'Totalt' and line[-3:] == 'SEK':
      try:
         total_price = float(line[7:-4])
      except:
         pass

# remove unwanted information
indices = []
for i in range(len(text_list)):
   if text_list[i] == 'FRYSVAROR BYTES EJ':
      indices.append(i+1)
   elif text_list[i][:6] == 'Totalt':
      indices.append(i)
   if len(indices) == 2:
      break

if len(indices) == 1:
   indices.append(-1)

text_list = text_list[indices[0]:indices[1]]

# remove blanks
l = len(text_list)
for i in range(l):
   if text_list[l-i-1] == '':
      text_list.pop(l-i-1)

# divide every line into single words
text_list = [x.split(' ') for x in text_list]

# make a list with elements [product, amount, price]
new_list = []
for x in text_list:
   # check if line is a product (products are BOLD as opposed to discounts and the like)
   try:
      int(x[0][0]) # making sure it's a product
      x[0] = f'a{x[0]}'
   except:
      pass
   if x[0] != x[0].upper() and x[0] != 'Soda':
      try: # check if there's a discount or if it's irrelevant
         discount = abs(float(x[-1]))
         x_mod = ''.join(x[:-1])
         if x_mod[-5:] == 'kr/kg': # check if it's vegetable price or discount
            discount = -discount
         new_list[-1][2] -= discount # subtract the discount
         new_list[-1][2] = round(new_list[-1][2], 2) # remove round-off errors 
      finally:
         continue # avoid creating a new row
   # ignore pant (which is also capital letters)
   if x[0] == '+PANT':
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
         i = y.index('st*') # check if more than one purchase
         amount = int(y[:i]) # change the amount if there was
      except ValueError:
         try:
            int(y[:-1]) # check if there's some 380G bs 
            if len(y) <= 2: # might be 12 pack or something instead
               product += ' ' + y
         except ValueError:
            product += ' ' + y # add the product title 
   new_list.append([product[1:], amount, price]) # add a row to our table            

# testing
print(f'new_list: {new_list}')

# make the list into an array for structured output
new_list = np.array(new_list, dtype=object)

# calculate the total price
calc_price = sum(new_list[:,2])

# check that the read price corresponds to the sum on the receipt
if total_price is None:
   print('\nWARNING: Could not extract total price from receipt. Double check to confirm everything is okay.')
elif abs(calc_price-total_price) >= 0.1:
   print('\nWARNING: There is a discrepancy in the total price:\n')
   print(f'Calculated sum: {calc_price}\nSum on receipt: {total_price}\n')
else:
   print('\nNo red flags found.\n')

def delete_prompt(index):
   global new_list
   user_input = input().lower()
   if user_input == 'n':
      return alter_list()
   elif user_input == 'y':
      new_list = list(new_list)
      new_list.pop(index)
      new_list = np.array(new_list)
      print(new_list)
      return alter_list()
   elif user_input == 'exit' or user_input == 'exit()':
      exit()
   else: 
      return delete_prompt()

def delete_row(prompt=True):
   global new_list
   if prompt:
      print('What row number to delete? (index starting at 0)')
   user_input = input()
   try:
      new_list = list(new_list)
      index = int(user_input)
      row = new_list[index]
   except:
      print('Please insert an integer.')
      return delete_row(False)
   print(f'Are you sure you want to delete the row: {row}? [y/n]')
   return delete_prompt(index)

def add_amount():
   amount_input = input()
   try:
      amount_input = float(amount_input)
   except:
      print('Please enter an integer greater than 0.')
      return add_amount()
   amount_int = np.floor(amount_input)
   if amount_input - amount_int != 0:
      print('Please enter an integer.')
      return add_amount()
   amount_input = int(amount_input)
   if amount_input <= 0:
      print('Please enter an integer greater than zero.')
      return add_amount()
   return amount_input

def add_price():
   price_input = input()
   try:
      price = float(price_input)
   except:
      print('Please enter a float.')
      return add_price()
   return round(price, 2)


def add_row(first_time=True):
   global new_list
   if first_time:
      print('Please enter product name.')
      product_input = input().upper()
      row = [product_input]
      print('Please enter purchase amount.')
      row.append(add_amount())
      print('Please enter purchase price.')
      row.append(add_price())
      print('Add the following row? [y/n]')
      print(row)
   user_input = input().lower()
   if user_input == 'y':
      new_list = list(new_list)
      new_list.append(row)
      new_list = np.array(new_list)
      return
   elif user_input == 'exit' or user_input == 'exit()':
      exit()
   elif user_input == 'n':
      print('Redo row? [y/n]')
      user_input = input().lower()
      if user_inout == 'y':
         add_row()
      elif user_input == 'exit' or 'exit()':
         exit()
      elif user_input == 'n':
         return
      else:
         add_row()
   else:
      add_row(False)

def edit_element(coordinates, prompt=True):
   global new_list
   element = new_list[coordinates]
   if prompt:
      print(f'Are you sure you want to edit {element} at row {coordinates[0]} and column {coordinates[1]}? [y/n]')
   user_input = input()
   if user_input == 'y':
      print('Assign a new value.')
      new_element = input().upper()
      print(f'Are you sure you want to change {element} to {new_element}? [y/n]')
      user_input = input().lower()
      if user_input == 'y':
         if coordinates[1] == 0:
            new_list[coordinates] = new_element
         else:
            try:
               new_element = float(new_element)
            except:
               if coordinates[1] == 1:
                  print('Error: The new element must be an integer. Please try again.')
               else:
                  print('Error: The new element must be a rational number. Please try again.')
               return edit_element(coordinates, False)
            if coordinates[1] == 1:
               int_element = np.floor(new_element)
               diff = new_element - int_element
               if diff != 0:
                  print('Error: The new element must be an integer. Please try again.')
                  return edit_element(coordinates, False)
               else:
                  new_element = int(new_element)
            new_list[coordinates] = new_element
   elif user_input == 'n':
      new_element_prompt()
   elif user_input == 'exit' or user_input == 'exit()':
      exit()
   else:
      edit_element(coordinates, False)

def edit_list(prompt=True):
   if prompt:
      print('Please enter row and column number starting from 0 [row column].')
   user_input = input()
   coordinates = user_input.split(' ')
   try:
      coordinates = [int(i) for i in coordinates]
      coordinates = tuple(coordinates)
   except:
      print('Please insert two integers separated with a space [i j] to edit the element in the i-th row in the j-th column.')
      return edit_list(False)
   if len(coordinates) != 2:
      print('Please enter exactly 2 integers.')
      return edit_list(False)
   edit_element(coordinates)

def new_element_prompt(prompt=True):
   print('Do you want to edit another element? [y/n]')
   user_input = input().lower()
   if user_input == 'y':
      edit_list()
   elif user_input == 'n':
      alter_list()
   elif user_input == 'exit' or user_input == 'exit()':
      exit()
   else:
      new_element_prompt(False)

def alter_prompt(first=True):
   if first:
      print('This is the current list. Enter "alter" to make more adjustments, or "return" if the list is good.')
      print(new_list)
   else:
      print('Please enter a valid input.')
   user_input = input()
   if user_input == 'alter':
      return alter_list()
   elif user_input == 'return':
      return
   elif user_input == 'exit' or user_input == 'exit()':
      exit()
   else:
      return alter_prompt(False)

def alter_list(no_prompt=False):
   if not no_prompt:
      print('\nEnter "edit" to edit an element or row, "add" to add a missing row, "delete" to delete a bad row, or "cancel" to go back.')
   else:
      print('Current list:')
      print(new_list)
   user_input = input().lower()
   if user_input == 'edit':
       edit_list()
   elif user_input == 'add':
      add_row()
   elif user_input == 'delete':
      delete_row()
   elif user_input == 'cancel':
      return
   elif user_input == 'exit' or user_input == 'exit()':
      exit()
   else:
      print('Please enter one of the aforementioned options, or "exit" to abort.')
      return alter_list(True)
   return alter_prompt()

def proceed_prompt():
   user_input = input().lower()
   if user_input == 'p' or user_input == 'proceed':
      return
   elif user_input == 'a' or user_input == 'alter':
      return alter_list()
   elif user_input == 'exit' or user_input == 'exit()':
      exit()
   else:
      return proceed_prompt()

print(new_list)
print('\nHere is the list. Do you wish to proceed [p] or alter [a] the list first?')
proceed_prompt()



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

insert_product_purchase = '''
   INSERT INTO purchases
   (date, price, amount, product_id)
   VALUES (%s, %s, %s, %s);
''' 

list_categories = 'SELECT category_name FROM categories ORDER BY category_name;'


def create_new_category(product_name, amount, price, msg=True):
   if msg:
      print(f'Please enter a fitting category name that {product_name} fits into.')
   user_input = input()
   new_category = user_input[0].upper() + user_input[1:].lower()
   cursor.execute(check_category_existence, (new_category,))
   if cursor.fetchone()[0]:
      print('This category already exists.')
   else:
      print(f'You\'re about to create a category called {new_category}. Do you want to proceed? [y/n]')
      new_input = input().lower()
      if new_input == 'y':
         cursor.execute(insert_category, (new_category,))
         connection.commit()
         cursor.execute(find_category_id, (new_category,))
         category_id = cursor.fetchone()[0]
         cursor.execute(insert_product, (product_name, category_id))
         connection.commit()
         cursor.execute(find_product_id, (product_name,))
         product_id = cursor.fetchone()[0]
         new_purchase = (date_time, price, amount, product_id)
         cursor.execute(insert_product_purchase, new_purchase)
         connection.commit()
      elif new_input == 'exit()' or new_input == 'exit':
         exit()
      else:
         return create_new_category(product_name, amount, price, msg=False)


def nonexistent_product(product_name, amount, price, msg=None):
   if msg is None:
      print(f'\n\n{product_name} is not registered. Choose an already existing category, or write "new":\n')
      cursor.execute(list_categories)
      categories = cursor.fetchall()
      for category in categories:
         print(category[0])
   else:
      print(msg)
   user_input = input()
   user_input = user_input[0].upper() + user_input[1:].lower()
   if user_input == 'New':
      print('You are about to create a new category. Proceed? [y/n]')
      second_input = input().lower()
      if second_input == 'y':
         return create_new_category(product_name, amount, price)
      else:
         return nonexistent_product(product_name, amount, price)
   elif (user_input,) in categories:
      cursor.execute(find_category_id, (user_input,))
      category_id = cursor.fetchone()[0]
      cursor.execute(insert_product, (product_name, category_id))
      connection.commit()
      cursor.execute(find_product_id, (product_name,))
      product_id = cursor.fetchone()[0]
      new_purchase = (date_time, price, amount, product_id)
      cursor.execute(insert_product_purchase, new_purchase)
      connection.commit()
   elif user_input == 'Exit' or user_input == 'Exit()':
      exit()
   else:
      new_msg = 'Please enter one of the existing categories as listed above, or write "new" to create a new category.'
      return nonexistent_product(product_name, amount, price, new_msg)

cursor.execute(check_existing_purchases, (date_time,))

found_old_purchase = cursor.fetchone()

def dummy_function():
   return False

if found_old_purchase:
   msg = 'It looks like this purchase is already registered. Are you absolutely sure you want to register this receipt? [y/n]'
   if not confirm(msg, dummy_function, 'Registration cancelled.'):
      exit()
      
for purchase in new_list:
   name, amount, price = purchase
   cursor.execute(check_product_existence, (name,))
   if cursor.fetchone()[0]:
      cursor.execute(find_ids, (name,))
      product_id, category_id = cursor.fetchone()
      new_purchase = (date_time, price, amount, product_id)
      cursor.execute(insert_product_purchase, new_purchase)
      connection.commit()
   else:
      nonexistent_product(name, amount, price)

print('Registering receipt completed.')

