import unittest

from ..orbital_gateway import Order, Profile, Reversal


def new_profile():
    profile = Profile()
    profile.name = "Test User"
    profile.address1 = "101 Main St."
    profile.address2 = "Apt. 4"
    profile.city = "New York"
    profile.state = "NY"
    profile.zipCode = "10012"
    profile.email = "test@example.com"
    profile.phone = "9089089080"
    profile.cc_num = "4788250000028291"
    profile.cc_expiry = "1116"
    return profile


def new_order():
    return Order()


def new_reversal():
    return Reversal()


class TestProfileFunctions(unittest.TestCase):

    def assert_default_fields(self, result):
        self.assertEqual(result['ProfileProcStatus'], '0')
        self.assertEqual(result['CustomerName'], 'Test User')
        self.assertEqual(result['CustomerAddress1'], '101 Main St.')
        self.assertEqual(result['CustomerAddress2'], 'Apt. 4')
        self.assertEqual(result['CustomerCity'], 'New York')
        self.assertEqual(result['CustomerState'], 'NY')
        self.assertEqual(result['CustomerZIP'], '10012')
        self.assertEqual(result['CustomerEmail'], 'test@example.com')
        self.assertEqual(result['CustomerPhone'], '9089089080')
        self.assertEqual(result['CCAccountNum'], '4788250000028291')
        self.assertEqual(result['CCExpireDate'], '1116')

    def test_lifecycle(self):
        # test profile creation
        profile = new_profile()
        result = profile.create()
        self.assert_default_fields(result)
        customer_ref_num = result['CustomerRefNum']

        # test profile reading
        profile = new_profile()
        profile.customer_ref_num = customer_ref_num
        result = profile.read()
        self.assert_default_fields(result)

        # test profile updating
        profile = new_profile()
        profile.customer_ref_num = customer_ref_num
        profile.name = 'Example Customer'
        profile.city = 'Philadelphia'
        profile.state = 'PA'
        profile.zipCode = '19130'
        result = profile.update()
        self.assertEqual(result['ProfileProcStatus'], '0')
        self.assertEqual(result['CustomerRefNum'], customer_ref_num)
        self.assertEqual(result['CustomerName'], 'Example Customer')
        self.assertEqual(result['CustomerCity'], 'Philadelphia')
        self.assertEqual(result['CustomerState'], 'PA')
        self.assertEqual(result['CustomerZIP'], '19130')
        result = profile.read()
        self.assertEqual(result['ProfileProcStatus'], '0')
        self.assertEqual(result['CustomerName'], 'Example Customer')
        self.assertEqual(result['CustomerAddress1'], '101 Main St.')
        self.assertEqual(result['CustomerAddress2'], 'Apt. 4')
        self.assertEqual(result['CustomerCity'], 'Philadelphia')
        self.assertEqual(result['CustomerState'], 'PA')
        self.assertEqual(result['CustomerZIP'], '19130')
        self.assertEqual(result['CustomerEmail'], 'test@example.com')
        self.assertEqual(result['CustomerPhone'], '9089089080')
        self.assertEqual(result['CCAccountNum'], '4788250000028291')
        self.assertEqual(result['CCExpireDate'], '1116')

        # test profile deletion
        profile = new_profile()
        profile.customer_ref_num = customer_ref_num
        result = profile.destroy()
        self.assertEqual(result['ProfileProcStatus'], '0')
        self.assertEqual(result['CustomerRefNum'], customer_ref_num)


