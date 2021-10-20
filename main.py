from typing import Optional
import motor.motor_tornado
from fastapi.responses import JSONResponse
from fastapi import FastAPI, Response
#from fastapi.templating import template
from bson import ObjectId
import re
import asyncio
app = FastAPI()

#connection to db
client = motor.motor_tornado.MotorClient()
client = motor.motor_tornado.MotorClient('mongodb+srv://zupay_demo:zupay*123@cluster.pubwu.mongodb.net/myFirstDatabase?retryWrites=true&w=majority')
db = client.zupay_db


#db func
async def db_insert(data,collection):
    result = await db[collection].insert_one(data)
    if not result.acknowledged:
        return -1
    return result.inserted_id

async def db_find_one(data,collection):
    result = await db[collection].find_one(data)
    return result

async def db_find_many(data,collection):
    result = []
    cursor = db[collection].find(data)
    count = await db[collection].count_documents(data)
    for document in await cursor.to_list(length=count):
        result.append(document)
    return result

async def db_delete(data,collection):
    result = await db[collection].delete_many(data)
    if not result.acknowledged:
        return -1
    return result.deleted_count

async def db_update(curr_val,new_val,collection):
    print(curr_val,new_val)
    old_document = await db_find_one(curr_val, collection)
    if old_document == None:
        return -1
    # _id = old_document['_id']
    result = await db[collection].update_one(curr_val,{'$set': new_val})
    if not result.acknowledged:
        return -1
    return 1

#################### HELPER FUNCS ###########################
def is_passowrd_match(user_record, password):
    return hash(password) == user_record['password']

async def email_sanitization(email):
    match = re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', email)
    if match == None:
        return -1
    return 0


################### END OF HELPER FUNS #######################

#API
@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/signup")
async def sign_up(user_name,email,password):
    print(user_name,email,password)
    if await email_sanitization(email) == -1:
        print("invalid email format")
        return JSONResponse(status_code=400,content={"message":"email syntax is wrong"})
    result = await db_find_one({"email":email}, 'users')
    if result != None:      
        print("email already exists")
        return JSONResponse(status_code=400,content={"message":"email already exists"})
    data = {"user_name":user_name,"email":email,"password":hash(password)}
    if await db_insert(data, 'users') == -1:
        print("failed to add info to db")
        return JSONResponse(status_code=400,content={"message":"failed to add info to db"})
    return JSONResponse(status_code=200,content={"message":"signup completed"})

@app.post("/login")
async def login(email,password):
    result = await db_find_one({"email":email}, 'users')
    if result == None:  
        print("no matching records found")
        return JSONResponse(status_code=400,content={"message":"no matching user found with this user name"})
    if is_passowrd_match(result, password):
        print("login successful")
        print(hash(password))
        return JSONResponse(status_code=200,content={"message":"login completed","id":str(result['_id'])})
    else:
        print("incorrect password")
        print(hash(password))
        return JSONResponse(status_code=400,content={"message":"incorrect password"})

@app.post("/add_todo")
async def add_todo(user_id,title,description):
    try:
        result = await db_find_one({"_id":ObjectId(user_id)},"users")
    except Exception as e:
        print(e)
        return JSONResponse(status_code=400,content={"message":"no such userid exists"})
    if result == None:
        print("no user with this id exists")
        return JSONResponse(status_code=400,content={"message":"no such userid exists"})
    #result = await db_find_one({"id":id,"title":title},"tasks")
    #if result != None:
    #    print("todo task already exists")
    #    return JSONResponse(status_code=400,content={"message":"todo task already exists"})
    data = {"user_id":user_id,"title":title,"description":description,"task_state":0}
    result = await db_insert(data,"tasks")
    if result == -1:
        print("failed to add info to db")
        return JSONResponse(status_code=400,content={"message":"failed to add info to db"})
    return JSONResponse(status_code=200,content={"message":"addition of task completed"})

@app.post("/delete_todo")
async def delete_todo(user_id,task_id):
    try:
        result = await db_find_one({"_id":ObjectId(user_id)},"users")
    except Exception as e:
        print(e)
        return JSONResponse(status_code=400,content={"message":"no such userid exists"})
    if result == None:
        print("no user with this id exists")
        return JSONResponse(status_code=400,content={"message":"no such userid exists"})
    result = await db_find_one({"_id":ObjectId(task_id)},"tasks")
    if result == None:
        print("no todo task exists with given title with this user_id")
        return JSONResponse(status_code=400,content={"message":"no todo task exists with given title with this user_id"})
    result = await db_delete(result,"tasks")
    if result == -1:
        print("failed to delete todo task")
        return JSONResponse(status_code=400,content={"message":"failed to delete todo task"})
    return JSONResponse(status_code=200,content={"message":"deletion of task completed"})

@app.put("/update_task_state")
async def update_task_state(user_id,task_id):
    try:
        result = await db_find_one({"_id":ObjectId(user_id)},"users")
    except Exception as e:
        print(e)
        return JSONResponse(status_code=400,content={"message":"no such userid exists"})
    if result == None:
        print("no user with this id exists")
        return JSONResponse(status_code=400,content={"message":"no such userid exists"})
    result = await db_update({'_id':ObjectId(task_id),'user_id':ObjectId(user_id)},{'task_state':1},"tasks")
    if result < 0:
        print("failed to update todo task state")
        return JSONResponse(status_code=400,content={"message":"failed to update todo task state"})
    return JSONResponse(status_code=200,content={"message":"updation of task state completed"})

@app.post("/modify_task")
async def modify_task(user_id,task_id,new_description):
    try:
        result = await db_find_one({"_id":ObjectId(user_id)},"users")
    except Exception as e:
        print(e)
        return JSONResponse(status_code=400,content={"message":"no such userid exists"})
    if result == None:
        print("no user with this id exists")
        return JSONResponse(status_code=400,content={"message":"no such userid exists"})
    result = await db_update({"_id":ObjectId(task_id)},{"description":new_description},"tasks")
    if result < 0:
        print("failed to update todo task description")
        return JSONResponse(status_code=400,content={"message":"failed to update todo task description"})
    return JSONResponse(status_code=200,content={"message":"updation of task description completed"})

@app.get("/show_all_todo_tasks/{user_id}")
async def show_all_todo_tasks(user_id):
    try:
        result = await db_find_one({"_id":ObjectId(user_id)},"users")
    except Exception as e:
        print(e)
        return JSONResponse(status_code=400,content={"message":"no such userid exists"})
    if result == None:
        print("no user with this id exists")
        return JSONResponse(status_code=400,content={"message":"no such userid exists"})
    result = await db_find_many({'user_id':user_id},'tasks')
    for i in result:
        i['_id'] = str(i['_id'])
    return JSONResponse(status_code=200,content=result)
    