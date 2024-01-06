![cover image for simply mail](/assets/images/cover.png)
 (UNFINISHED)A simple mail client that uses http requests to add and unsubscribe users, get a list of all users, and send batch emails. Great for integrating into a website with ease.

## Python Setup:
Create a virtual environment via: `python -m venv venv`

Activate the virtual enviorment with:\
Mac and Linux: `source venv/bin/activate`\
Windows: `.\venv\Scripts\activate.bat`

Install via `pip install requirements.txt`

## Json Setup:
apikeys.json
```
{
    "api_keys": ["<api-key-goes-here>"]
}
```

mailinglist.json
```
{
    "<api-key-goes-here>": {
        "email": "<sending-email (GMAIL ONLY)>",
        "email_password": "<sending-email-password>",
        "clients":["<client-email>", "<client-email>"]
    }
}
```
