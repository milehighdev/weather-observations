import unittest
from main import find_distance_pythagorean, process_daily_temps

#Since we were making many API calls, I didn't do mocking to keep it simple
class TestWeatherFunctions(unittest.TestCase):

    def test_pythagorean_distance_should_be_zero(self):
        distance = find_distance_pythagorean(34.103, -118.410, 34.103, -118.410)
        self.assertEqual(distance, 0)

    def test_pythagorean_distance_should_be_correct(self):
        distance = find_distance_pythagorean(34.100, -114.45, 34.102, -118.14)
        self.assertEqual(round(distance, 2), 3.69)

    def test_calculate_daily_temps(self):
        observations = [
            {
                "properties": {
                    "timestamp": "2023-05-01T14:00:00Z",
                    "temperature": {"value": 20}
                }
            },
            {
                "properties": {
                    "timestamp": "2023-05-01T14:00:00Z",
                    "temperature": {"value": 22}
                }
            },
            {
                "properties": {
                    "timestamp": "2023-05-02T14:00:00Z",
                    "temperature": {"value": 25}
                }
            }
        ]
        data = process_daily_temps(observations)
        expected = [
            {"day": "2023-05-01", "high": 22, "low": 20},
            {"day": "2023-05-02", "high": 25, "low": 25}
        ]
        self.assertEqual(data, expected)

if __name__ == '__main__':
    unittest.main()