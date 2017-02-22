#!/usr/bin/python3

import unittest
from netsandbox import NetworkSandbox


class TestStringMethods(unittest.TestCase):

    def test_namesapce(self):
        import logging
        logging.basicConfig(level=logging.DEBUG)

        with NetworkSandbox() as ns:
            for a in ["10.32.255.254", "10.32.0.1", "10.0.0.2", "127.0.0.1"]:
                p = ns.spawn("ping {} -c 3".format(a))
                p.wait(timeout=10)

if __name__ == '__main__':
    unittest.main()
