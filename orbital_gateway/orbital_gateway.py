import os
from uuid import uuid4
import xml.etree.ElementTree as ET
import requests
import unicodedata

import config


def remove_control_characters(s):
    """
    Remove unicode characters that will endanger xml parsing on Chase's end
    """
    u = s.decode('unicode-escape')
    return "".join(ch for ch in u if unicodedata.category(ch)[0] != "C")


def sanitize_address_field(s):
    """
    Address fields hould not include any of the following characters:
    % | ^ \ /
    """
    chars = ["%", "|", "^", "\\", "/"]
    return "".join(ch for ch in s if ch not in chars)


def sanitize_phone_field(s):
    """
        Phone Number Format
        AAAEEENNNNXXXX, where
        AAA = Area Code
        EEE = Exchange
        NNNN = Number
        XXXX = Extension
    """
    chars = ["(", ")", "-", "."]
    return "".join(ch for ch in s if ch not in chars)


class Endpoint(object):
    def __init__(self, **kwargs):
        """
        Endpoint takes the following constructor params:
            merchant_id
            username
            password
            trace_number
            production
        """
        self.merchant_id = os.getenv('ORBITAL_MERCHANT_ID') or kwargs.get('merchant_id', '')
        self.username = os.getenv('ORBITAL_USERNAME') or kwargs.get('username', '')
        self.password = os.getenv('ORBITAL_PASSWORD') or kwargs.get('password', '')
        self.trace_number = kwargs.get('trace_number', str(uuid4().node))
        self.production = kwargs.get('production', False)
        if self.production:
            self.url = config.ENDPOINT_URL_1
            self.url2 = config.ENDPOINT_URL_2
        else:
            self.url = config.TEST_ENDPOINT_URL_1
            self.url2 = config.TEST_ENDPOINT_URL_2
        self.dtd_version = 'application/%s' % config.CURRENT_DTD_VERSION
        self.headers = {
            'MIME-Version': "1.1",
            'Content-type': self.dtd_version,
            'Content-transfer-encoding': "text",
            'Request-number': "1",
            'Document-type': "Request",
            'Trace-number': self.trace_number,
            'Interface-Version': "MooreBro 1.01",
            'MerchantID': str(self.merchant_id),
        }
        # there are 2 platform options defined in the orbital gateway chase
        # Salem - BIN 000001
        # PNS - BIN 000002
        self.platform = kwargs.pop('platform', 'salem')

    def get_platform_bin(self):
        try:
            return config.AUTH_PLATFORM_BIN[self.platform.lower()]

        except KeyError:
            raise KeyError('You have supplied an invalid platform identification,'
                           'you can choose `Salem` (Stratus) or `PNS`')

    def make_request(self, xml):
        for i in range(3):
            try:
                result = requests.post(self.url, data=xml, headers=self.headers)
                result.raise_for_status()
            except requests.exceptions.RequestException:
                result = requests.post(self.url2, data=xml, headers=self.headers)
            if result and result.text:
                return result.text

        return "Could not communicate with Chase"

    def convert_amount(self, amount):
        """
        Remove decimal, pad zeros for ints.
        45.25 -> 4525
        54 -> 5400
        """
        if not amount:
            return
        a = amount.split(".")
        if len(a) > 1:
            dec = a[1]
            if len(dec) == 1:
                dec = dec + "0"
            amount = a[0] + dec
        else:
            amount = amount + "00"
        return amount

    @property
    def reversal(self):
        return self.card_type in (
            config.CARD_TYPE_MC, config.CARD_TYPE_DISCOVER, config.CARD_TYPE_VISA
        )

    @property
    def card_type(self):
        cc_num = self.cc_num
        card = None
        try:
            if cc_num[0] == "4":
                card = config.CARD_TYPE_VISA
            elif cc_num[0] == "5":
                card = config.CARD_TYPE_MC
            elif cc_num[:4] == "6011" or cc_num[:2] == "65":
                card = config.CARD_TYPE_DISCOVER
            elif cc_num[:2] in ("34", "37"):
                card = config.CARD_TYPE_AMEX
            elif cc_num[:4] in ("2131", "1800") or cc_num[:2] == "35":
                card = config.CARD_TYPE_JCB
        except IndexError:
            card = None
        return card

    def parse_xml(self, xml_file_name, values, default_value=None):
        xml_file = os.path.join(
            os.path.dirname(__file__), 'templates', xml_file_name
        )
        tree = ET.parse(xml_file)
        root = tree.getroot()
        values['OrbitalConnectionUsername'] = self.username
        values['OrbitalConnectionPassword'] = self.password
        values['BIN'] = self.get_platform_bin()
        values['CustomerBin'] = self.get_platform_bin()
        for key, value in values.items():
            elem = root.find(".//%s" % key)
            if elem is not None:
                elem.text = value or default_value
                if elem.text is not None:
                    elem.text = remove_control_characters(elem.text)
        return ET.tostring(root)

    def parse_result(self, result):
        root = ET.fromstring(result)
        resp_elem = root.getchildren()[0]
        values = {}
        for child_elem in resp_elem:
            values[child_elem.tag] = child_elem.text
        return values


