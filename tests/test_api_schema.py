# -*- coding: UTF-8 -*-
"""
A suite of tests for the HTTP API schemas
"""
import unittest

from jsonschema import Draft4Validator, validate, ValidationError
from vlab_dns_api.lib.views import dns


class TestDnsViewSchema(unittest.TestCase):
    """A set of test cases for the schemas of /api/1/inf/dns"""

    def test_post_schema(self):
        """The schema defined for POST on is valid"""
        try:
            Draft4Validator.check_schema(dns.DnsView.POST_SCHEMA)
            schema_valid = True
        except RuntimeError:
            schema_valid = False

        self.assertTrue(schema_valid)


    def test_get_schema(self):
        """The schema defined for GET on is valid"""
        try:
            Draft4Validator.check_schema(dns.DnsView.GET_SCHEMA)
            schema_valid = True
        except RuntimeError:
            schema_valid = False

        self.assertTrue(schema_valid)

    def test_delete_schema(self):
        """The schema defined for DELETE on is valid"""
        try:
            Draft4Validator.check_schema(dns.DnsView.DELETE_SCHEMA)
            schema_valid = True
        except RuntimeError:
            schema_valid = False

        self.assertTrue(schema_valid)

    def test_iamges_schema(self):
        """The schema defined for GET on /images is valid"""
        try:
            Draft4Validator.check_schema(dns.DnsView.IMAGES_SCHEMA)
            schema_valid = True
        except RuntimeError:
            schema_valid = False

        self.assertTrue(schema_valid)


if __name__ == '__main__':
    unittest.main()
