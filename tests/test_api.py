"""
tests.test_api
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Tests the api

Copyright (c) 2015 Finbarr Brady <https://github.com/fbradyirl>
Licensed under the MIT license.
"""
# pylint: disable=protected-access
import unittest
from unittest.mock import Mock, patch
import hikvision.api
from hikvision.error import HikvisionError, MissingParamError
from requests.exceptions import ConnectionError

class TestAPI(unittest.TestCase):
    """ Tests hikvision.api module. """

    def test_create(self):
        """ Test creating a new device. """
        # Bogus config
        self.assertRaises(MissingParamError, lambda: hikvision.api.CreateDevice())
        self.assertRaises(HikvisionError, lambda: hikvision.api.CreateDevice('10.10.10.4'))

    def test_get_ptz_position(self):
        """Read the three absolute PTZ coordinates from the camera response."""
        device = hikvision.api.CreateDevice.__new__(hikvision.api.CreateDevice)
        device._base = "http://camera"
        device._username = "user"
        device._password = "password"
        response = Mock()
        response.raise_for_status.return_value = None

        with patch.object(hikvision.api.requests, "get", return_value=response) as get:
            response.text = (
                '<PTZStatus xmlns="http://www.hikvision.com/ver20/XMLSchema">'
                '<AbsoluteHigh><azimuth>1675</azimuth><elevation>142</elevation>'
                '<absoluteZoom>16</absoluteZoom></AbsoluteHigh>'
                '</PTZStatus>'
            )
            self.assertEqual(device.getPTZPosition(), (1675, 142, 16))

        self.assertEqual(get.call_args.args[0], "http://camera/ISAPI/PTZCtrl/channels/1/status")
        self.assertIsInstance(get.call_args.kwargs["auth"], hikvision.api.HTTPDigestAuth)
        self.assertEqual(get.call_args.kwargs["timeout"], 3)

    def test_get_ptz_position_rejects_incomplete_response(self):
        """Do not use missing or invalid coordinates as a position."""
        device = hikvision.api.CreateDevice.__new__(hikvision.api.CreateDevice)
        device._base = "http://camera"
        device._username = "user"
        device._password = "password"
        response = Mock()
        response.raise_for_status.return_value = None

        with patch.object(hikvision.api.requests, "get", return_value=response):
            for xml in (
                "<PTZStatus />",
                "<PTZStatus><AbsoluteHigh><azimuth>1</azimuth>"
                "<elevation>2</elevation></AbsoluteHigh></PTZStatus>",
                "<PTZStatus><AbsoluteHigh><azimuth>invalid</azimuth>"
                "<elevation>2</elevation><absoluteZoom>3</absoluteZoom>"
                "</AbsoluteHigh></PTZStatus>",
            ):
                with self.subTest(xml=xml):
                    response.text = xml
                    with self.assertRaises(ValueError):
                        device.getPTZPosition()

