from api_test import TestApiClient

client = TestApiClient()
client.register_user(email='gahugga@gmail.com', password='bobby')
user = client.login(email='gahugga@gmail.com', password='bobby')
client.delete_account()