class Profile(Endpoint):
    def __init__(self, **kwargs):
        super(Profile, self).__init__(**kwargs)
        self.name = kwargs.get('name')
        self.address1 = kwargs.get('address1')
        self.address2 = kwargs.get('address2')
        self.city = kwargs.get('city')
        self.state = kwargs.get('state')
        self.country = kwargs.get('country', 'US') # <CustomerCountryCode>
        self.zipCode = kwargs.get('zip_code')
        self.email = kwargs.get('email')
        self.phone = kwargs.get('phone')
        self.xml = None
        # Echeck fields
        self.customer_ref_num = kwargs.get('customer_ref_num')
        self.card_brand = kwargs.get('card_type', '')
        self.ecp_dda_number = kwargs.get('check_account_number')# ECPAccountDDA
        self.bank_account_type = kwargs.get(
            'bank_account_type', config.CONSUMER_CHECKING
        ) # ECPAccountType
        self.routing_number = kwargs.get('routing_number') # ECPAccountRT
        self.ecp_delivery_method = kwargs.get(
            'ecp_delivery_method', config.BEST_POSSIBLE_METHOD
        ) # ECPBankPmtDlv
        # Credit card fields
        self.cc_num = kwargs.get('cc_num', '')
        self.cc_expiry = kwargs.get('cc_expiry')

    @property
    def echeck(self):
        return self.card_brand == config.ELECTRONIC_CHECK

    def sanitize(self):
        if self.name is not None:
            self.name = self.name[:30]
        if self.address1 is not None:
            address1 = sanitize_address_field(self.address1)
            self.address1 = address1[:30]
        if self.address2 is not None:
            address2 = sanitize_address_field(self.address2)
            self.address2 = address2[:30]
        if self.city is not None:
            city = sanitize_address_field(self.city)
            self.city = city[:20]
        if self.state is not None:
            state = sanitize_address_field(self.state)
            self.state = state[:2]
        if self.zipCode is not None:
            self.zipCode = self.zipCode[:5]
        if self.email is not None:
            self.email = self.email[:50]
        if self.phone is not None:
            phone = sanitize_phone_field(self.phone)
            self.phone = phone[:14]

    def parse_result(self, result):
        values = super(Profile, self).parse_result(result)
        for key in ['CustomerName', 'CustomerAddress1', 'CustomerAddress2',
                    'CustomerCity']:
            if key in values and values[key]:
                values[key] = values[key].title()
        return values

    def create(self):
        self.sanitize()
        values = {
            'CustomerMerchantID': self.merchant_id,
            'CustomerProfileAction': config.CREATE_CUSTOMER,
            'CustomerProfileFromOrderInd': config.AUTO_GENERATE,
            'CustomerName': self.name,
            'CustomerAddress1': self.address1,
            'CustomerAddress2': self.address2,
            'CustomerCity': self.city,
            'CustomerState': self.state,
            'CustomerCountryCode': self.country,
            'CustomerZIP': self.zipCode,
            'CustomerEmail': self.email,
            'CustomerPhone': self.phone,
        }
        if self.customer_ref_num:
            values['CustomerProfileFromOrderInd'] = 'S'
            values['CustomerRefNum'] = self.customer_ref_num
        if not self.echeck:
            values['CCAccountNum'] = self.cc_num
            values['CCExpireDate'] = self.cc_expiry
            template = "profile_CU.xml"
        else:
            # add echeck specific fields here
            values['UseCustomerRefNum'] = self.customer_ref_num
            values['ECPAccountDDA'] = self.ecp_dda_number
            values['ECPAccountType'] = self.bank_account_type
            values['ECPAccountRT'] = self.routing_number
            values['ECPBankPmtDlv'] = self.ecp_delivery_method
            template = "echeck_profile_CU.xml"

        self.xml = self.parse_xml(
            template, values, default_value=""
        )
        self.result = self.make_request(self.xml)
        return self.parse_result(self.result)

    def read(self):
        values = {
            'CustomerMerchantID': self.merchant_id,
            'CustomerRefNum': self.customer_ref_num,
            'CustomerProfileAction': config.READ_CUSTOMER,
        }
        self.xml = self.parse_xml("profile_RD.xml", values)
        result = self.make_request(self.xml)
        return self.parse_result(result)

    def update(self):
        self.sanitize()
        values = {
            'CustomerProfileAction': config.UPDATE_CUSTOMER,
            'CustomerProfileFromOrderInd': config.USE_CUSTOMERREF,
            'CustomerMerchantID': self.merchant_id,
            'CustomerRefNum': self.customer_ref_num,
            'CustomerName': self.name,
            'CustomerAddress1': self.address1,
            'CustomerAddress2': self.address2,
            'CustomerCity': self.city,
            'CustomerState': self.state,
            'CustomerCountryCode': self.country,
            'CustomerZIP': self.zipCode,
            'CustomerEmail': self.email,
            'CustomerPhone': self.phone,
            'CCAccountNum': self.cc_num,
            'CCExpireDate': self.cc_expiry,
        }
        self.xml = self.parse_xml("profile_CU.xml", values)
        result = self.make_request(self.xml)
        return self.parse_result(result)

    def destroy(self):
        values = {
            'CustomerProfileAction': config.DELETE_CUSTOMER,
            'CustomerMerchantID': self.merchant_id,
            'CustomerRefNum': self.customer_ref_num,
        }
        self.xml = self.parse_xml("profile_RD.xml", values)
        result = self.make_request(self.xml)
        return self.parse_result(result)


