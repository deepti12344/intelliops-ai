import os
import tempfile
import unittest
from pathlib import Path

import app

class IncidentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_db = app.DB
        app.DB = Path(self.temp.name) / "test.sqlite3"
    def tearDown(self):
        app.DB = self.old_db
        self.temp.cleanup()
    def test_create_and_list(self):
        row = app.create_incident({"title":"API timeout","description":"500 error on payments","service":"payments"})
        self.assertEqual(row["severity"], "high")
        self.assertEqual(len(app.list_incidents()), 1)
        self.assertEqual(len(app.list_incidents("high")), 1)
    def test_critical_wins(self):
        self.assertEqual(app.analyze("Production down", "slow requests")[0], "critical")
    def test_defaults_low(self):
        self.assertEqual(app.analyze("Button color", "Change blue to teal")[0], "low")
    def test_validation(self):
        for value in ({}, {"title":"x","description":"x","service":""}, {"title":3,"description":"x","service":"x"}):
            with self.assertRaises(ValueError):
                app.create_incident(value)
    def test_sql_injection_as_data(self):
        name = "test'); DROP TABLE incidents;--"
        app.create_incident({"title":name,"description":"Description","service":"test"})
        self.assertEqual(app.list_incidents()[0]["title"],name)
        self.assertEqual(len(app.list_incidents()),1)

if __name__ == "__main__":
    unittest.main()
