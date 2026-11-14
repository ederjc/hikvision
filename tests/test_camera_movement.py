import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock

from hikvision_ptz_camera import camera


class TestCameraMovement(unittest.TestCase):
    def setUp(self):
        self.camera = camera.__new__(camera)
        self.camera._device = Mock()
        self.camera._ptz_command_at = None
        self.camera._last_movement_status_error = None
        self.camera._device.getPTZMoveStatus.return_value = False

    def test_command_assumes_movement_for_at_least_two_seconds(self):
        self.camera._ptz_command_at = datetime.now() - timedelta(seconds=1)

        self.assertTrue(self.camera.is_moving())

    def test_false_poll_after_minimum_clears_assumption(self):
        self.camera._ptz_command_at = datetime.now() - timedelta(seconds=3)

        self.assertFalse(self.camera.is_moving())
        self.assertIsNone(self.camera._ptz_command_at)

    def test_true_poll_keeps_assumption_until_ten_second_timeout(self):
        self.camera._device.getPTZMoveStatus.return_value = True
        self.camera._ptz_command_at = datetime.now() - timedelta(seconds=5)
        self.assertTrue(self.camera.is_moving())

        self.camera._ptz_command_at = datetime.now() - timedelta(seconds=11)
        self.assertFalse(self.camera.is_moving())
        self.assertIsNone(self.camera._ptz_command_at)

    def test_sending_a_preset_starts_movement_assumption(self):
        self.camera._currentPreset = -1

        self.camera.gotoPreset(42)

        self.camera._device.runPreset.assert_called_once_with(42)
        self.assertIsNotNone(self.camera._ptz_command_at)