class Order(Endpoint):

    def __init__(self, **kwargs):
        super(Order, self).__init__(**kwargs)
        self.message_type = kwargs.get('message_type')  # <MessageType>
        self.cc_num = kwargs.get('cc_num', '')  # <AccountNum> null for echecks
        self.customer_num = kwargs.get('customer_num')  # <CustomerRefNum>
        self.order_id = kwargs.get('order_id')  # <OrderID>
        self.amount = kwargs.get('amount')  # <Amount>
        self.zipCode = kwargs.get('zip_code')  # <AVSzip>
        self.address1 = kwargs.get('address1')  # <AVSaddress1>
        self.address2 = kwargs.get('address2')  # <AVSaddress2>
        self.city = kwargs.get('city')  # <AVScity>
        self.state = kwargs.get('state')  # <AVSstate>
        self.phone = kwargs.get('phone')  # <AVSphoneNum>
        self.prior_auth_id = kwargs.get('prior_auth_id')  # <PriorAuthID>
        self.tx_ref_num = kwargs.get('tx_ref_num')  # <TxRefNum>
        self.new_customer = kwargs.get('new_customer', False)
        # ECHECK FIELDS
        self.customer_ref_num = kwargs.get('customer_ref_num')
        self.avs_name = kwargs.get('name')  # <AVSname>
        self.card_brand = kwargs.get('card_type', '')  # <CardBrand>
        # <BCRtNum> Bank Routing and Transit Number for the Customer
        self.routing_number = kwargs.get('routing_number')
        # <CheckDDA> Customer DDA Account Number
        self.check_account_number = kwargs.get('check_account_number')
        # <BankAccountType? > Deposit Account Type (Defaults to Consumer Checking)
        self.bank_account_type = kwargs.get(
            'bank_account_type', config.CONSUMER_CHECKING
        )
        # <BankPmtDelv > ECP Payment Delivery method
        self.ecp_delivery_method = kwargs.get(
            'ecp_delivery_method', config.BEST_POSSIBLE_METHOD
        )
        # CREDIT CARD FIELDS
        self.cc_expiry = kwargs.get('cc_expiry')  # <Exp>
        self.cvv_indicator = kwargs.get('cvv_indicator')  # <CardSecValInd>
        self.cvv = kwargs.get('cvv')  # <CardSecVal>

    @property
    def echeck(self):
        return self.card_brand == config.ELECTRONIC_CHECK

    def sanitize(self):
        if self.address1 is not None:
            address1 = sanitize_address_field(self.address1)
            self.address1 = address1[:30]
        if self.address2 is not None:
            address2 = sanitize_address_field(self.address2)
            self.address2 = address2[:30]
        if self.city is not None:
            city = sanitize_address_field(self.city)
            self.city = city[:20]
        if self.state is not None:
            state = sanitize_address_field(self.state)
            self.state = state[:2]
        if self.zipCode is not None:
            self.zipCode = self.zipCode[:5]
        if self.phone is not None:
            phone = sanitize_phone_field(self.phone)
            self.phone = phone[:14]

    def card_sec_val_ind(self):
        """
        Card Security Presence Indicator
        For Discover/Visa
        1     Value is Present
        2     Value on card but illegible
        9     Cardholder states data not available
        Null if not Visa/Discover
        """
        if not self.cvv:
            return None
        if self.cvv_indicator:
            return self.cvv_indicator
        if self.message_type not in (config.AUTHORIZE_CAPTURE, config.AUTHORIZE):
            return None
        # Quick check for card type
        if self.card_type in (config.CARD_TYPE_VISA, config.CARD_TYPE_DISCOVER):
            if self.cc_expiry and len(self.cc_expiry) > 0:
                return "1"
            else:
                return "9"
        return None

    def charge(self):
        self.sanitize()
        values = {
            'MerchantID': self.merchant_id,
            'MessageType': self.message_type or config.AUTHORIZE_CAPTURE,
            'AccountNum': self.cc_num,
            'OrderID': self.order_id,
            'Amount': self.convert_amount(self.amount),
            'AVSzip': self.zipCode,
            'AVSaddress1': self.address1,
            'AVSaddress2': self.address2,
            'AVScity': self.city,
            'AVSstate': self.state,
            'AVSphoneNum': self.phone,
            'PriorAuthID': self.prior_auth_id,
            'TxRefNum': self.tx_ref_num,
        }
        if not self.echeck:
            # CREDIT CARD FIELDS
            template = "order_new.xml"
            cvvi = self.card_sec_val_ind()
            cvv = self.cvv if cvvi == '1' else None
            values['CustomerRefNum'] = self.customer_num
            values['Exp'] = self.cc_expiry
            values['CardSecValInd'] = cvvi
            values['CardSecVal'] = cvv
        else:
            # ECHECK FIELDS
            template = "echeck_order_new.xml"
            values['AVSname'] = self.avs_name
            values['CardBrand'] = self.card_brand
            values['BCRtNum'] = self.routing_number
            values['CheckDDA'] = self.check_account_number
            values['BankPmtDelv'] = self.ecp_delivery_method
            values['BankAccountType'] = self.bank_account_type
            values['UseCustomerRefNum'] = self.customer_ref_num

        if self.new_customer and not self.echeck:
            values['CustomerProfileFromOrderInd'] = "A"
            values['CustomerProfileOrderOverrideInd'] = "NO"

        # Validation, TBD
        if self.message_type not in config.MESSAGE_TYPES:
            pass

        xml = self.parse_xml(template, values)
        result = self.make_request(xml)
        return self.parse_result(result)

    def authorize(self):
        self.message_type = config.AUTHORIZE
        return self.charge()

    def authorize_capture(self):
        self.message_type = config.AUTHORIZE_CAPTURE
        return self.charge()

    def force_capture(self):
        self.message_type = config.FORCE_CAPTURE
        return self.charge()

    def refund(self):
        self.message_type = config.REFUND
        return self.charge()


