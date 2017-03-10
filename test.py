#!/usr/bin/python3

import unittest
import logging
import subprocess
import time
from netsandbox import NetworkSandbox

logging.basicConfig(level=logging.DEBUG)

class TestStringMethods(unittest.TestCase):

    def test_namespace(self):
        with NetworkSandbox() as ns:
            for a in ["10.1.0.1", "10.1.0.2", "10.0.0.2", "127.0.0.1"]:
                p = ns.spawn("ping {} -c 3".format(a))
                if p.wait(timeout=10) != 0:
                    raise OSError('destination %s is unreachable' % a)

    def test_net_1(self):
        with NetworkSandbox('172.99.56.0/24') as ns:
            for a in ["172.99.56.1", "172.99.56.2", "10.0.0.2", "127.0.0.1"]:
                p = ns.spawn("ping {} -c 3".format(a))
                if p.wait(timeout=10) != 0:
                    raise OSError('destination %s is unreachable' % a)

    # def test_mappings(self):
    #     with NetworkSandbox() as ns:
    #         mapping = {'tcp': {8000: 8000}}
    #         p = ns.spawn("python3 -m http.server 8000", mapping)
    #         subprocess.call("wget http://10.1.0.2:8000 -O -", shell=True)
    #         p.kill()
    #         p.wait(timeout=3)

if __name__ == '__main__':
    unittest.main()
