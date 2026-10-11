"""Data-driven unittest entry point for the ASPSX fixture matrix."""

import re
import unittest

import util
from case_model import discover_cases


class TestAssemblerMatrix(unittest.TestCase):
    """Generated below: one independently reportable test per fixture case."""


def _test_for(case):
    def test(self):
        result = util.run_aspsx_result(
            case.source,
            {"aspsx_version": case.aspsx_version},
            data_limit=case.data_limit,
            extra_flags=case.extra_flags,
        )
        if not result.ok:
            raise util.AssemblerError(result)
        mismatch = util.output_diff(case.text, case.sections, result)
        if mismatch:
            self.fail(mismatch)

    return test


for _case in discover_cases():
    _method_name = "test_" + re.sub(r"[^a-zA-Z0-9_]", "_", _case.name)
    setattr(TestAssemblerMatrix, _method_name, _test_for(_case))
