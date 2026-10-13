import json
from pathlib import Path
import shutil
import tempfile
import unittest
from aria.abilities import plan_abilities
from aria.compiler import ensure_callback
from aria.core import PatchError

ROOT = Path(__file__).resolve().parents[1]


class GateCompositionTests(unittest.TestCase):
    def test_existing_config_and_ram_abi_preserved(self):
        profile = json.loads((ROOT/'framework/aos-usa-r0.json').read_text())
        combined = json.loads((ROOT/'examples/soul-gate-abilities/mod.json').read_text())['abilities']
        standard = json.loads((ROOT/'examples/ability-workshop/mod.json').read_text())['abilities']
        a, report = plan_abilities(combined, profile)
        b, original = plan_abilities(standard, profile)
        self.assertEqual(a, b)
        self.assertEqual(report['ram_claims'], original['ram_claims'])
        self.assertEqual(report['abi'], 1)

    def test_gate_header_is_a_required_fingerprint_dependency(self):
        source = ROOT/'examples/soul-gate-abilities/runtime'
        spec = json.loads((source/'build.json').read_text())
        ensure_callback(source, spec)
        directory = ROOT/'local/framework-tests'; directory.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=directory) as temp:
            folder = Path(temp)/'runtime'; shutil.copytree(source, folder)
            (folder/'gate.h').write_text('changed gate contract')
            with self.assertRaises(PatchError):
                ensure_callback(folder, spec)
