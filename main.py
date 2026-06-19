import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv
import httpx

# Load the environment variables from the .env file
load_dotenv()

app = FastAPI(title="Google OAuth Sandbox")

# Fetch credentials from environment variables
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

# Quick safety check to make sure variables loaded properly
if not all([CLIENT_ID, CLIENT_SECRET, REDIRECT_URI]):
    raise RuntimeError("Missing one or more environment variables in .env file")

@app.get("/")
def home():
    return {"message": "Go to /docs to test the OAuth flow!"}

@app.get("/login")
def login():
    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope=openid%20profile%20email"
        f"&access_type=offline"
    )
    return RedirectResponse(url=google_auth_url)

@app.get("/auth/callback")
async def auth_callback(code: str = None, error: str = None):
    if error:
        raise HTTPException(status_code=400, detail=f"Google error: {error}")
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code missing.")

    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient() as client:
        token_response = await client.post(token_url, data=token_data)
        if token_response.status_code != 200:
            return {"error": "Failed to fetch token", "details": token_response.json()}
        
        tokens = token_response.json()
        access_token = tokens.get("access_token")

        user_info_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        user_response = await client.get(user_info_url, headers=headers)
        
        if user_response.status_code != 200:
            return {"error": "Failed to fetch user info"}

        user_data = user_response.json()

    return {
        "message": "Login successful!",
        "user_profile": user_data,
        "tokens_received": tokens 
    }