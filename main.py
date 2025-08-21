import logging
import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='twilio_call.log',
    filemode='a'
)

account_sid = os.getenv("ACCOUNT_SID")
auth_token = os.getenv("AUTH_TOKEN")
twilio_number = os.getenv("TWILIO_NUMBER")
config_id = os.getenv("HUME_CONFIG_ID")
api_key = os.getenv("HUME_API_KEY")

if not all([account_sid, auth_token, twilio_number, config_id, api_key]):
    logging.error("Missing one or more required environment variables.")
    raise Exception("Missing required environment variables for Twilio/Hume configuration.")

webhook_url = f"https://api.hume.ai/v0/evi/twilio?config_id={config_id}&api_key={api_key}"

try:
    client = Client(account_sid, auth_token)
    logging.info("Twilio client initialized successfully.")
except Exception as e:
    logging.error(f"Failed to initialize Twilio client: {e}")
    raise Exception("Twilio client initialization error") from e

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"], 
)

@app.get("/", response_class=JSONResponse)
async def index_page():
    return {"message": "Hume AI Call Agent is running!"}

@app.post("/make-call")
def make_call(to_number: str = Query(..., description="Destination phone number")):
    """
    Endpoint to initiate an outbound call using Twilio.
    The destination phone number is provided as a query parameter.
    """
    try:
        logging.info(f"Attempting to make a call from {twilio_number} to {to_number}.")
        call = client.calls.create(
            to=to_number,
            from_=twilio_number,
            url=webhook_url,
            record = True
        )
        logging.info(f"Call SID: {call.sid}")
        logging.info(f"Call status: {call.status}")
        # Return a JSON response with the call SID, status, and HTTP status code
        return JSONResponse(
            content={
                "status_code": 200,
                "message": "Call initiated successfully!",
                "call_sid": call.sid,
                "status": call.status
            }
        )
    except TwilioRestException as e:
        logging.error(f"Twilio REST API error occurred: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)