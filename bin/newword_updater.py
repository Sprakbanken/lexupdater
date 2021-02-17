#!/usr/bin/env python
# coding=utf-8

import sqlite3



if __name__ == "__main__":
    try:
        sqliteConnection = sqlite3.connect('../../backend-db_test.db')
        print("Successfully Connected to SQLite")
        # Run tests
        
    except sqlite3.Error as error:
        print("Error while creating a sqlite table", error)
    finally:
        if (sqliteConnection):
            sqliteConnection.close()
            print("sqlite connection is closed")