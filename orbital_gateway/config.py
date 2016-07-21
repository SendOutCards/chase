PROCSTATUS_INVALID_RETRY_TRACE = '9714'
PROCSTATUS_USER_NOT_FOUND = '9581'

ELECTRONIC_CHECK = 'EC'

CONSUMER_CHECKING = 'C'  # (US or Canadian)
CONSUMER_SAVINGS = 'S'  # (US Only)
COMMERCIAL_CHECKING = 'X'  # (US Only)
DEPOSIT_ACCOUNT_TYPES = [
    CONSUMER_CHECKING,
    CONSUMER_SAVINGS,
    COMMERCIAL_CHECKING,
]


BEST_POSSIBLE_METHOD = 'B'  # (US Only)
ACH = 'A'   # (US or Canadian)
ECP_PAYMENT_DELIVERY_METHODS = [
    BEST_POSSIBLE_METHOD,
    ACH,
]

CARD_TYPE_VISA = 'Visa'
CARD_TYPE_MC = 'MC'
CARD_TYPE_AMEX = 'Amex'
CARD_TYPE_DISCOVER = 'Discover'
CARD_TYPE_JCB = 'JCB'
CARD_TYPES = [
    CARD_TYPE_VISA,
    CARD_TYPE_MC,
    CARD_TYPE_AMEX,
    CARD_TYPE_DISCOVER,
    CARD_TYPE_JCB,
]

# message types
AUTHORIZE = 'A'
AUTHORIZE_CAPTURE = 'AC'
FORCE_CAPTURE = 'FC'
REFUND = 'R'

MESSAGE_TYPES = [
    AUTHORIZE,
    AUTHORIZE_CAPTURE,
    FORCE_CAPTURE,
    REFUND,
]

# Customer profile actions
CREATE_CUSTOMER = 'C'
READ_CUSTOMER = 'R'
UPDATE_CUSTOMER = 'U'
DELETE_CUSTOMER = 'D'

# CustomerProfileFromOrderInd options
AUTO_GENERATE = 'A'
USE_CUSTOMERREF = 'S'

TEST_ENDPOINT_URL_1 = "https://orbitalvar1.chasepaymentech.com/authorize"
TEST_ENDPOINT_URL_2 = "https://orbitalvar2.chasepaymentech.com/authorize"
ENDPOINT_URL_1 = "https://orbital1.chasepaymentech.com/authorize"
ENDPOINT_URL_2 = "https://orbital2.chasepaymentech.com/authorize"

CURRENT_DTD_VERSION = "PTI68"

AUTH_PLATFORM_BIN = {
    'salem': '000001',
    'pns': '000002'
}


