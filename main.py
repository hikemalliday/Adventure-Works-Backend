import jwt
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, MetaData, Table, text, delete
from sqlalchemy.orm import sessionmaker
from auth import AuthHandler
from schemas import AuthDetails

engine = create_engine("mssql+pyodbc://sa:changeme@DESKTOP-RIAC343\\SQLEXPRESS/AdventureWorks2019?driver=ODBC+Driver+17+for+SQL+Server")
Session = sessionmaker(bind = engine)
session = Session()
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
     # Fetch / GET table 'users', and append the col 'usernames' in the list:
     users = []
     query_string = "SELECT username from [AdventureWorks2019].[Person].[UsernameAndPassword]"
     query = text(query_string)
     results = session.execute(query).fetchall()
     
     for user in results:
          users.append(user[0])

     if any(x == body['username'] for x in users):
          raise HTTPException(status_code = 400, detail = 'Username is taken')
     
     hashed_password = auth_handler.get_password_hash(body['password'])
     query_string = f"INSERT INTO [AdventureWorks2019].[Person].[UsernameAndPassword] VALUES ('{body['username']}' , '{hashed_password}', '{body['admin']}')"

     query = text(query_string)
     session.execute(query)
     session.commit()

     return {'username': body['username'], 'password': body['password']}
     
@app.post('/login')
def login(auth_details: AuthDetails):

    query_string = "SELECT username, password, admin FROM [AdventureWorks2019].[Person].[UsernameAndPassword]"
    query = text(query_string)
    results = session.execute(query).fetchall()
    found_user = None
    admin = False
    for user in results:
         
         print(user)
         if user[0] == auth_details.username:
              found_user = {'username' : user[0], 'hashed_password' : user[1]}
              admin = user[2]
              print('found_user: ')
              print(found_user)
              break
     
    print(auth_handler.verify_password(auth_details.password, found_user['hashed_password']))
    # We need to GET the hashed password from the SQL db, and pass it as second parameter below where 'found_user' is:
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
    # Firstly we need to create the subCat + subCat names object
    query_string = "SELECT [ProductSubcategoryID], [Name] FROM [AdventureWorks2019].[Production].[ProductSubCategory]"
    query = text(query_string)
    results = session.execute(query).fetchall()
    
    categories = {}
    for row in results:
         categories[row[0]] = row[1]
    

    query_string = "SELECT [name], [ListPrice], [Size], [ProductSubcategoryID], [color], [productID] FROM [AdventureWorks2019].[Production].[Product]"
    query = text(query_string)
    results = session.execute(query).fetchall()
    # print(results)
    array = []

    # We have a dict that has 'key=subCatInt / val = "name"
    # We have the subCatInt in results, how can we map?

    for row in results:
        dictionary = {}
        dictionary['name'] = row[0]
        dictionary['listPrice'] = row[1]
        dictionary['size'] = row[2]
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
    
    return array


@app.put("/editItem")
async def edit_item(body: dict):
     try:
          parameters = {
               'x': body.get('name', None),
               'y': body.get('listPrice', None),
               "z": body.get('size', None),
               "a": body.get('color', None),
               "b": body.get('productId')
          }

          for key, value in parameters.items():
               if value == 'None':
                    parameters[key] = None

          query_string_raw = f"UPDATE [AdventureWorks2019].[Production].[Product] SET [name] = :x , [listPrice] = :y , [size] = :z , [color] = :a WHERE [productId] = :b"
          query_string = text(query_string_raw)
          session.execute(query_string, parameters)
          session.commit()
          return
     except Exception as e:
          print(str(e))
          return HTTPException(status_code=500, detail="Update failed")
     finally:
          session.close()
     
     
  