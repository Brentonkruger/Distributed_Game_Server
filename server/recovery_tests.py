import unittest
import json
import secrets
import socket
import asyncio

class TestingRecovery (unittest.TestCase):
    # works on list
    # add list
    # call function to get next 

    # Testing recovery message broadcast
    def test_recovery_broadcast(self):
        string = ["0.0.0.1", "0.0.0.2", "0.0.0.8", "0.2.0.7", "0.0.0.0"]
        string.sort()
        ip = "0.0.0.1"
        i = string.index(ip)
        print("Index of 0.0.0.1: " + str(i))
        return False

    # Testing recovery response
    def test_recovery_response(self):
        return False

if __name__ == '__main__':
    unittest.main()