#!/Users/VetleTjora/miniconda3/bin/python3

import sys
from pdf2image import convert_from_path
import pytesseract
import time
import json
import pandas as pd
import logging

logging.basicConfig(level=logging.DEBUG)

# start the timer
start_time = time.perf_counter_ns()

# get the name of the pdf
pdf_name = sys.argv[1]

# get the DPI
dpi = int(sys.argv[2])

# convert pdf to png
png = convert_from_path(pdf_name, dpi=dpi)

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
#for i in range(l):                        CAN PRESUMABLY BE OMITTED 
#   if groc_list[l-i-1] == '':
#      groc_list.pop(l-i-1)

# divide every line into single words
groc_word_list = [x.split(' ') for x in groc_list]

# make a list with elements [product, amount, price]
ordered_list = []
veggie_price = False
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

# debugging
#logging.debug(receipt_df)

# check if the data frame is empty
if receipt_df.empty:
   end_script(2)

# check for inconsistencies
calculated_total = receipt_df['Price'].sum()
calculated_amount = receipt_df['Amount'].sum()

def end_script(exit_code=0):
   end_time = time.perf_counter_ns()
   total_time = end_time - start_time
   result = {"time": total_time}
   print(json.dumps(result))
   sys.exit(exit_code)

if calculated_total == 0:
   end_script(5)

if not read_total:
   end_script(6)

if not read_amount:
   end_script(7)

if calculated_total < read_total - 3 or calculated_total > read_total + 3:
   logging.debug(f'receipt: {read_total}')
   logging.debug(f'price:   {calculated_total}')
   end_script(3)

if calculated_amount != read_amount:
   end_script(4)

end_script()


'''
--------------------------------
codes:
--------------------------------
 0: full success
 1: unforeseen error
 2: empty data frame
 3: wrong total price
 4: wrong total amount
 5: total price is 0
 6: receipt price not found
 7: receipt amount not found

'''




