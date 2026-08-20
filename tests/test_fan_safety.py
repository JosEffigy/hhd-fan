import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from adjustor.core.fan.core import update_fan_speed, validate_fan_curve


class FanCurveSafetyTests(unittest.TestCase):
    def test_accepts_sane_curve(self):
        validate_fan_curve({40: 0.2, 60: 0.5, 90: 1.0})

    def test_rejects_out_of_bounds_duty(self):
        with self.assertRaises(ValueError):
            validate_fan_curve({40: 0.2, 90: 1.1})

    def test_rejects_decreasing_duty(self):
        with self.assertRaises(ValueError):
            validate_fan_curve({40: 0.5, 90: 0.4})

    def test_rejects_weak_emergency_endpoint(self):
        with self.assertRaises(ValueError):
            validate_fan_curve({40: 0.2, 90: 0.7})

    @patch("adjustor.core.fan.core.read_temp", return_value=130.0)
    def test_rejects_implausible_temperature(self, _read_temp):
        info = {"edge": "/fake/temp", "tctl": None, "fans": []}
        with self.assertRaises(RuntimeError):
            update_fan_speed(None, info, {40: 0.2, 90: 1.0}, False, True)


if __name__ == "__main__":
    unittest.main()
