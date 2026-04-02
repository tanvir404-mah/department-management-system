import requests

def send_otp_sms(phone_number, otp_code):
    """
    Sends an OTP SMS using the TextBee API.
    """
    BASE_URL = 'https://api.textbee.dev/api/v1'
    API_KEY = '4080e363-90f8-4f69-9327-0b800dd36bcc'
    DEVICE_ID = '69ce58a04bae50b1a3f8a76e' # Provided by User
    
    message_body = (
    f" CST AUTH Portal Security\n\n"
    f"Your Registration OTP: {otp_code}\n"
    f"This code will expire in 05:00 minutes.\n\n"
    f"Note: Never share your OTP with anyone for security."
)
    
    try:
        response = requests.post(
            f'{BASE_URL}/gateway/devices/{DEVICE_ID}/send-sms',
            json={'recipients': [phone_number], 'message': message_body},
            headers={'x-api-key': API_KEY}
        )
        # Detailed logging for debugging
        print(f"SMS Response Status: {response.status_code}")
        print(f"SMS Response Body: {response.text}")
        
        # Check if the request was successful (200-299)
        return response.ok
    except Exception as e:
        # Log the error or handle it as needed
        print(f"SMS sending error: {e}")
        return False
def send_broadcast_sms(recipients, message):
    """
    Sends a custom broadcast SMS to multiple recipients using TextBee.
    """
    BASE_URL = 'https://api.textbee.dev/api/v1'
    API_KEY = '4080e363-90f8-4f69-9327-0b800dd36bcc'
    DEVICE_ID = '69ce58a04bae50b1a3f8a76e'
    
    try:
        response = requests.post(
            f'{BASE_URL}/gateway/devices/{DEVICE_ID}/send-sms',
            json={'recipients': recipients, 'message': message},
            headers={'x-api-key': API_KEY}
        )
        print(f"Broadcast SMS Status: {response.status_code}")
        return response.ok
    except Exception as e:
        print(f"Broadcast SMS error: {e}")
        return False
