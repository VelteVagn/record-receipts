#!/usr/bin/env python3

import os
import sys
import psycopg2
from dotenv import load_dotenv
import getpass

def main():

    # get connection variables from .env
    load_dotenv()
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    
    # check if password is needed
    try:
        connection = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            host=DB_HOST,
            port=DB_PORT,
        )
        connection.close()
        sys.exit(0)
    except psycopg2.OperationalError:
        sys.exit(2)
    '''
        DB_PWD = getpass.getpass("Password: ")
        try:
            connection = psycopg2.connect(
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PWD,
                host=DB_HOST,
                port=DB_PORT,
            )
            connection.close()
            print(DB_PWD)
            sys.exit(0)
        except psycopg2.OperationalError:
            print("Unable to connect to psql server. Possibly wrong password. Try again.")
            sys.exit(2)
    '''
if __name__ == "__main__":
    main()