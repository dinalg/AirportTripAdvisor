import mysql.connector
import string
import random
import numpy as np
import pandas as pd
import math

mydb = mysql.connector.connect(
    host = '127.0.0.1',
    user = 'root',
    database = 'tables',
    password = 'dbmerchants'
)

mycursor = mydb.cursor()

mycursor.execute("DROP TABLE User")

# Table for users
mycursor.execute('''CREATE TABLE User(  user_id int, 
                                        firstName varchar(255), 
                                        lastName varchar(255), 
                                        userName varchar(255), 
                                        password varchar(255),
                                        start_iata varchar(255), 
                                        end_iata varchar(255),  
                                        PRIMARY KEY (user_id))''')

# Populating User Table
random.seed()
id = 1
for i in range(1001):
    firstName = ''.join(random.choice(string.ascii_letters) for j in range(5))
    lastName = ''.join(random.choice(string.ascii_letters) for j in range(5))
    userName = ''.join(random.choice(string.ascii_letters) for j in range(5))
    password = ''.join(random.choice(string.ascii_letters) for j in range(5))
    mycursor.execute(f"INSERT INTO User VALUES ({id}, '{firstName}', '{lastName}', '{userName}', '{password}' , 'ORD', 'BWI')")
    id += 1

mydb.commit()
