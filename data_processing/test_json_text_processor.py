import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from json_text_processor import JSONTextProcessor

TEXT = ("1 SENATOR LANZA: Thank you, Mr. President. I rise to speak on the bill.\n"
        "2 SENATOR SMITH: I disagree with the Senator.\n"
        "3 SENATOR LANZA: One more point on funding.\n"
        "4 PRESIDENT JONES: The Senator may proceed.")


class SpeakerExtractionTest(unittest.TestCase):
    def run_pipeline(self, text):
        with tempfile.TemporaryDirectory() as d:
            year = Path(d) / "2010"
            year.mkdir()
            (year / "a.json").write_text(json.dumps({"result": {"dateTime": "2010-01-05", "text": text}}))
            JSONTextProcessor(d).process_all("SENATOR LANZA")
            return (year / "all_senator_lanza_statements.txt").read_text()

    def test_statements_stop_at_next_speaker(self):
        out = self.run_pipeline(TEXT)
        self.assertIn("SENATOR LANZA: Thank you, Mr. President. I rise to speak on the bill.", out)
        self.assertIn("SENATOR LANZA: One more point on funding.", out)
        self.assertNotIn("SMITH", out)
        self.assertNotIn("PRESIDENT", out)
        self.assertNotIn("SENATOR\n", out)

    def test_inline_speaker_change_still_stops(self):
        out = self.run_pipeline("SENATOR LANZA: First point. SENATOR SMITH: Reply.")
        self.assertEqual(out.strip(), "SENATOR LANZA: First point.")


if __name__ == "__main__":
    unittest.main()
