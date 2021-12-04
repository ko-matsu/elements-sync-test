import unittest
import logging
import time
from bitcoinrpc.authproxy import AuthServiceProxy


BTC_FEE_ADDR = 'bcrt1qpaujknvwumkwplvpdlh6gtsv7hrl60a37fc9tx'
WSH_OP_TRUE = \
    '00204ae81572f06e1b88fd5ced7a1a000945432e83e1551e6f721ee9c00b8cc33260'
DYNAFED_FEDPEG_SCRIPT = '5121024241bff4d20f2e616bef2f6e5c25145c068d45a78da3ddba433b3101bbe9a37d51ae'  # noqa: E501
DYNAFED_PAK = [
    '02b6991705d4b343ba192c2d1b10e7b8785202f51679f26a1f2cdbe9c069f8dceb024fb0908ea9263bedb5327da23ff914ce1883f851337d71b3ca09b32701003d05',  # noqa: E501
    '030e07d4f657c0c169e04fac5d5a8096adb099874834be59ad1e681e22d952ccda0214156e4ae9168289b4d0c034da94025121d33ad8643663454885032d77640e3d',   # noqa: E501
]


def generatetoaddress(btc_rpc, count):
    btc_rpc.generatetoaddress(count, BTC_FEE_ADDR)


def generatetoaddress_dynafed(elm_rpc, count):
    for i in range(count):
        # generate dynafed block
        block_data = elm_rpc.getnewblockhex(
            0,
            {
                "signblockscript": WSH_OP_TRUE,
                "max_block_witness": 500,
                "fedpegscript": DYNAFED_FEDPEG_SCRIPT,
                "extension_space": DYNAFED_PAK,
            })
        elm_rpc.submitblock(block_data)


class RpcWrapper:
    def __init__(self, host='127.0.0.1', port=8432,
                 rpc_user='', rpc_password=''):
        self.rpc_connection = AuthServiceProxy('http://{}:{}@{}:{}'.format(
            rpc_user, rpc_password, host, port))

    def command(self, command, *args):
        return self.rpc_connection.command(args)

    def get_rpc(self):
        return self.rpc_connection


class TestElements(unittest.TestCase):
    def setUp(self):
        logging.basicConfig()
        logging.getLogger("BitcoinRPC").setLevel(logging.DEBUG)

        self.btcConn = RpcWrapper(
            host='testing-bitcoin', port=18443, rpc_user='bitcoinrpc', rpc_password='password')
        self.elmConn = RpcWrapper(
            host='testing-elements', port=18447, rpc_user='elementsrpc', rpc_password='password')
        self.elm2Conn = RpcWrapper(
            host='testing-elements2', port=18457, rpc_user='elementsrpc', rpc_password='password')

    def test_bitcoin_elements(self):
        btc_rpc = self.btcConn.get_rpc()
        elm_rpc = self.elmConn.get_rpc()
        elm2_rpc = self.elm2Conn.get_rpc()

        past_btc_chaininfo = btc_rpc.getblockchaininfo()
        past_elm_chaininfo = elm_rpc.getblockchaininfo()
        past_elm2_chaininfo = elm2_rpc.getblockchaininfo()

        # generate
        generatetoaddress(btc_rpc, 10)
        generatetoaddress_dynafed(elm_rpc, 10)
        time.sleep(10)

        btc_chaininfo = btc_rpc.getblockchaininfo()
        elm_chaininfo = elm_rpc.getblockchaininfo()
        elm2_chaininfo = elm2_rpc.getblockchaininfo()

        self.assertGreaterEqual(
            btc_chaininfo['blocks'], past_btc_chaininfo['blocks'] + 9)
        self.assertGreaterEqual(
            elm_chaininfo['blocks'], past_elm_chaininfo['blocks'] + 9)
        self.assertGreaterEqual(
            elm2_chaininfo['blocks'], past_elm2_chaininfo['blocks'] + 9)


if __name__ == "__main__":
    unittest.main()