class TestOrderFunctions(unittest.TestCase):

    def test_profile_order(self):
        order_id = '300001'
        self.profile = new_profile()
        result = self.profile.create()
        customer_num = result['CustomerRefNum']
        order = new_order()
        order.customer_num = customer_num
        order.order_id = order_id
        order.amount = '10.00'
        result = order.charge()
        self.assertEqual(result['ProfileProcStatus'], '0')
        txRefNum = result['TxRefNum']
        txRefIdx = result['TxRefIdx']
        self.assertTrue(txRefNum)
        self.assertTrue(txRefIdx)
        refund = new_reversal()
        refund.tx_ref_num = txRefNum
        refund.tx_ref_idx = txRefIdx
        refund.order_id = '100001'
        result = refund.void()
        self.assertEqual(result['ProcStatus'], '0')

    def test_cc_order(self):
        order_id = '200001'
        order = new_order()
        order.order_id = order_id
        order.amount = '10.00'
        order.address1 = "101 Main St."
        order.address2 = "Apt. 4"
        order.city = "New York"
        order.state = "NY"
        order.zipCode = "10012"
        order.email = "test@example.com"
        order.phone = "9089089080"
        order.cc_num = "4788250000028291"
        order.cc_expiry = "1116"
        result = order.charge()
        txRefNum = result['TxRefNum']
        txRefIdx = result['TxRefIdx']
        self.assertTrue(txRefNum)
        self.assertTrue(txRefIdx)
        refund = new_reversal()
        refund.tx_ref_num = txRefNum
        refund.tx_ref_idx = txRefIdx
        refund.order_id = order_id
        result = refund.void()
        self.assertEqual(result['ProcStatus'], '0')


class TestFailover(unittest.TestCase):
    def test_failover_amex(self):
        order_id = '400001'
        order = new_order()
        order.order_id = order_id
        order.url = 'https://bad-url'
        order.amount = '105.00'
        order.address1 = "4 Northeastern Blvd"
        order.address2 = ""
        order.city = "Salem"
        order.state = "NH"
        order.zipCode = "03195"
        order.cc_num = "341134113411347"
        order.ccv = '1234'
        result = order.charge()
        txRefNum = result['TxRefNum']
        txRefIdx = result['TxRefIdx']
        self.assertTrue(txRefNum)
        self.assertTrue(txRefIdx)
        self.assertEqual(result['ProcStatus'], '0')

    def test_failover_discover(self):
        order_id = '400002'
        order = new_order()
        order.url = 'https://bad-url'
        order.order_id = order_id
        order.amount = '105.00'
        order.address1 = "4 Northeastern Blvd"
        order.address2 = ""
        order.city = "Bedford"
        order.state = "NH"
        order.zipCode = "03109"
        order.cc_num = "6559906559906557"
        order.ccv = '613'
        result = order.charge()
        txRefNum = result['TxRefNum']
        txRefIdx = result['TxRefIdx']
        self.assertTrue(txRefNum)
        self.assertTrue(txRefIdx)
        self.assertEqual(result['ProcStatus'], '0')

    def test_failover_mastercard(self):
        order_id = '400003'
        order = new_order()
        order.url = 'https://bad-url'
        order.order_id = order_id
        order.amount = '105.00'
        order.address1 = "Suite 100"
        order.address2 = "5 Northeastern Blvd"
        order.city = "Bedford"
        order.state = "NH"
        order.zipCode = "03101"
        order.cc_num = "5112345112345114"
        order.ccv = '123'
        result = order.charge()
        txRefNum = result['TxRefNum']
        txRefIdx = result['TxRefIdx']
        self.assertTrue(txRefNum)
        self.assertTrue(txRefIdx)
        self.assertEqual(result['ProcStatus'], '0')

    def test_failover_visa(self):
        order_id = '400003'
        order = new_order()
        order.order_id = order_id
        order.amount = '105.00'
        order.url = 'https://bad-url'
        order.address1 = "Apt 2"
        order.address2 = "1 Northeastern Blvd"
        order.city = "Bedford"
        order.state = "NH"
        order.zipCode = "03109-1234"
        order.cc_num = "4112344112344113"
        order.ccv = '411'
        result = order.charge()
        txRefNum = result['TxRefNum']
        txRefIdx = result['TxRefIdx']
        self.assertTrue(txRefNum)
        self.assertTrue(txRefIdx)
        self.assertEqual(result['ProcStatus'], '0')