class MarkForCapture(Endpoint):
    def __init__(self, **kwargs):
        super(MarkForCapture, self).__init__(**kwargs)
        self.order_id = kwargs.get('order_id')
        self.amount = kwargs.get('amount')
        self.tx_ref_num = kwargs.get('tx_ref_num')

    def request(self):
        values = {
            'MerchantID': self.merchant_id,
            'OrderID': self.order_id,
            'Amount': self.convert_amount(self.amount),
            'TxRefNum': self.tx_ref_num,
        }
        xml = self.parse_xml("mark_for_capture.xml", values)
        result = self.make_request(xml)
        return self.parse_result(result)


class Reversal(Endpoint):
    def __init__(self, **kwargs):
        super(Reversal, self).__init__(**kwargs)
        self.tx_ref_num = kwargs.get('tx_ref_num')  # <TxRefNum>
        self.tx_ref_idx = kwargs.get('tx_ref_idx')  # <TxRefIdx>
        self.amount = kwargs.get('amount')  # <AdjustedAmt>
        self.order_id = kwargs.get('order_id')  # <OrderID>
        self.online_reversal_ind = kwargs.get('online_reversal_ind')  # <OnlineReversalInd>

    def reversal(self):
        self.online_reversal_ind = "Y"
        values = {
            'MerchantID': self.merchant_id,
            'TxRefNum': self.tx_ref_num,
            'TxRefIdx': self.tx_ref_idx,
            'OrderID': self.order_id,
            'OnlineReversalInd': self.online_reversal_ind,
        }
        if self.amount:
            values['AdjustedAmt'] = self.convert_amount(self.amount)
        xml = self.parse_xml("reversal.xml", values)
        result = self.make_request(xml)
        return self.parse_result(result)

    def void(self):
        values = {
            'MerchantID': self.merchant_id,
            'TxRefNum': self.tx_ref_num,
            'TxRefIdx': self.tx_ref_idx,
            'OrderID': self.order_id,
        }
        if self.amount:
            values['AdjustedAmt'] = self.convert_amount(self.amount)
        xml = self.parse_xml("reversal.xml", values)
        result = self.make_request(xml)
        return self.parse_result(result)
