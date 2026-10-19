import importlib.util
import io
import subprocess
import sys
import unittest
from unittest import mock
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
        lcomm_alignment = self.maspsx_cli.LcommAlignment
        expected_by_version = {
            None: self.maspsx_cli.AspsxVersionConfig(),
            "1.05": self.maspsx_cli.AspsxVersionConfig(
                nop_at_expansion=True,
                nop_mflo_mfhi=False,
                nop_lw_lw=True,
                addiu_at=True,
                lcomm_alignment=lcomm_alignment.NONE,
                comm_uses_sdata_limit=False,
                gp_allow=False,
            ),
            "2.05": self.maspsx_cli.AspsxVersionConfig(
                div_uses_tge=True,
                nop_at_expansion=True,
                nop_mflo_mfhi=False,
                nop_lw_lw=True,
                addiu_at=True,
                lcomm_alignment=lcomm_alignment.NONE,
                comm_uses_sdata_limit=False,
                gp_allow=False,
            ),
            "2.08": self.maspsx_cli.AspsxVersionConfig(
                div_uses_tge=True,
                nop_at_expansion=True,
                nop_mflo_mfhi=False,
                nop_lw_lw=True,
                addiu_at=True,
                comm_uses_sdata_limit=False,
                gp_allow=False,
            ),
            "2.21": self.maspsx_cli.AspsxVersionConfig(
                nop_at_expansion=True,
                nop_mflo_mfhi=False,
                nop_lw_lw=True,
                addiu_at=True,
            ),
            "2.30": self.maspsx_cli.AspsxVersionConfig(),
            "2.34": self.maspsx_cli.AspsxVersionConfig(),
            "2.50": self.maspsx_cli.AspsxVersionConfig(
                expand_li=False,
                li_small_uses_addiu=True,
            ),
            "2.56": self.maspsx_cli.AspsxVersionConfig(
                expand_li=False,
                li_small_uses_addiu=True,
            ),
            "2.67": self.maspsx_cli.AspsxVersionConfig(
                expand_li=False,
                li_small_uses_addiu=True,
                sltu_at=False,
                lcomm_alignment=lcomm_alignment.POWER_OF_TWO,
            ),
            "2.77": self.maspsx_cli.AspsxVersionConfig(
                expand_li=False,
                li_small_uses_addiu=True,
                sltu_at=False,
                gp_allow_offset=True,
                lcomm_alignment=lcomm_alignment.POWER_OF_TWO,
            ),
            "2.81": self.maspsx_cli.AspsxVersionConfig(
                expand_li=False,
                li_small_uses_addiu=True,
                sltu_at=False,
                gp_allow_offset=True,
                gp_allow_la=True,
                lcomm_alignment=lcomm_alignment.POWER_OF_TWO,
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

    def test_old_versions_force_G0_for_assembler(self):
        """
        If the `aspsx` version is sufficiently old, always override the user and
        force `-G0`.
        """
        argv = [
            "maspsx.py",
            "--aspsx-version=2.08",
            "--run-assembler",
            "--gnu-as-path=as",
            "--dont-force-G0",
            "--force-stdin",
            "-G8",
        ]

        # Mock the utilities that `maspsx` uses to invoke the assembler so we can
        # capture the invocation/args.
        with (
            mock.patch.object(sys, "argv", argv),
            mock.patch.object(sys, "stdin", io.StringIO("nop\n")),
            mock.patch.object(self.maspsx_cli.shutil, "which", return_value="as"),
            mock.patch.object(self.maspsx_cli.subprocess, "Popen") as popen,
        ):
            process = popen.return_value.__enter__.return_value
            process.communicate.return_value = (b"", b"")
            process.returncode = 0

            self.maspsx_cli.main()

        self.assertEqual(["as", "-G8", "-G0", "-"], popen.call_args.args[0])
