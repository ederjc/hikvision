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

    def test_get_ptz_move_status(self):
        """Read moving and idle states from the PTZ status response."""
        device = hikvision.api.CreateDevice.__new__(hikvision.api.CreateDevice)
        device._base = "http://camera"
        device._username = "user"
        device._password = "password"
        response = Mock()
        response.raise_for_status.return_value = None

        with patch.object(hikvision.api.requests, "get", return_value=response) as get:
            response.text = (
                '<PTZStatus xmlns="http://www.hikvision.com/ver20/XMLSchema">'
                '<MoveStatus><panTilt>MOVING</panTilt><zoom>IDLE</zoom></MoveStatus>'
                '</PTZStatus>'
            )
            self.assertTrue(device.getPTZMoveStatus())

            response.text = (
                '<PTZStatus xmlns="http://www.hikvision.com/ver20/XMLSchema">'
                '<MoveStatus><panTilt>IDLE</panTilt><zoom>IDLE</zoom></MoveStatus>'
                '</PTZStatus>'
            )
            self.assertFalse(device.getPTZMoveStatus())

        self.assertEqual(get.call_count, 2)

    def test_get_ptz_move_status_rejects_missing_state(self):
        """Do not treat an unrecognized status response as stopped."""
        device = hikvision.api.CreateDevice.__new__(hikvision.api.CreateDevice)
        device._base = "http://camera"
        device._username = "user"
        device._password = "password"
        response = Mock()
        response.text = "<PTZStatus />"
        response.raise_for_status.return_value = None

        with patch.object(hikvision.api.requests, "get", return_value=response):
            with self.assertRaises(ValueError):
                device.getPTZMoveStatus()

