
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text

from sqlalchemy.orm import sessionmaker
from auth import AuthHandler
from schemas import AuthDetails
import sqlite3

engine_mssql = create_engine("mssql+pyodbc://sa:changeme@DESKTOP-RIAC343\\SQLEXPRESS/AdventureWorks2019?driver=ODBC+Driver+17+for+SQL+Server")
engine_sqlite = create_engine("sqlite:///./.venv/server/master.db")

Session_mssql = sessionmaker(bind = engine_mssql)
session_mssql = Session_mssql()

Session_sqlite = sessionmaker(bind = engine_sqlite)
session_sqlite = Session_sqlite()

app = FastAPI()
auth_handler = AuthHandler()

origins = [
    'http://localhost',
    'http://localhost:8000',
    'http://localhost:8001',
    'http://localhost:5173',
    'http://localhost:5175'
]

app.add_middleware(
    CORSMiddleware,
    allow_origins = origins,
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"]
)

@app.post("/createusernameandpassword", status_code = 201)
def register(body: dict):
     print('test test test')
     # Fetch / GET table 'users', and append the col 'usernames' in the list:
     # query_string = "SELECT username from [AdventureWorks2019].[Person].[UsernameAndPassword]"
     # query = text(query_string)
     # results = session_mssql.execute(query).fetchall()
     users = []
     conn = sqlite3.connect('./master.db')
     c = conn.cursor()
     c.execute("""SELECT * FROM username_and_password""")
     results = c.fetchall()
     
     for user in results:
          users.append(user[0])

     if any(x == body['username'] for x in users):
          raise HTTPException(status_code = 400, detail = 'Username is taken')
     
     # If username does not already exist, create a hashed password
     hashed_password = auth_handler.get_password_hash(body['password'])
     c.execute(f"INSERT INTO username_and_password VALUES (?, ?, ?)", (body['username'], hashed_password, body['admin']))
     conn.commit()
     conn.close()
     # query = text(query_string)
     # session_mssql.execute(query)
     # session_mssql.commit()
     print('success')
     return {'username': body['username'], 'password': body['password']}

@app.post('/login')
def login(auth_details: AuthDetails):

#     query_string = "SELECT username, password, admin FROM [AdventureWorks2019].[Person].[UsernameAndPassword]"
#     query = text(query_string)
#     results = session_mssql.execute(query).fetchall()
     
    conn = sqlite3.connect('./master.db')
    c = conn.cursor()
    c.execute("""SELECT * FROM username_and_password""")
    results = c.fetchall()
    print(results)
    found_user = None
    admin = False
    print('test')
    for user in results:
         
         print(user)
         if user[1] == auth_details.username:
              found_user = {'username' : user[1], 'hashed_password' : user[2]}
              admin = user[3]
              print('found_user: ')
              print(found_user)
              break
    print('test2')
    print(found_user['hashed_password'])
    print(auth_handler.verify_password(auth_details.password, found_user['hashed_password']))
    print('test3')
   
    if (found_user is None) or (not auth_handler.verify_password(auth_details.password, found_user['hashed_password'])):
          print('debug test')
          raise HTTPException(status_code = 401, detail = 'Invalid username and / or password')
    token = auth_handler.encode_token(found_user['username'])
    if admin == 'False':
         admin = False
    else:
         admin = True
    
    return { 'token': token, 'admin': admin }

@app.get('/istokenvalid')
def protected(username = Depends(auth_handler.auth_wrapper)):
     token = auth_handler.encode_token(username)
     return { 'token': token }

@app.get("/initialFetch")
async def initial_fetch():

    print('test initial fetch')
    conn = sqlite3.connect('./master.db')
    c = conn.cursor()
    c.execute("""SELECT product_subcategory_id, name FROM product_subcategory_id""")
    results = c.fetchall()
    print('test test test')
    
    categories = {}
    for row in results:
         categories[int(row[0])] = row[1]
    
    query_string = "SELECT [name], [ListPrice], [Size], [ProductSubcategoryID], [color], [productID] FROM [AdventureWorks2019].[Production].[Product]"
    query = text(query_string)
    results = session_mssql.execute(query).fetchall()
#     
    array = []
    

    for row in results:
        dictionary = {}
        dictionary['name'] = row[0]
        dictionary['listPrice'] = row[1]
        dictionary['size'] = row[2]
        if row[3]:   
             dictionary['ProductSubcategoryID'] = float(row[3])
        else:
             dictionary['ProductSubcategoryID'] = row[3]
        dictionary['color'] = row[4]
        dictionary['productId'] = row[5]
        
    
        if row[1] is None or row[1] == 0:
             dictionary['listPrice'] = 10.00
        if row[3] is not None:
             dictionary['ProductSubcategoryName'] = categories[row[3]]
        if row[3] in (1, 2, 3):
             dictionary['ProductCategoryID'] = 1
             dictionary['ProductCategoryName'] = 'Bikes'
        if row[3] is not None and 4 <= row[3] <= 17:
             dictionary['ProductCategoryID'] = 2
             dictionary['ProductCategoryName'] = 'Components'
        if row[3] is not None and 18 <= row[3] <= 25:
             dictionary['ProductCategoryID'] = 3
             dictionary['ProductCategoryName'] = 'Clothing'
        if row[3] is not None and 26 <= row[3] <= 37:
             dictionary['ProductCategoryID'] = 4
             dictionary['ProductCategoryName'] = 'Accessories'
        if row[3] == None:
             dictionary['ProductCategoryID'] = 5
             dictionary['ProductCategoryName'] = 'Misc'
             dictionary['ProductSubcategoryName'] = 'Hardware'
        
        array.append(dictionary)
    
    conn.commit()
    conn.close()
    return array

@app.put("/editItem")
async def edit_item(body: dict):
     try:
          parameters = {
               'name': body.get('name', None),
               'list_price': body.get('listPrice', None),
               "size": body.get('size', None),
               "color": body.get('color', None),
               "product_id": body.get('productId')
          }

          for key, value in parameters.items():
               if value == 'None':
                    parameters[key] = None
          conn = sqlite3.connect('./master.db')
          c = conn.cursor()
          c.execute("""
                    UPDATE product
                    SET name = ?, list_price = ?, size = ?, color = ?
                    WHERE product_id = ?
                    """, (parameters['name'], parameters['list_price'], parameters['size'], parameters['color'], parameters['product_id']))
          return
     except Exception as e:
          print(str(e))
          return HTTPException(status_code=500, detail="Update failed")
     finally:
          conn.commit()
          conn.close()
     
