"""CPU checks for the production helper's preservation boundaries."""
import importlib.util
import json
from pathlib import Path
import tempfile
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

    def test_s12_c1t_promoted_contract(self):
        self.assertEqual(serving.RECIPE, "S12-C1T")
        self.assertEqual(serving.DRAFT_DIR, Path("/srv/models/strata-data/dflash2"))
        self.assertNotIn("results/stage10-preparation", str(serving.DRAFT_DIR))
        self.assertEqual(serving.ENV["STRATA_OOMD_ROOM"], "0")
        self.assertEqual(serving.ENV["STRATA_MMAP_ADAPT_ASYNC"], "1")
        self.assertEqual(serving.ENV["STRATA_COLD_OVERLAP"], "5")
        self.assertEqual(serving.ENV["STRATA_AVX512BW_IQ"], "22")
        self.assertEqual(serving.ENV["STRATA_HC_V100"], "1")
        self.assertEqual(serving.ENV["STRATA_ROUTE_TAIL_SKIP"], "7")
        for forbidden in ("STRATA_AUX_CPUS", "STRATA_ADAPT_LAG", "STRATA_PF_WMMA2"):
            self.assertNotIn(forbidden, serving.ENV)

    def test_non_canonical_draft_dir_in_manifest_blocks_install(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = root / "releases/s12-c1t-test"
            rel.mkdir(parents=True)
            (rel / "release.json").write_text(json.dumps({
                "image": serving.IMAGE,
                "draft_dir": "/home/loopwhile/v100-x2-strata-qwen3.8-flash-next/results/stage10-preparation/draft-data/dflash2",
                "configs": {},
            }))
            (rel / "commands.json").write_text(json.dumps({}))
            with patch.object(serving, "SERVING_ROOT", root), \
                 patch.object(serving, "preflight"), \
                 patch.object(serving, "run", return_value=""):
                with self.assertRaisesRegex(AssertionError, "Unexpected draft_dir"):
                    serving.install(rel)

    def test_check_rejects_legacy_dflash2_mount(self):
        legacy_item = {
            "State": {"Running": True},
            "Mounts": [{
                "Destination": "/stage10-data/dflash2",
                "Source": "/home/loopwhile/v100-x2-strata-qwen3.8-flash-next/results/stage10-preparation/draft-data/dflash2",
                "RW": False,
            }],
        }
        with patch.object(serving, "identity", return_value=legacy_item):
            with self.assertRaisesRegex(AssertionError, "Unexpected DFlash2 mount"):
                serving.check()


if __name__ == "__main__":
    unittest.main()
