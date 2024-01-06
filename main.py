from typing import Annotated
import json
import random

import smtplib, ssl
from pydantic import BaseModel
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from fastapi import FastAPI, HTTPException, Security, Request, status, Form
from fastapi.security import APIKeyHeader
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
adminApi = FastAPI()

origins = ['http://localhost:4000']  

adminApi.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

templates = Jinja2Templates(directory="templates")

### EMAILING
ssl_port = 465
context = ssl._create_unverified_context()
def send_email(sender, sender_password, recipents, subject, contentHTML, contentText):
    msg = MIMEMultipart("alternative")
    
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ', '.join(recipents)
    
    msg.attach(MIMEText(contentText, "plain"))
    msg.attach(MIMEText(contentHTML, "html"))
    
    with smtplib.SMTP_SSL("smtp.gmail.com", ssl_port, context=context) as server:
        server.login(sender, sender_password)
        server.sendmail(sender, recipents, msg.as_string())
class Email(BaseModel):
    subject: str
    bodyText: str
    bodyHTML: str

### JSON DATABASE
mail_list = {}
with open("mailinglist.json") as f:
    mail_list = json.load(f)   
def add_client_to_database(api_key, email):
    if api_key in mail_list:
        mail_list[api_key]["clients"].append(email)
    else:
        mail_list[api_key]["clients"] = [email]
    with open("mailinglist.json", "w") as f:
        json.dump(mail_list, f)
def unsubscribe_client_from_database(api_key, email):
    mail_list[api_key]["clients"].remove(email)
    with open("mailinglist.json", "w") as f:
        json.dump(mail_list, f)

### API KEYS
api_key_header = APIKeyHeader(name="X-API-Key")
with open("apikeys.json") as f:
    api_keys = json.load(f)["api_keys"]
def get_api_key(api_key_header: str = Security(api_key_header)) -> str:
    if api_key_header in api_keys:
        return api_key_header
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API Key",
    )

### PATHS
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.html"
    )

@app.get("/api/get_clients")
def request_get_clients(api_key: str = Security(get_api_key)):
    return {
        "data": {
            "clients": mail_list[api_key]
        }
    }

@app.post("/api/add_client", status_code=status.HTTP_201_CREATED)
def request_add_client(email: Annotated[str, Form()], api_key: str = Security(get_api_key)):
    if email == None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No email provided for new client. Provide via query params (?email=<email here>)."
        )
    
    email = email.strip()
    
    if api_key in mail_list and email in mail_list[api_key]["clients"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered to this api-key."
        )
        
    add_client_to_database(api_key, email)
    
    return {
        "message": "Client Successfully Created", 
        "data": {
            "client": {
                "email": email
            }
        }
    }

@app.post("/api/unsubscribe_client")
def request_unsubscribe_client(email: Annotated[str, Form()], api_key: str = Security(get_api_key)):
    if email == None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No email provided for client. Provide via query params (?email=<email here>)."
        )
    
    email = email.strip()
    
    if (api_key not in mail_list) or (api_key in mail_list and email not in mail_list[api_key]["clients"]):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is not registered to this api-key"
        )
        
    unsubscribe_client_from_database(api_key, email)
    
    return {
        "message": "Client Successfully Unsubscribed", 
        "data": {
            "client": {
                "email": email
            }
        }
    }

@app.post("/api/send_to_clients")
def request_send_mail_to_clients(email: Email, api_key: str = Security(get_api_key)):
    if api_key not in mail_list:
        return {"message": "No clients to send to."}
    
    if "clients" not in mail_list[api_key] or ("clients" in mail_list[api_key] and len(mail_list[api_key]["clients"]) == 0):
        return {"message": "No clients to send to."}
    
    send_email(
        mail_list[api_key]["email"],
        mail_list[api_key]["email_password"],
        mail_list[api_key]["clients"],
        email.subject,
        email.bodyHTML,
        email.bodyText
    )
    
    return {"message": "Success"}

@adminApi.post("/register_new_key")
def register_new_key(sender_email: Annotated[str, Form()], sender_password: Annotated[str, Form()]):
    api_key = ''.join([random.choice("abcdefghijklmnopqrtuvwxyz-0123456789") for i in range(35)])
    api_keys.append(api_key)
    api_keys_data = {
        "api_keys": api_keys
    }
    with open("apikeys.json", "w") as f:
        json.dump(api_keys_data, f)
    
    with open("mailinglist.json", "w") as f:
        mail_list[api_key] = {
            "email": sender_email,
            "email_password": sender_password,
            "clients": []
        }
        json.dump(mail_list, f)
    
    return HTMLResponse(f"<span>Your API KEY is: {api_key}</span>")

app.mount("/api/admin", adminApi)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4000)