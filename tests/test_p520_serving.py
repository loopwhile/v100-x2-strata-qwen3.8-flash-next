"""CPU checks for the production helper's preservation boundaries."""
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("serving", Path(__file__).resolve().parents[1] / "scripts/127-p520-serving.py")
serving = importlib.util.module_from_spec(spec)
spec.loader.exec_module(serving)


class PreservationTests(unittest.TestCase):
    def test_foreign_stable_name_is_never_managed(self):
        with patch.object(serving, "run", return_value=json.dumps([{"Config": {"Labels": {}}}])) as call:
            with self.assertRaisesRegex(AssertionError, "foreign"):
                serving.identity("a")
            self.assertEqual(call.call_args.args[:2], ("docker", "inspect"))
            self.assertEqual(call.call_count, 1)

    def test_live_foreign_container_blocks_preflight_without_stopping(self):
        with patch.object(serving, "run", return_value="strata-s4b-iq2xs-agent-a") as call:
            with self.assertRaisesRegex(AssertionError, "Other containers"):
                serving.preflight(allow_owned=True)
            self.assertEqual(call.call_count, 1)

    def test_existing_stable_names_block_install_without_replacement(self):
        with patch.object(serving, "preflight"), patch.object(serving, "run", return_value="p520-llm-a") as call:
            with self.assertRaisesRegex(AssertionError, "already exist"):
                serving.install(serving.SERVING_ROOT / "releases/test")
            self.assertEqual(call.call_count, 1)
            self.assertEqual(call.call_args.args[:3], ("docker", "ps", "-a"))

    def test_release_outside_owned_directory_is_rejected(self):
        with patch.object(serving, "run") as call:
            with self.assertRaisesRegex(AssertionError, "releases directory"):
                serving.install(Path("/tmp/foreign-release"))
            call.assert_not_called()


if __name__ == "__main__":
    unittest.main()
