# Adventure-Works-Backend
### Backend server for [Adventure-Works](https://github.com/hikemalliday/Adventure-Works)

##### Docker Hub:
https://hub.docker.com/repository/docker/hikemalliday/adventure-works-backend/general

The backend server handles all query logic, log-in/log-out logic, as well as usernames and passwords. 

The API route handling is created with FastAPI. JWT's are created using PyJWT, and the passwords are encrypted using CryptContext. 

I oringally was using the Adventure Works database, running on MSSQL, but in order to showcase the project on a deployed website, I pulled all the data I need from the SQL database and stored it in a SQLite database instead.
