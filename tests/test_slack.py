import requests
import os
import dotenv

dotenv.load_dotenv()

data = {
    "name": "Test User",
    "email": "test@example.com",
    "company": "Test Co",
    "phone": "123-456-7890",
    "itemType": "Technology",
    "itemTitle": "Test Technology",
    "message": "This is a test message"
}

data = {
    "text": f"New Contact Form Submission:\n"
            f"Name: {data['name']}\n"
            f"Email: {data['email']}\n"
            f"Company: {data['company']}\n"
            f"Phone: {data['phone']}\n"
            f"Item Type: {data['itemType']}\n"
            f"Item Title: {data['itemTitle']}\n"
            f"Message: {data['message']}"
}

response = requests.post(
    os.getenv('SLACK_WEBHOOK_URL'),
    json=data
)

print(f"Status Code: {response.status_code}")
print(f"Response Text: {response.text}")