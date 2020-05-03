import unittest
import requests
import random

# This function generates a random sequence of length "length" if length is not None. 
# Else the length is random
def generate_random_sequence(length=None):
    if length is None:
        length = random.randint(3, 10)
    sequence = ""
    for i in range(length):
        sequence += chr(random.randint(97, 122))
    return sequence

ip_users = "http://3.95.137.44"
ip_rides = ""

# The below class inherits from unittest.Testcase. Don't ask me why, but that's the structure.
# The functions with name starting with "test_" are called automatically and no need to call them explicitly.
# If you want to add any more tests, then add a function with a prefix of "test_"
class Tester(unittest.TestCase):
    def test_add_name(self):
        self.__class__.name = generate_random_sequence()
        password = generate_random_sequence(length=40)
        data = {
            "username": self.__class__.name,
            "password": password
        }
        res = requests.put(ip_users + "/api/v1/users", json=data)
        self.assertEqual(res.status_code, 201)

    def test_remove_name(self):
        res = requests.delete(ip_users + "/api/v1/users/" + self.__class__.name)
        self.assertEqual(res.status_code, 200)
    
    def test_list_users(self):
        res = requests.get(ip_users + "/api/v1/users")
        # Testing if status_code is not 500 as there can be many users or none.
        # Nevertheless, the function shouldn't fail.
        self.assertNotEqual(res.status_code, 500)

if __name__ == "__main__":
    unittest.main()