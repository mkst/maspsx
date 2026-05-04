import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path


class TestCli(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.repo_root = Path(__file__).resolve().parents[1]
        spec = importlib.util.spec_from_file_location(
            "maspsx_cli",
            cls.repo_root / "maspsx.py",
        )
        assert spec is not None
        assert spec.loader is not None
        cls.maspsx_cli = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.maspsx_cli)

    def test_config_for_aspsx_version(self):
        expected_by_version = {
            None: self.maspsx_cli.AspsxVersionConfig(),
            "1.05": self.maspsx_cli.AspsxVersionConfig(
                nop_at_expansion=True,
                nop_mflo_mfhi=False,
                addiu_at=True,
            ),
            "2.05": self.maspsx_cli.AspsxVersionConfig(
                div_uses_tge=True,
                nop_at_expansion=True,
                nop_mflo_mfhi=False,
                addiu_at=True,
            ),
            "2.21": self.maspsx_cli.AspsxVersionConfig(
                nop_at_expansion=True,
                nop_mflo_mfhi=False,
                addiu_at=True,
            ),
            "2.30": self.maspsx_cli.AspsxVersionConfig(),
            "2.56": self.maspsx_cli.AspsxVersionConfig(
                expand_li=False,
            ),
            "2.67": self.maspsx_cli.AspsxVersionConfig(
                expand_li=False,
                sltu_at=False,
            ),
            "2.77": self.maspsx_cli.AspsxVersionConfig(
                expand_li=False,
                sltu_at=False,
                gp_allow_offset=True,
            ),
            "2.81": self.maspsx_cli.AspsxVersionConfig(
                expand_li=False,
                sltu_at=False,
                gp_allow_offset=True,
                gp_allow_la=True,
            ),
        }

        for version, expected in expected_by_version.items():
            with self.subTest(version=version):
                self.assertEqual(
                    expected,
                    self.maspsx_cli.config_for_aspsx_version(version),
                )

    def test_run_assembler_returns_assembler_exit_code(self):
        process = subprocess.run(
            [
                sys.executable,
                str(self.repo_root / "maspsx.py"),
                "--run-assembler",
                "--gnu-as-path",
                "false",
                "--force-stdin",
            ],
            input="nop\n",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        self.assertEqual(1, process.returncode)
