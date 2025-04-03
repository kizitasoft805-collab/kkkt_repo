import os
import requests
import base64
from dotenv import load_dotenv
from sms.models import SentSMS
from django.utils.timezone import now

# Load environment variables
load_dotenv()

# Get Beem API credentials
BEEM_SENDER_NAME = os.getenv("BEEM_SENDER_NAME")
BEEM_API_KEY = os.getenv("BEEM_API_KEY")
BEEM_SECRET_KEY = os.getenv("BEEM_SECRET_KEY")

# Beem API URL
BEEM_URL = "https://apisms.beem.africa/v1/send"

# Ensure credentials are loaded correctly
if not BEEM_API_KEY or not BEEM_SECRET_KEY or not BEEM_SENDER_NAME:
    raise ValueError("❌ Missing Beem API credentials. Check your .env file.")

# Encode API credentials for Authorization header
credentials = f"{BEEM_API_KEY}:{BEEM_SECRET_KEY}"
encoded_credentials = base64.b64encode(credentials.encode()).decode()

def send_sms(to, message, member):
    """
    Sends an SMS via Beem API and stores `request_id` in the database.

    :param to: Phone number of the recipient (e.g., 255741943155)
    :param message: SMS text content
    :param member: ChurchMember instance representing the recipient
    :return: API response with request_id
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {encoded_credentials}"
    }
    
    payload = {
        "source_addr": BEEM_SENDER_NAME,  # Ensure sender name is used
        "encoding": 0,
        "message": message,
        "recipients": [{"recipient_id": 1, "dest_addr": to}]
    }

    try:
        print(f"📩 Sending SMS to {to}...")

        response = requests.post(BEEM_URL, json=payload, headers=headers)
        response_data = response.json()

        print("📩 Beem API Response:", response_data)

        if "request_id" in response_data:
            request_id = response_data["request_id"]

            # Store the sent SMS details in the database
            SentSMS.objects.create(
                recipient=member,
                phone_number=to,
                message=message,
                request_id=request_id,
                status="PENDING",
                sent_at=now()
            )

            print(f"✅ SMS sent successfully. Stored in DB with Request ID: {request_id}")
            return {"success": True, "request_id": request_id}

        else:
            print("⚠️ Beem API did not return a request_id!")
            return {"error": "Beem API did not return request_id"}

    except requests.exceptions.RequestException as e:
        print("❌ Error sending SMS:", str(e))
        return {"error": str(e)}

import os
import requests
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Beem API Credentials
BEEM_API_KEY = os.getenv("BEEM_API_KEY")
BEEM_SECRET_KEY = os.getenv("BEEM_SECRET_KEY")

# Beem API Endpoints
BEEM_BALANCE_URL = "https://apisms.beem.africa/public/v1/vendors/balance"
BEEM_SMS_STATUS_URL = "https://dlrapi.beem.africa/public/v1/delivery-reports"

# Encode credentials for Authorization header
credentials = f"{BEEM_API_KEY}:{BEEM_SECRET_KEY}"
encoded_credentials = base64.b64encode(credentials.encode()).decode()

def check_sms_balance():
    """
    Fetches the total SMS balance from Beem API.
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {encoded_credentials}"
    }

    try:
        response = requests.get(BEEM_BALANCE_URL, headers=headers)

        if response.status_code == 200:
            balance_data = response.json()
            return balance_data.get("data", {}).get("credit_balance", "N/A")
        else:
            return {"error": f"API Error {response.status_code}: {response.text}"}

    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def check_sms_status(dest_addr, request_id):
    """
    Fetches the delivery status of a specific SMS.
    Requires `dest_addr` (recipient's phone number) and `request_id` (transaction ID).
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {encoded_credentials}"
    }

    if not dest_addr or not request_id:
        print("⚠️ Missing `dest_addr` or `request_id` in check_sms_status()")
        return {"error": "Missing dest_addr or request_id"}

    params = {
        "dest_addr": dest_addr,
        "request_id": request_id
    }

    print(f"\n📌 Fetching SMS Status for {dest_addr} (Request ID: {request_id})...")

    try:
        response = requests.get(BEEM_SMS_STATUS_URL, headers=headers, params=params)

        if response.status_code == 200:
            sms_status_data = response.json()
            print(f"✅ Beem API Response for {dest_addr}: {sms_status_data}")

            if isinstance(sms_status_data, list) and len(sms_status_data) > 0:
                return sms_status_data[0].get("status", "UNKNOWN")
            else:
                return "NO DATA"

        else:
            print(f"❌ Error Fetching SMS Status for {dest_addr}: {response.status_code} - {response.text}")
            return {"error": response.text}

    except requests.exceptions.RequestException as e:
        print("❌ Error fetching SMS status:", str(e))
        return {"error": str(e)}





def send_demo_broadcast():
    """
    Sends a sample message to multiple numbers using the send_sms function
    from above. This can be run from the Django shell.
    
    Usage in shell:
    >>> from sms.utils import send_demo_broadcast
    >>> send_demo_broadcast()
    """
    phone_numbers = [
        "255741943155",
        "255619043757",
        "255762954068",
        "255763968849"
    ]
    message = (
        "Hellow, this is a sample message from the church application "
        "using the kkkt mkwawa sender name"
    )

    # If 'member' is required in the `send_sms` signature, you can pass None,
    # or fetch a ChurchMember if you want to store in the SentSMS table.
    # For example, if your DB allows member to be null, do `member=None`.
    # Otherwise you might do: `member = ChurchMember.objects.get(phone_number=... )`
    # or something similar for each phone. For this example, let's pass None.

    for number in phone_numbers:
        print(f"--- Sending to {number} ---")
        # Call your existing send_sms function
        result = send_sms(to=number, message=message, member=None)

        # Optionally print out the result or log it
        print("Result:", result)
        print()
