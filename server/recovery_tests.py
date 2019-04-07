import unittest
import json
import secrets
import socket
import asyncio

class TestingRecovery (unittest.TestCase):
    
    # Testing recovery message broadcast
    def test_recovery_broadcast(self):
        string = "127.0.0.1"
        x = string.split(".")
        print(x)
        return False

    # Testing recovery response
    def test_recovery_response(self):
        return False

if __name__ == '__main__':
    unittest.main()