# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0

import datetime
from collections import OrderedDict
from functools import partial
from os import path
from typing import OrderedDict as OrderedDictType
from unittest import TestCase

from freezegun import freeze_time
from xmltodict import parse

import sys

sys.path.insert(0, "app")
from app.sd_mox import SDMox

xmlparse = partial(parse, dict_constructor=dict)


def read_file(path):
    """Read the file at path, and return its contents."""
    with open(path, "r") as resource_file:
        return resource_file.read()


script_dir = path.dirname(path.realpath(__file__))
res_prefix = script_dir + "/res/sd_mox_"
xml_create = read_file(res_prefix + "create.xml")
xml_edit_simple = read_file(res_prefix + "edit_simple.xml")
xml_edit_address = read_file(res_prefix + "edit_address.xml")
xml_edit_integration_values = read_file(res_prefix + "edit_integration_values.xml")
xml_move = read_file(res_prefix + "move.xml")


unit_parent = {
    "name": "A-sdm1",
    "uuid": "12345-11-11-11-12345",
    "org_unit_type": {"uuid": "uuid-a"},
    "org_unit_level": {"uuid": "uuid-b"},
    "user_key": "user-key-11111",
}

mox_overrides = {
    "triggered_uuids": [],
    "ou_levelkeys": [],
    "amqp_tls": {
        "host": "example.org",
        "port": 5672,
        "server": "some.server",
        "virtual_host": "/some/vhost",
        "username": "guest",
        "password": "guest",
        "ca": b"ca",
        "cert": b"cert",
        "key": b"key",
        "exchange": "some-exchange",
    },
    "sd_username": "",
    "sd_password": "",
    "sd_institution": "",
}


class TestableSDMox(SDMox):
    def _read_ou_levelkeys(self) -> OrderedDictType[str, str]:
        return OrderedDict()


