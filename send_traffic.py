import requests

url = "http://localhost:5000/api/process-image"

# API key for the user account
api_key = "sRMWrC0xMWJR0ZcjKl_vnhfBe-VrKx3-FwYybAB7M_w"

# Make sure to use a raw string (r"") so that Windows paths with backslashes are handled properly.
files = {
    "image": open(r"C:\Users\Kingston\PycharmProjects\FIR\Dataset\SGFood\Chicken_Rice_Steamed\Chicken_Rice_Steamed_10.jpg", "rb")
}
data = {"mass": "150"}  # Adjust as needed

headers = {
    "X-API-Key": api_key
}

response = requests.post(url, headers=headers, files=files, data=data)
print(response.json())
