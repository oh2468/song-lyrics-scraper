import os
import requests
import json
import time


if __name__ == "__main__":
    api_token_file = "api_token.txt"
    token_file = "bearer_token.txt"
    valid_token = False
    try:
        with open(token_file, "r", encoding="UTF-8") as file:
            auth = json.load(file)
        valid_token =  time.time() <= auth["expires_in"] + auth["created_at"]
    except FileNotFoundError as err:
        pass

    if not valid_token:
        with open(api_token_file, "r", encoding="UTF-8") as file:
            api_token = file.read()
            
        auth_resp = requests.post(
            "https://accounts.spotify.com/api/token",
            data={"grant_type": "client_credentials"},
            headers={"Authorization": api_token}
        )

        if auth_resp.status_code != 200:
            print(auth_resp)
            raise SystemExit("SOMETHING WENT WRONG WITH TRYING RENEW THE TOKEN....")

        auth = auth_resp.json()
        auth["created_at"] = time.time()

        with open(token_file, "w", encoding="UTF-8") as file:
            json.dump(auth, file)
        
        print("Token now updated!")
    else:
        print("Token is still valid!")



