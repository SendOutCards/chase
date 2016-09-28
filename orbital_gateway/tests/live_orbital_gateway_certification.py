from copy import deepcopy
import csv
import datetime
import random
import six

from .. import orbital_gateway
from . import orbital_gateway_test_data as td


def uniqueids():
    """
    usage:
    unique_sequence = uniqueids
    for i in some_list:
        oid = six.next(unique_sequence)
    """
    seed = random.getrandbits(32)
    # if we are here
    while True:
        yield str(seed)
        seed += 1


def timestamp():
    return str(datetime.datetime.now())


def mop_lookup(obj):
    if not obj.echeck:
        return {
            'MOP': obj.card_type, 'cc_num': obj.cc_num,
            # want fields to be consistent for csv file
            'check_account_number': None, 'routing_number': None,
        }
    else:
        return {
            # want fields to be consistent for csv file
            'MOP': 'Echeck', 'cc_num': None,
            'check_account_number': obj.check_account_number,
            'routing_number': obj.routing_number,
        }


class Certification(object):
    def __init__(self, customer_sequence=None, order_sequence=None):
        """
        run all chase certification tests and print results to file
        """
        self.customer_sequence = customer_sequence if customer_sequence else uniqueids()
        self.order_sequence = order_sequence if order_sequence else uniqueids()
        self.section_b_results = list()
        self.section_g_results = list()

    def run_all(self, output_file='results.txt'):
        test_sections = [
            self.section_a,
            self.section_b,
            self.section_c,
            self.section_d,
            self.section_e_1,
            self.section_e_2,
            self.section_f,
            self.section_g,
            self.section_h,
            self.section_i,
            self.section_j,
            self.section_k,
            #self.failover()
        ]
        with open(output_file, 'a') as fout:
            for test_section in test_sections:
                fieldnames = list()
                fout.write(test_section.__doc__ + '\n')
                for line_number, result in test_section():
                    if line_number is 1:
                        fieldnames = sorted(result.keys())
                        writer = csv.DictWriter(fout, fieldnames=fieldnames)
                        writer.writeheader()
                    writer.writerow(result)

    def section_a(self):
        """SECTION A: Authorization for Account Verification Testing"""
        for line, profile in enumerate(deepcopy(td.TEST_PROFILES), 1):
            oid = six.next(self.order_sequence)
            profile['order_id'] = oid
            order = orbital_gateway.Order(**profile)
            result = order.authorize()
            result.update(mop_lookup(order))
            result.update({'amount': order.amount, 'cvv': order.cvv})
            yield line, result

    def section_b(self):
        """SECTION B: Authorization Testing"""
        for line, profile in enumerate(deepcopy(td.TEST_PROFILES), 1):
            oid = six.next(self.order_sequence)
            customer_id = six.next(self.customer_sequence)
            profile['order_id'] = oid
            profile['amount'] = "100.00"
            profile['customer_ref_num'] = customer_id
            order = orbital_gateway.Order(**profile)
            result = order.authorize()
            result.update(mop_lookup(order))
            result.update({'amount': order.amount, 'cvv': order.cvv})

            # add detail to section_b_results for later tests
            txn_ref_num = result.get('TxRefNum')
            if txn_ref_num:
                self.section_b_results.append({
                    'mop': result['MOP'],
                    'tx_ref_num': txn_ref_num,
                    'amount': profile['amount'],
                    'order_id': oid
                })
            yield line, result

    def section_c(self):
        """SECTION C: Capture Testing"""
        for line, txn in enumerate(self.section_b_results, 1):
            capture = orbital_gateway.MarkForCapture(**txn)
            result = capture.request()
            yield line, result

    def section_d(self):
        """SECTION D: Auth/Capture Testing"""
        for line, profile in enumerate(deepcopy(td.TEST_PROFILES), 1):
            oid = six.next(self.order_sequence)
            customer_id = six.next(self.customer_sequence)
            profile['order_id'] = oid
            profile['amount'] = "100.00"
            profile['customer_ref_num'] = customer_id
            order = orbital_gateway.Order(**profile)
            result = order.authorize_capture()
            result.update(mop_lookup(order))
            result.update({'amount': order.amount, 'cvv': order.cvv})
            yield line, result

    def section_e_1(self):
        """SECTION E1: Refund Testing using a TxnRefNum"""
        for line, profile in enumerate(deepcopy(td.TEST_PROFILES), 1):
            oid = six.next(self.order_sequence)
            customer_id = six.next(self.customer_sequence)
            profile['order_id'] = oid
            profile['amount'] = "10.00"
            order = orbital_gateway.Order(**profile)
            auth_response = order.authorize()
            refund_args = {
                'tx_ref_num': auth_response['TxRefNum'],
                'order_id': oid,
                'amount': profile['amount'],
                'customer_ref_num': customer_id,
            }
            refund = orbital_gateway.Order(**refund_args)
            result = refund.refund()
            result.update(mop_lookup(order))
            result.update({'amount': order.amount, 'cvv': order.cvv})
            yield line, result

    def section_e_2(self):
        """SECTION E2: Refund Testing using a Credit Card Number"""
        for line, profile in enumerate(deepcopy(td.TEST_PROFILES), 1):
            if not profile.get('card_type') == "EC":
                oid = six.next(self.order_sequence)
                customer_id = six.next(self.customer_sequence)
                profile['order_id'] = oid
                profile['amount'] = "10.00"
                profile['customer_ref_num'] = customer_id
                order = orbital_gateway.Order(**profile)
                order.authorize()
                refund = orbital_gateway.Order(**profile)
                result = refund.refund()
                result.update(mop_lookup(order))
                result.update({'amount': order.amount, 'cvv': order.cvv})
                yield line, result

    def section_f(self):
        """SECTION F: Authorization to Void/Reversal Testing"""
        for line, profile in enumerate(deepcopy(td.TEST_PROFILES), 1):
            oid = six.next(self.order_sequence)
            customer_id = six.next(self.customer_sequence)
            profile['order_id'] = oid
            profile['amount'] = "10.00"
            profile['customer_ref_num'] = customer_id
            order = orbital_gateway.Order(**profile)
            auth_response = order.authorize()
            void_args = {
                'tx_ref_num': auth_response['TxRefNum'],
                'tx_ref_idx': '0',
                'order_id': oid,
                'amount': profile['amount'],
            }
            reversal = orbital_gateway.Reversal(**void_args)
            if order.reversal:
                response = reversal.reversal()
            else:
                response = reversal.void()
            response.update(mop_lookup(order))
            response['amount'] = order.amount
            yield line, response

    def section_g(self):
        """SECTION G: Create a Customer Profile Testing"""
        for line, profile_args in enumerate(deepcopy(td.TEST_PROFILES), 1):
            profile = orbital_gateway.Profile(**profile_args)
            result = profile.create()
            self.section_g_results.append({
                'name': result['CustomerName'],
                'customer_ref_num': result['CustomerRefNum'],
                'amount': profile_args['amount'],
            })
            result.update({
                'timestamp': timestamp(), 'profile_name': profile.name,
            })
            yield line, result

    def section_h(self):
        """SECTION H: Update a Customer Profile Testing"""
        for line, profile_args in enumerate(self.section_g_results, 1):
            profile = orbital_gateway.Profile(**profile_args)
            result = profile.update()
            result.update({
                'timestamp': timestamp(), 'profile_name': profile.name,
            })
            yield line, result

    def section_i(self):
        """SECTION I: Using a Customer Profile Testing"""
        for line, profile_args in enumerate(self.section_g_results, 1):
            profile_args['amount'] = "10.00"
            profile_args['customer_num'] = profile_args.pop('customer_ref_num')
            profile_args['order_id'] = six.next(self.order_sequence)
            order = orbital_gateway.Order(**profile_args)
            result = order.authorize_capture()
            yield line, result

    def section_j(self):
        """SECTION J: Delete Customer Profile Testing"""
        for line, profile_args in enumerate(deepcopy(td.TEST_PROFILES), 1):
            profile = orbital_gateway.Profile(**profile_args)
            result = profile.create()
            customer_ref_num = result['CustomerRefNum']
            name = result['CustomerName']
            profile = orbital_gateway.Profile(customer_ref_num=customer_ref_num)
            destroy_response = profile.destroy()
            yield line, destroy_response

    def section_k(self):
        """SECTION K: Negative Testing"""
        charges = [
            "530.00",  # AMEX
            "304.00",  # DISCOVER
            "605.00",  # JCB
            "402.00",  # MasterCard
            "999.00",  # Visa
        ]
        profiles = [
            i for i in self.section_g_results
            if 'echeck' not in i['name'].lower()
        ]
        for d, c in zip(profiles, charges):
            d['amount'] = c

        for line, profile_args in enumerate(profiles, 1):
            profile_args['order_id'] = six.next(self.order_sequence)
            order = orbital_gateway.Order(**profile_args)
            response = order.authorize_capture()
            yield line, response

    def failover(self):
        """5.11 Failover Testing Test Cases"""
        for line, profile in enumerate(deepcopy(td.TEST_PROFILES), 1):
            if not profile.get('card_type') == "EC":
                oid = six.next(self.order_sequence)
                profile['order_id'] = oid
                profile['amount'] = "105.00"
                profile['url'] = 'https://bad-url'
                order = orbital_gateway.Order(**profile)
                result = order.authorize()
                result.update(mop_lookup(order))
                result.update({'amount': order.amount, 'cvv': order.cvv})
                yield line, result


if __name__ == '__main__':
    c = Certification()
    c.run_all()