@freeze_time("2020-01-01 12:00:00")
class Tests(TestCase):
    def setUp(self):
        from_date = datetime.datetime(2019, 7, 1, 0, 0)
        self.mox = TestableSDMox(from_date, overrides=mox_overrides)

        from collections import OrderedDict

        self.mox.sd_levels = OrderedDict([("Afdelings-niveau", "uuid-b")])
        self.mox.level_by_uuid = {
            "uuid-b": "Afdelings-niveau",
        }

    def test_grouped_adresses(self):
        addresses = [
            {
                "address_type": {"scope": "DAR", "user_key": "dar-key-1"},
                "value": "0a3f507b-6331-32b8-e044-0003ba298018",
            },
            {
                "address_type": {"scope": "DAR", "user_key": "dar-key-2"},
                "value": "0a3f507b-7750-32b8-e044-0003ba298018",
            },
            {
                "address_type": {"scope": "PHONE", "user_key": "phn-key-1"},
                "value": "12345678",
            },
            {
                "address_type": {"scope": "PNUMBER", "user_key": "pnum-key-1"},
                "value": "0123456789",
            },
        ]
        scoped, keyed = self.mox._grouped_addresses(addresses)

        self.assertEqual(
            {
                "DAR": [
                    "Banegårdspladsen 1, 2750 Ballerup",
                    "Toftebjerghaven 4, 2750 Ballerup",
                ],
                "PHONE": ["12345678"],
                "PNUMBER": ["0123456789"],
            },
            scoped,
        )

        self.assertEqual(
            {
                "dar-key-1": ["0a3f507b-6331-32b8-e044-0003ba298018"],
                "dar-key-2": ["0a3f507b-7750-32b8-e044-0003ba298018"],
                "phn-key-1": ["12345678"],
                "pnum-key-1": ["0123456789"],
            },
            keyed,
        )

    def test_payload_create(self):
        pc = self.mox._payload_create(
            unit_uuid="12345-22-22-22-12345",
            unit={
                "name": "A-sdm2",
                # "uuid": "12345-22-22-22-12345",
                "org_unit_type": {"uuid": "uuid-a"},
                "org_unit_level": {"uuid": "uuid-b"},
                "user_key": "user-key-22222",
            },
            parent=unit_parent,
        )

        self.assertEqual(
            {
                "unit_name": "A-sdm2",
                "parent": {
                    "level": "Afdelings-niveau",
                    "unit_code": "user-key-11111",
                    "uuid": "12345-11-11-11-12345",
                },
                "unit_code": "user-key-22222",
                "unit_level": "Afdelings-niveau",
                "unit_uuid": "12345-22-22-22-12345",
            },
            pc,
        )

        expected = xmlparse(xml_create)
        actual = self.mox._create_xml_import(
            unit_name=pc["unit_name"],
            unit_uuid=pc["unit_uuid"],
            unit_code=pc["unit_code"],
            unit_level=pc["unit_level"],
            parent=pc["parent"]["uuid"],
        )
        self.assertEqual(expected, xmlparse(actual))

    def test_payload_edit_simple(self):
        pe = self.mox._payload_edit(
            unit_uuid="12345-22-22-22-12345",
            unit={
                "name": "A-sdm2",
                "org_unit_type": {"uuid": "uuid-a"},
                "user_key": "user-key-22222",
            },
            addresses=[],
        )

        self.assertEqual(
            {
                "unit_name": "A-sdm2",
                "unit_code": "user-key-22222",
                "phone": None,
                "adresse": None,
                "pnummer": None,
                "integration_values": {
                    "formaalskode": None,
                    "skolekode": None,
                },
                "unit_uuid": "12345-22-22-22-12345",
            },
            pe,
        )

        expected = xmlparse(xml_edit_simple)
        actual = self.mox._create_xml_ret(**pe)
        self.assertEqual(expected, xmlparse(actual))

    def test_payload_edit_address(self):
        pe = self.mox._payload_edit(
            unit_uuid="12345-22-22-22-12345",
            unit={
                "name": "A-sdm2",
                "org_unit_type": {"uuid": "uuid-a"},
                "user_key": "user-key-22222",
            },
            addresses=[
                {
                    "address_type": {
                        "scope": "DAR",
                        "user_key": "dar-userkey-not-used",
                    },
                    "value": "0a3f507b-7750-32b8-e044-0003ba298018",
                },
                {
                    "address_type": {
                        "scope": "PHONE",
                        "user_key": "phone-user-key-not-used",
                    },
                    "value": "12345678",
                },
                {
                    "address_type": {
                        "scope": "PNUMBER",
                        "user_key": "pnummer-user-key-not-used",
                    },
                    "value": "0123456789",
                },
            ],
        )

        self.assertEqual(
            {
                "unit_name": "A-sdm2",
                "unit_code": "user-key-22222",
                "phone": "12345678",
                "adresse": {
                    "silkdata:AdresseNavn": "Toftebjerghaven 4",
                    "silkdata:ByNavn": "Ballerup",
                    "silkdata:PostKodeIdentifikator": "2750",
                },
                "pnummer": "0123456789",
                "integration_values": {
                    "formaalskode": None,
                    "skolekode": None,
                },
                "unit_uuid": "12345-22-22-22-12345",
            },
            pe,
        )

        expected = xmlparse(xml_edit_address)
        actual = self.mox._create_xml_ret(**pe)
        self.assertEqual(expected, xmlparse(actual))

    def test_payload_edit_integration_values(self):
        pe = self.mox._payload_edit(
            unit_uuid="12345-33-33-33-12345",
            unit={
                "name": "A-sdm3",
                "org_unit_type": {"uuid": "uuid-a"},
                "user_key": "user-key-33333",
            },
            addresses=[
                {
                    "address_type": {"scope": "TEXT", "user_key": "Formålskode"},
                    "name": "fkode-name-not-used",
                    "value": "Formål1",
                },
                {
                    "address_type": {"scope": "TEXT", "user_key": "Skolekode"},
                    "value": "Skole1",
                },
            ],
        )

        self.assertEqual(
            {
                "unit_name": "A-sdm3",
                "unit_code": "user-key-33333",
                "phone": None,
                "adresse": None,
                "pnummer": None,
                "integration_values": {
                    "formaalskode": "Formål1",
                    "skolekode": "Skole1",
                },
                "unit_uuid": "12345-33-33-33-12345",
            },
            pe,
        )

        expected = xmlparse(xml_edit_integration_values)
        actual = self.mox._create_xml_ret(**pe)
        self.assertEqual(expected, xmlparse(actual))

    def test_payload_move_orgunit(self):
        pc = self.mox._payload_create(
            unit_uuid="12345-22-22-22-12345",
            unit={
                "name": "A-sdm2",
                # "uuid": "12345-22-22-22-12345",
                "org_unit_type": {"uuid": "uuid-a"},
                "org_unit_level": {"uuid": "uuid-b"},
                "user_key": "user-key-22222",
            },
            parent=unit_parent,
        )

        self.assertEqual(
            {
                "unit_name": "A-sdm2",
                "parent": {
                    "level": "Afdelings-niveau",
                    "unit_code": "user-key-11111",
                    "uuid": "12345-11-11-11-12345",
                },
                "unit_code": "user-key-22222",
                "unit_level": "Afdelings-niveau",
                "unit_uuid": "12345-22-22-22-12345",
            },
            pc,
        )

        expected = xmlparse(xml_move)
        actual = self.mox._create_xml_flyt(
            unit_name=pc["unit_name"],
            unit_uuid=pc["unit_uuid"],
            unit_code=pc["unit_code"],
            unit_level=pc["unit_level"],
            parent_unit_uuid=pc["parent"]["uuid"],
        )
        self.assertEqual(expected, xmlparse(actual))
