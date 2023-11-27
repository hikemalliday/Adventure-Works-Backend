from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from auth import AuthHandler
from schemas import AuthDetails
import sqlite3

app = FastAPI()
auth_handler = AuthHandler()

origins = [
    'http://localhost',
    'http://localhost:8000',
    'http://localhost:8001',
    'http://localhost:5173',
    'http://localhost:5174',
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
     
     users = []
     conn = sqlite3.connect('./master.db')
     c = conn.cursor()
     c.execute("""SELECT * FROM username_and_password""")
     results = c.fetchall()
     
     for user in results:
          users.append(user[0])

     if any(x == body['username'] for x in users):
          raise HTTPException(status_code = 400, detail = 'Username is taken')
     
     hashed_password = auth_handler.get_password_hash(body['password'])
     c.execute(f"INSERT INTO username_and_password VALUES (?, ?, ?)", (body['username'], hashed_password, body['admin']))
     conn.commit()
     conn.close()
     
     print('successful account creation')
     return {'username': body['username'], 'password': body['password']}

@app.post('/login')
def login(auth_details: AuthDetails):
    conn = sqlite3.connect('./master.db')
    c = conn.cursor()
    c.execute("""SELECT * FROM username_and_password""")
    results = c.fetchall()
    
    found_user = None
    admin = False
    
    for user in results:
         print(user)
         if user[1] == auth_details.username:
              found_user = {'username' : user[1], 'hashed_password' : user[2]}
              admin = user[3]
              print('found_user: ')
              print(found_user)
              break
    
    print(found_user['hashed_password'])
    print(auth_handler.verify_password(auth_details.password, found_user['hashed_password']))
    
    if (found_user is None) or (not auth_handler.verify_password(auth_details.password, found_user['hashed_password'])):
          
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
    conn = sqlite3.connect('./master.db')
    c = conn.cursor()
    c.execute("""SELECT product_subcategory_id, name FROM product_subcategory_id""")
    results = c.fetchall()
    
    categories = {}
    for row in results:
         categories[row[0]] = row[1]
     
    c.execute("""SELECT name, list_price, size, product_subcategory_id, color, product_id FROM product""")
    results = c.fetchall()
    array = []
    
    for row in results:
        dictionary = {}
        dictionary['name'] = row[0]
        dictionary['listPrice'] = row[1]
        dictionary['size'] = row[2]
        if row[3]:   
             dictionary['ProductSubcategoryID'] = row[3]
        dictionary['color'] = row[4]
        dictionary['productId'] = row[5]

        if row[1] is None or row[1] == 0:
             dictionary['listPrice'] = 10.00
        if row[3] is not None:
             dictionary['ProductSubcategoryName'] = categories[int(row[3])]
        if row[3]:
             if int(row[3]) in (1, 2, 3):
                dictionary['ProductCategoryID'] = 1
                dictionary['ProductCategoryName'] = 'Bikes'
        if row[3] is not None and 4 <= int(row[3]) <= 17:
             dictionary['ProductCategoryID'] = 2
             dictionary['ProductCategoryName'] = 'Components'
        if row[3] is not None and 18 <= int(row[3]) <= 25:
             dictionary['ProductCategoryID'] = 3
             dictionary['ProductCategoryName'] = 'Clothing'
        if row[3] is not None and 26 <= int(row[3]) <= 37:
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
     
