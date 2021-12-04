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
    '030e07d4f657c0c169e04fac5d5a8096adb099874834be59ad1e681e22d952ccda0214156e4ae9168289b4d0c034da94025121d33ad8643663454885032d77640e3d',  # noqa: E501
]
SIGNBLOCK_PRIVKEY = 'cSsx8QSjhbmuRkkHLgimDMn33aruGeZW9bZR68AP9NyuWBh2pqED'
SIGNBLOCK_WPKH = '00141dc71237c712e65d80bad8ddeaf2f9eb93786249'
SIGNBLOCK_WPKH_ADDRESS = 'ert1qrhr3yd78ztn9mq96mrw74uheawfhscjfqk93s0'
SIGNBLOCK_WSH = '0020553f7e34a30d24eea90f64c54d30dd875095ea95331e952b8bdd98cfac8f6505'  # noqa: E501
SIGNBLOCK_WSH_ADDRESS = 'ert1q25lhud9rp5jwa2g0vnz56vxasagft654xv0f22utmkvvlty0v5zs833rnq'  # noqa: E501
SIGNBLOCK_WSH_WITNESS_SCRIPT = '5121038c4d1d8df94497042cee07847d7258c0aed73165aed971c12c383d75a911067a51ae'  # noqa: E501
SIGNBLOCK_WSH_DESCRIPTOR = 'wsh(multi(1,038c4d1d8df94497042cee07847d7258c0aed73165aed971c12c383d75a911067a))#679ym4m4'  # noqa: E501

# signblock test type. (wpkh/wsh/notSign)
SIGNBLOCK_TYPE = 'notSign'


def generatetoaddress(btc_rpc, count):
    btc_rpc.generatetoaddress(count, BTC_FEE_ADDR)


def get_block_data(elm_rpc, block_hex) -> str:
    chaininfo = elm_rpc.getblockchaininfo()
    if chaininfo['current_signblock_hex'] == SIGNBLOCK_WPKH:
        sigs = elm_rpc.signblock(block_hex, '')
        signed_data = elm_rpc.combineblocksigs(block_hex, sigs, '')
        assert signed_data['complete']
        signed_block = signed_data['hex']
    elif chaininfo['current_signblock_hex'] == SIGNBLOCK_WSH:
        sigs = elm_rpc.signblock(block_hex, SIGNBLOCK_WSH_WITNESS_SCRIPT)
        signed_data = elm_rpc.combineblocksigs(
            block_hex, sigs, SIGNBLOCK_WSH_WITNESS_SCRIPT)
        assert signed_data['complete']
        signed_block = signed_data['hex']
    else:
        signed_block = block_hex
    return signed_block


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
        block_hex = get_block_data(elm_rpc, block_data)
        elm_rpc.submitblock(block_hex)


def generatetoaddress_dynafed_signed_p2wpkh(elm_rpc, count):
    for i in range(count):
        # generate dynafed block
        block_data = elm_rpc.getnewblockhex(
            0,
            {
                "signblockscript": SIGNBLOCK_WPKH,
                "max_block_witness": 500,
                "fedpegscript": DYNAFED_FEDPEG_SCRIPT,
                "extension_space": DYNAFED_PAK,
            })
        signed_block = get_block_data(elm_rpc, block_data)
        elm_rpc.submitblock(signed_block)


def generatetoaddress_dynafed_signed_multisig(elm_rpc, count):
    for i in range(count):
        # generate dynafed block
        chaininfo = elm_rpc.getblockchaininfo()
        block_data = elm_rpc.getnewblockhex(
            0,
            {
                "signblockscript": SIGNBLOCK_WSH,
                "max_block_witness": 500,
                "fedpegscript": DYNAFED_FEDPEG_SCRIPT,
                "extension_space": DYNAFED_PAK,
            })
        signed_block = get_block_data(elm_rpc, block_data)
        elm_rpc.submitblock(signed_block)


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

    def test_bitcoin_elements_signblock(self):
        btc_rpc = self.btcConn.get_rpc()
        elm_rpc = self.elmConn.get_rpc()
        elm2_rpc = self.elm2Conn.get_rpc()

        past_btc_chaininfo = btc_rpc.getblockchaininfo()
        elm_rpc.getblockchaininfo()

        # load wallet
        is_load = False
        try:
            elm_rpc.createwallet('wallet')
        except Exception as err:
            print('Exception({})'.format(err))
            is_load = 'Database already exists.' in str(err)
        if is_load:
            try:
                elm_rpc.loadwallet('wallet')
            except Exception as err:
                print('Exception({})'.format(err))

        # import privkey
        try:
            elm_rpc.importprivkey(SIGNBLOCK_PRIVKEY, 'signblock', True)
            time.sleep(1)
            elm_rpc.importaddress(SIGNBLOCK_WPKH_ADDRESS, 'signblock', True)
        except Exception as err:
            print('Exception({})'.format(err))
        try:
            elm_rpc.importmulti(
                [{
                    'desc': SIGNBLOCK_WSH_DESCRIPTOR,
                    'timestamp': 'now',
                }])
        except Exception as err:
            print('Exception({})'.format(err))

        # generate
        generatetoaddress(btc_rpc, 10)
        if SIGNBLOCK_TYPE == 'wpkh':
            # start dynafed
            generatetoaddress_dynafed_signed_p2wpkh(elm_rpc, 10)
            past_elm_chaininfo = elm_rpc.getblockchaininfo()
            past_elm2_chaininfo = elm2_rpc.getblockchaininfo()
            time.sleep(1)
            # start sign block
            generatetoaddress_dynafed_signed_p2wpkh(elm_rpc, 10)
            # generatetoaddress_dynafed_signed_multisig(elm_rpc, 10)
        elif SIGNBLOCK_TYPE == 'wsh':
            # start dynafed
            generatetoaddress_dynafed_signed_multisig(elm_rpc, 10)
            past_elm_chaininfo = elm_rpc.getblockchaininfo()
            past_elm2_chaininfo = elm2_rpc.getblockchaininfo()
            time.sleep(1)
            # start sign block
            generatetoaddress_dynafed_signed_multisig(elm_rpc, 10)
        else:
            past_elm_chaininfo = elm_rpc.getblockchaininfo()
            past_elm2_chaininfo = elm2_rpc.getblockchaininfo()
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
