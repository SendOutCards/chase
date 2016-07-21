import datetime
import random

import orbital_gateway
from tests import orbital_gateway_test_data as td


def uniqueids():
    """
    usage:
    unique_sequence = uniqueids
    for i in some_list:
        oid = unique_sequence.next()
    """
    seed = random.getrandbits(32)
    while True:
        yield str(seed)
        seed += 1


def format_order_response(response):
    auth_code = response.get('AuthCode', '')
    oid = response.get('OrderID', '')
    txrefnum = response.get('TxRefNum', '')
    return "Auth code: {} Order ID: {}, TxRefNum: {}".format(
        auth_code, oid, txrefnum
    )


def timestamp():
    return str(datetime.datetime.now())


def format_mop(obj):
    if not obj.echeck:
        return '{} {}'.format(obj.card_type, obj.cc_num)
    else:
        return 'ECHECK: {} RDFI {}'.format(
            obj.check_account_number, obj.routing_number
        )


class Certification(object):
    def __init__(self):
        """
        run all chase certification tests and print results to file
        """
        self.fout = open('results.txt', 'a')
        self.customer_sequence = uniqueids()
        self.order_sequence = uniqueids()
        self.section_b_results = list()
        self.section_g_results = list()

        # run tests
        self.section_a()
        self.section_b()
        self.section_c()
        self.section_d()
        self.section_e_1()
        self.section_e_2()
        self.section_f()
        self.section_g()
        self.section_h()
        self.section_i()
        self.section_j()
        self.section_k()

        # close file
        self.fout.close()

    def section_a(self):
        """SECTION A: Authorization for Account Verification Testing"""
        self.fout.write(
            "SECTION A: Authorization for Account Verification Testing\n"
        )
        for line, profile in enumerate(td.TEST_PROFILES, 1):
            oid = self.order_sequence.next()
            customer_id = self.customer_sequence.next()
            profile['order_id'] = oid
            profile['customer_ref_num'] = customer_id
            order = orbital_gateway.Order(**profile)
            result = order.authorize()
            formatted_response = format_order_response(result)
            mop_value = format_mop(order)
            self.fout.write(
                "{} MOP: {} Amt: {}, CVV: {} {}\n".format(
                    line, mop_value, order.amount, order.cvv, formatted_response
                )
            )

    def section_b(self):
        """SECTION B: Authorization Testing"""
        self.fout.write("SECTION B: Authorization Testing\n")
        for line, profile in enumerate(td.TEST_PROFILES, 1):
            oid = self.order_sequence.next()
            customer_id = self.customer_sequence.next()
            profile['order_id'] = oid
            profile['amount'] = "100.00"
            profile['customer_ref_num'] = customer_id
            order = orbital_gateway.Order(**profile)
            result = order.authorize()
            formatted_response = format_order_response(result)
            mop_value = format_mop(order)
            txn_ref_num = result.get('TxRefNum')
            if txn_ref_num:
                self.section_b_results.append({
                    'mop': mop_value,
                    'tx_ref_num': txn_ref_num,
                    'amount': profile['amount'],
                    'order_id': oid
                })
            self.fout.write(
                "{} MOP: {} Amt: {}, CVV: {} {}\n".format(
                    line, mop_value, order.amount, order.cvv, formatted_response
                )
            )

    def section_c(self):
        """SECTION C: Authorization Testing"""
        self.fout.write("SECTION C: Capture Testing\n")
        for line, txn in enumerate(self.section_b_results, 1):
            capture = orbital_gateway.MarkForCapture(**txn)
            result = capture.request()
            mop = txn.get('mop', '')
            amount = result.get('Amount')
            auth_code = result.get('AuthCode')
            order_id = result.get('OrderID')
            tx_ref_num = result.get('TxRefNum')
            self.fout.write(
                "{} MOP: {}, Amt: {}, AuthCode: {}, OrderID: {}, TxRefNum: {}\n".format(
                    line, mop, amount, auth_code, order_id, tx_ref_num
                )
            )

    def section_d(self):
        """SECTION D: Auth/Capture Testing"""
        self.fout.write("SECTION D: Auth/Capture Testing\n")
        for line, profile in enumerate(td.TEST_PROFILES, 1):
            oid = self.order_sequence.next()
            customer_id = self.customer_sequence.next()
            profile['order_id'] = oid
            profile['amount'] = "100.00"
            profile['customer_ref_num'] = customer_id
            order = orbital_gateway.Order(**profile)
            result = order.authorize_capture()
            formatted_response = format_order_response(result)
            mop_value = format_mop(order)
            self.fout.write(
                "{} MOP: {} Amt: {}, CVV: {} {}\n".format(
                    line, mop_value, order.amount, order.cvv, formatted_response
                )
            )

    def section_e_1(self):
        """SECTION E1: Refund Testing using a TxnRefNum"""
        self.fout.write("SECTION E1: Refund Testing using a TxnRefNum\n")
        for line, profile in enumerate(td.TEST_PROFILES, 1):
            oid = self.order_sequence.next()
            customer_id = self.customer_sequence.next()
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
            response = refund.refund()
            formatted_response = format_order_response(response)
            mop_value = format_mop(order)
            self.fout.write(
                "{} MOP: {} Amt: {}, CVV: {} {}\n".format(
                    line, mop_value, order.amount, order.cvv,
                    formatted_response
                )
            )

    def section_e_2(self):
        """SECTION E2: Refund Testing using a Credit Card Number"""
        self.fout.write("SECTION E2: Refund Testing using a Credit Card Number\n")
        for line, profile in enumerate(td.TEST_PROFILES, 1):
            oid = self.order_sequence.next()
            customer_id = self.customer_sequence.next()
            profile['order_id'] = oid
            profile['amount'] = "10.00"
            profile['customer_ref_num'] = customer_id
            order = orbital_gateway.Order(**profile)
            order.authorize()
            refund = orbital_gateway.Order(**profile)
            response = refund.refund()
            formatted_response = format_order_response(response)
            mop_value = format_mop(order)
            self.fout.write(
                "{} MOP: {} Amt: {}, CVV: {} {}\n".format(
                    line, mop_value, order.amount, order.cvv,
                    formatted_response
                )
            )

    def section_f(self):
        """SECTION F: Authorization to Void/Reversal Testing"""
        self.fout.write("SECTION F: Authorization to Void/Reversal Testing\n")
        for line, profile in enumerate(td.TEST_PROFILES, 1):
            oid = self.order_sequence.next()
            customer_id = self.customer_sequence.next()
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
            mop_value = format_mop(order)
            self.fout.write(
                "{} MOP: {} Amt: {}, OrderID: {}, TxRefNum: {}\n".format(
                    line, mop_value, order.amount,
                    oid, response['TxRefNum']
                )
            )

    def section_g(self):
        """SECTION G: Create a Customer Profile Testing"""
        self.fout.write("SECTION G: Create a Customer Profile Testing\n")
        for line, profile_args in enumerate(td.TEST_PROFILES, 1):
            profile = orbital_gateway.Profile(**profile_args)
            result = profile.create()
            self.section_g_results.append({
                'name': result['CustomerName'],
                'customer_ref_num': result['CustomerRefNum'],
                'amount': profile_args['amount'],
            })
            self.fout.write(
                "{} datetime: {} UTC, CustName: {}, Customer Ref Number {}\n".format(
                    line, timestamp(), profile.name, result.get('CustomerRefNum')
                )
            )

    def section_h(self):
        """SECTION H: Update a Customer Profile Testing"""
        self.fout.write("SECTION H: Update a Customer Profile Testing\n")

        for line, profile_args in enumerate(self.section_g_results, 1):
            profile = orbital_gateway.Profile(**profile_args)
            result = profile.update()
            self.fout.write(
                "{} datetime: {} UTC, CustName: {}, Customer Ref Number {}\n".format(
                    line, timestamp(), profile.name, result.get('CustomerRefNum')
                )
            )

    def section_i(self):
        """SECTION I: Using a Customer Profile Testing"""
        self.fout.write("SECTION I: Using a Customer Profile Testing\n")

        for line, profile_args in enumerate(self.section_g_results, 1):
            profile_args['amount'] = "10.00"
            profile_args['customer_num'] = profile_args.pop('customer_ref_num')
            profile_args['order_id'] = self.order_sequence.next()
            order = orbital_gateway.Order(**profile_args)
            response = order.authorize_capture()
            formatted_response = format_order_response(response)
            self.fout.write(
                "{} Customer {} {}\n".format(
                    line, profile_args['customer_num'], formatted_response
                )
            )

    def section_j(self):
        """SECTION J: Delete Customer Profile Testing"""
        self.fout.write("SECTION J: Delete Customer Profile Testing\n")
        for line, profile_args in enumerate(td.TEST_PROFILES, 1):
            profile = orbital_gateway.Profile(**profile_args)
            result = profile.create()
            profile = orbital_gateway.Profile(
                customer_ref_num=result['CustomerRefNum']
            )
            response = profile.destroy()
            self.fout.write(
                "{} datetime: {} UTC, CustName: {}, Customer Ref Number {}\n".format(
                    line, timestamp(), profile.name, response.get('CustomerRefNum')
                )
            )

    def section_k(self):
        """SECTION K: Negative Testing"""
        self.fout.write("SECTION K: Negative Testing\n")
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
            profile_args['order_id'] = self.order_sequence.next()
            order = orbital_gateway.Order(**profile_args)
            response = order.authorize_capture()
            formatted_response = format_order_response(response)
            self.fout.write(
                "{} Customer {}, Status Message {}, {}\n".format(
                    line, profile_args['customer_num'],
                    response['StatusMsg'], formatted_response
                )
            )

if __name__ == '__main__':
    c = Certification()

