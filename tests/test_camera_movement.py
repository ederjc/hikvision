import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock

import requests

from hikvision_ptz_camera import camera


class TestCameraMovement(unittest.TestCase):
    def setUp(self):
        self.camera = camera.__new__(camera)
        self.camera._device = Mock()
        self.camera._event_store = None
        self.camera._previous_ptz_position = None
        self.camera._ptz_command_at = None
        self.camera._last_movement_status_error = None
        self.camera._device.getPTZPosition.return_value = (1000, 200, 100)

    def test_first_sample_is_unknown(self):
        self.assertIsNone(self.camera.is_moving())
        self.assertFalse(self.camera.is_moving())

    def test_one_percent_is_inclusive_for_every_axis(self):
        self.camera._previous_ptz_position = (1000, 200, 100)
        self.camera._device.getPTZPosition.return_value = (1010, 198, 101)
        self.assertFalse(self.camera.is_moving())

        for position in ((1011, 200, 100), (1000, 203, 100), (1000, 200, 102)):
            with self.subTest(position=position):
                self.camera._previous_ptz_position = (1000, 200, 100)
                self.camera._device.getPTZPosition.return_value = position
                self.assertTrue(self.camera.is_moving())

    def test_zero_previous_value_requires_exact_match(self):
        self.camera._previous_ptz_position = (0, 0, 0)
        self.camera._device.getPTZPosition.return_value = (0, 0, 0)
        self.assertFalse(self.camera.is_moving())
        self.camera._device.getPTZPosition.return_value = (1, 0, 0)
        self.assertTrue(self.camera.is_moving())

    def test_command_assumes_movement_for_at_least_two_seconds(self):
        self.camera._previous_ptz_position = (1000, 200, 100)
        self.camera._ptz_command_at = datetime.now() - timedelta(seconds=1)
        self.assertTrue(self.camera.is_moving())

        self.camera._ptz_command_at = datetime.now() - timedelta(seconds=3)
        self.assertFalse(self.camera.is_moving())
        self.assertIsNone(self.camera._ptz_command_at)

    def test_movement_continues_after_ten_seconds(self):
        self.camera._previous_ptz_position = (1000, 200, 100)
        self.camera._device.getPTZPosition.return_value = (1020, 200, 100)
        self.camera._ptz_command_at = datetime.now() - timedelta(seconds=11)
        self.assertTrue(self.camera.is_moving())

    def test_failed_poll_resets_baseline(self):
        self.camera._previous_ptz_position = (1000, 200, 100)
        self.camera._device.getPTZPosition.side_effect = [
            requests.Timeout("camera timeout"), (1100, 200, 100), (1100, 200, 100)
        ]
        with self.assertRaises(requests.Timeout):
            self.camera.is_moving()
        self.assertIsNone(self.camera.is_moving())
        self.assertFalse(self.camera.is_moving())

    def test_sending_a_preset_starts_movement_assumption(self):
        self.camera._currentPreset = -1
        self.camera.gotoPreset(42)
        self.camera._device.runPreset.assert_called_once_with(42)
        self.assertIsNotNone(self.camera._ptz_command_at)
