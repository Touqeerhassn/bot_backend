import requests

response=requests.post(
    "http://localhost:8000/chain/invoke",
    json={'input':{'topic':"my best friend"}})
    

print(response.json()['output']['content'])