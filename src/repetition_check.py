#!/usr/bin/env python3

"""
This script is called in the script record_receipts.sh. Its function is to make sure
the input receipt has not been previously registered in the PSQL table. If a receipt
has been registered previously, the script will have exit code 2.

Usage:
    repetition_check.py yyyy-mm-ddThh_mm_ss.pdf
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv


def main():
    # get the name
    NAME = sys.argv[1]

    # get connection variables from .env
    load_dotenv()
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_PASSWORD = os.getenv("DB_PASSWORD")

    # get time and date
    time = list(NAME[-12:-4])
    time = [":" if t == "_" else t for t in time]
    time = "".join(time)
    date = NAME[-23:-13]
    TIMESTAMP = f"{date} {time}"

    # check if any registered purchase has the same timestamp
    timestamp_existence = "SELECT EXISTS (SELECT 1 FROM purchases WHERE date = %s);"

    # connect to psql database
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

    # PSQL cursor
    cursor = connection.cursor()

    # check if a purchase with the same timestamp exists:
    cursor.execute(timestamp_existence, (TIMESTAMP,))
    # exit script accordingly
    if cursor.fetchone()[0]:
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
