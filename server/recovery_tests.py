import unittest
import json
import secrets
import socket
import asyncio
from resources import replica

class TestingRecovery (unittest.TestCase):
    # works on list
    # add list
    # call function to get next 

    # Testing recovery message broadcast
    async def test_recovery_broadcast(self):
        self.rep = replica.replica("127.0.0.1")
        self.rep.start_recovery()
        return False

    # Testing recovery response
    async def test_recovery_help(self):
        self.rep = replica.replica("127.0.0.1")
        self.rep.recovery_help()
        return False

    async def test_recovery_response(self):
        self.rep = replica.replica("127.0.0.1")
        self.rep.recovery_response()
        return False

if __name__ == '__main__':
    unittest.main()