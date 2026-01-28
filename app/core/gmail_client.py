import requests 
GMAIL_API_BASE="https://gmail.googleapis.com/gmail/v1"

def list_messages(access_token:str,max_results:int =10):
    url=f"{GMAIL_API_BASE}/users/me/messages"
    headers={
        "Authorization":f"Bearer {access_token}"
    }
    params={
        "maxResults":max_results
    }
    response=requests.get(url,headers=headers,params=params)
    response.raise_for_status()
    return response.json().get("messages",[])

def get_message(access_token:str,message_id:str):
    url=f"{GMAIL_API_BASE}/users/me/messages/{message_id}"
    headers={
        "Authorization":f"Bearer {access_token}"
    }

    response=requests.get(url,headers=headers)
    response.raise_for_status()
    return response.json()