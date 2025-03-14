#!/usr/bin/env python3

"""
This script is called within record_receipts.sh. It takes digital receipts
named yyyy-mm-ddThh_mm_ss.pdf, and reads them using pytesseract. It then
saves the contents of the receipt in a csv format in ./data/temp if
everything goes as planned. If inconsistencies are found, a csv will be
saved in ./data/archive instead.

Usage:
    python3 src/read_receipt.py yyy-mm-ddThh_mm_ss.pdf
"""

import pytesseract
import sys
import pandas as pd
from pdf2image import convert_from_path
import subprocess
from prompt_toolkit import prompt


def main():
    # get the name of the pdf
    pdf_name = sys.argv[1]

    # extract time and date from the name
    time = list(pdf_name[-12:-4])
    time = [":" if t == "_" else t for t in time]
    time = "".join(time)
    date = pdf_name[-23:-13]
    date_time = f"{date} {time}"

    # convert pdf to png
    png = convert_from_path(pdf_name, dpi=250)

    # convert png to string
    string = ""
    for page in png:
        string += pytesseract.image_to_string(page, lang="swe", config="--psm 6")

    # replace ',' with '.'
    string = list(string)
    string = ["." if letter == "," else letter for letter in string]
    string = "".join(string)

    # make list divided by new line
    full_list = string.split("\n")

    # find the total price from the receipt
    read_total = None
    read_amount = None
    for line in full_list:
        if read_total is not None and read_amount is not None:
            break
        if line[:6] == "Totalt" and line[-3:] == "SEK":
            try:
                read_total = float(line[7:-4])
            except:
                pass
        elif line[:6] == "Totalt" and line[-5:].lower() == "varor":
            try:
                read_amount = int(line[7:-6])
            except:
                pass

    # remove unwanted information
    indices = []
    for i in range(len(full_list)):
        if full_list[i][:5] == "Orgnr":
            indices.append(i + 1)
        elif full_list[i] == "FRYSVAROR BYTES EJ":
            indices[0] = i + 1
        elif full_list[i][:6] == "Totalt":
            indices.append(i)
        if len(indices) == 2:
            break

    if len(indices) == 1:
        indices.append(-1)

    groc_list = full_list[indices[0] : indices[1]]

    # divide every line into single words
    groc_word_list = [x.split(" ") for x in groc_list]

    # make a list with elements [product, amount, price]
    ordered_list = []
    veggie_price = False
    pant = 0.0
    for x in groc_word_list:
        if x == "FRYSVAROR BYTES EJ":
            continue
        if "Självscanning" in x:
            continue
        # correct cases of "xx. xx" to "xx.xx":
        try:
            if x[-2][-1] == ".":
                try:
                    int(x[-2][:-1])
                    decimal = x.pop()
                    x[-1] += decimal
                except:
                    pass
        except:
            pass
        try:
            if x[-1][0] == ".":
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
            if x[-2] == "." and len(x[-1]) == 2:
                try:
                    last = int(x[-1])
                    first = int(x[-3])
                    x.pop()
                    x.pop()
                    x[-1] = f"{first}.{last}"
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
            """
            if the line starts with a number, it's most likely not a product, but it will be
            equal to itself in all caps, so we avoid this by adding an 'a' before it, so that
            it's not equal in all caps anymore.
            """
            int(x[0][0])  # making sure it's a product
            if not x[:2] == ["4", "CHEESE"]:
                x[0] = f"a{x[0]}"
        except:
            pass
        try:
            float("".join(x)[-4:])
        except ValueError:
            if "".join(x) == "".join(x).upper():
                product = "".join(x)
                ordered_list.append([product, 1, 0.0])
                veggie_price = True
                continue
        if x[0] != x[0].upper() and x[0] != "Soda":
            try:  # check if there's a discount or if it's irrelevant
                discount = abs(float(x[-1]))
                x_mod = "".join(x[:-1])
                if x_mod[-5:] == "kr/kg":  # check if it's vegetable price or discount
                    discount = -discount
                ordered_list[-1][2] -= discount  # subtract the discount
                ordered_list[-1][2] = round(
                    ordered_list[-1][2], 2
                )  # remove round-off errors
            finally:
                continue  # avoid creating a new row
        # register pant (which is also capital letters)
        if x[0] == "+PANT":
            try:
                pant += float(x[-1])
            finally:
                continue
        # change Soda to SODA for consistency
        if x[0] == "Soda":
            x[0] = "SODA"

        product = ""
        amount = 1
        price = 0.0

        try:
            price += float(x[-1])  # tally the price if it exists
            x1 = x[:-1]
        except ValueError:
            x1 = x  # otherwise it will be tallied next iteration
        for y in x1:
            try:
                i = y.index("st")  # check if more than one purchase
                amount = int(y[:i])  # change the amount if there was
            except ValueError:
                try:
                    int(y[:-1])  # check if there's some 380G bs
                    if len(y) <= 2:  # might be 12 pack or something instead
                        product += " " + y
                except ValueError:
                    product += " " + y  # add the product title
        ordered_list.append([product[1:], amount, price])  # add a row to our table

    # make it into a dataframe
    receipt_df = pd.DataFrame(ordered_list, columns=["Product", "Amount", "Price"])

    # check if the data frame is empty
    if receipt_df.empty:
        sys.exit(2)

    # check that total price and amount has been read from the receipt
    if read_total is None and read_amount is None:
        print(
            "Unable to read total price and amount from receipt. Please enter manually. Press enter to open receipt."
        )
        input()
        subprocess.call(["open", pdf_name])
        while True:
            user_input = prompt(default="[price] [amount]")
            if user_input == "exit":
                sys.exit(3)
            try:
                user_input = user_input.split(" ")
                read_total, read_amount = user_input
                read_total = float(read_total)
                read_amount = int(read_amount)
                break
            except:
                print("Please insert price and amount:")
    elif read_total is None:
        print(
            "Unable to read total price from receipt. Please enter manually. Press enter to open receipt."
        )
        input()
        subprocess.call(["open", pdf_name])
        while True:
            user_input = prompt(default="[price]")
            if user_input == "exit":
                sys.exit(3)
            try:
                read_total = float(user_input)
                break
            except:
                print("Please insert price:")
    elif read_amount is None:
        print(
            "Unable to read total amount from receipt. Please enter manually. Press enter to open receipt."
        )
        input()
        subprocess.call(["open", pdf_name])
        while True:
            user_input = prompt(default="[amount]")
            if user_input == "exit":
                sys.exit(3)
            try:
                read_amount = int(user_input)
                break
            except:
                print("Please insert amount:")

    # calculate sum of amounts and prices
    price = receipt_df["Price"].sum()
    amount = receipt_df["Amount"].sum()

    time = list(time)
    time = ["_" if t == ":" else t for t in time]
    time = "".join(time)

    # check for discrepencies in price and amount
    if read_amount != amount or abs(read_total - (price + pant)) > 0.1:
        receipt_df.to_csv(f"./data/archive/{date}T{time}_incorrect.csv", index=False)
        sys.exit(4)
    else:
        receipt_df.to_csv(f"./data/temp/{date}T{time}.csv", index=False)


if __name__ == "__main__":
    main()
