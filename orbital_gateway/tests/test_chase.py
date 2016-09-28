import os
import unittest

from six import add_move, MovedModule
add_move(MovedModule('test_support', 'test.test_support', 'test.support'))
from six.moves import test_support
import vcr

from ..orbital_gateway import Order, Profile, Reversal
from .live_orbital_gateway_certification import Certification


TEST_DATA_DIR = os.path.dirname(__file__)


def create_sequence(current_value):
    # if we are here
    while True:
        yield str(current_value)
        current_value += 1


class TestProfileFunctions(unittest.TestCase):
    def setUp(self):
        # setup test env vars
        self.env = test_support.EnvironmentVarGuard()
        self.env.set('ORBITAL_PASSWORD', 'potato')
        self.env.set('ORBITAL_MERCHANT_ID', '1234')
        self.env.set('ORBITAL_USERNAME', 'yeah')

        self.c = Certification(
            # these just happened to be the unique sequence at the time of the
            # vcrpy recording
            customer_sequence=create_sequence(653048486),
            order_sequence=create_sequence(946033583),
        )
        self.cassette = os.path.join(
            TEST_DATA_DIR, 'certification_requests.yaml'
        )

    def test_cassette(self):
        with vcr.use_cassette(self.cassette):
            self.c.run_all()

