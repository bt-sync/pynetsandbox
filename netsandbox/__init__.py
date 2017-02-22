import subprocess
import os
import binascii
import random
import logging

logger = logging.getLogger(__name__)


class NetworkNamespace(object):

    def __init__(self, name):
        self.name = name
        subprocess.check_output("ip netns add " + self.name, shell=True)

    def release(self):
        subprocess.check_output("ip netns delete " + self.name, shell=True)

    def call(self, cmds):
        for cmd in cmds:
            cmd = "ip netns exec %s %s" % (self.name, cmd)
            logger.debug(cmd)
            subprocess.check_output(cmd, shell=True)

    def spawn(self, cmd):
        cmd = "ip netns exec %s %s" % (self.name, cmd)
        logger.debug(cmd)
        return subprocess.Popen(cmd, shell=True)


class NetworkSandbox(object):

    def __init__(self):
        self.token = binascii.b2a_hex(os.urandom(4)).decode()
        self.namespaces = []
        self.counter = 1

        self.setup()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.release()
        return self

    def call(self, cmds, check=True):
        sub = {
            'i': self.counter,
            'token': self.token
        }
        cmds = [i.format(**sub) for i in cmds]

        if check:
            for cmd in cmds:
                logger.debug(cmd)
                subprocess.check_output(cmd, shell=True)
        else:
            for cmd in cmds:
                logger.debug(cmd)
                subprocess.call(cmd, shell=True)

    def setup(self):
        cmd = [
            "brctl addbr br-router-{token}",
            "ip link set up br-router-{token}",
            "ip addr add 10.32.255.254/16 dev br-router-{token}",
            "iptables -A INPUT -d 10.32.255.254/16 -p icmp -j ACCEPT"
        ]

        self.call(cmd)

    def release(self):
        for n in self.namespaces:
            n.release()

        self.call(["ip link del br-router-{token}"], check=False)

    def spawn(self, command):
        router_ns = NetworkNamespace(
            "%s_router%d" % (self.token, self.counter))
        process_ns = NetworkNamespace(
            "%s_process%d" % (self.token, self.counter))

        self.namespaces.append(router_ns)
        self.namespaces.append(process_ns)

        def preprocess(cmds):
            sub = {
                'router_ns': router_ns.name,
                'process_ns': process_ns.name,
                'i': self.counter,
                'token': self.token
            }
            return [i.format(**sub) for i in cmds]

        cmd = [
            "ip link add r{i}-{token} type veth peer name wan",
            "ip link set up r{i}-{token}",
            "brctl addif br-router-{token} r{i}-{token}",
            "ip link set wan netns {router_ns}",
        ]

        self.call(preprocess(cmd))

        cmd = [
            "ip link set up lo",

            "ip link set up wan",
            "ip addr add 10.32.0.{i}/16 dev wan",
            "ip route add default via 10.32.255.254",

            "ip link add to_process type veth peer name to_router",
            "ip link set to_router netns {process_ns}",
            "ip addr add 10.0.0.1/24 dev to_process",
            "ip link set up to_process",

            "iptables -A INPUT -p icmp -j ACCEPT",
            "iptables -P INPUT DROP",
            "iptables -t nat -A POSTROUTING -p udp -o wan -j MASQUERADE --to-ports 4000",
            "iptables -t nat -A POSTROUTING -p icmp -o wan -j MASQUERADE",
            "iptables -A FORWARD -o wan -j ACCEPT",
            "iptables -A FORWARD -m state --state ESTABLISHED,RELATED -j ACCEPT",
        ]
        router_ns.call(preprocess(cmd))

        cmd = [
            "ip link set up lo",

            "ip addr add 10.0.0.2/24 dev to_router",
            "ip link set up to_router",
            "ip route add default via 10.0.0.1",

            "iptables -P INPUT ACCEPT",
            "iptables -P OUTPUT ACCEPT",
            "iptables -P FORWARD DROP"
        ]
        process_ns.call(preprocess(cmd))
        self.counter += 1

        return process_ns.spawn(command)
