#!/usr/bin/env python3
"""Run the ASPSX fixture matrix concurrently.

This runs the same central manifest used by the unittest matrix.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import argparse
import os
import sys
import time

from case_model import AssemblerCase, discover_cases
import util


@dataclass
class CaseResult:
    case: AssemblerCase
    result: util.RunResult
    mismatch: bool = False

    @property
    def passed(self) -> bool:
        return self.result.ok and not self.mismatch


def run_case(case: AssemblerCase, timeout: float) -> CaseResult:
    result = util.run_aspsx_result(case.source, {"aspsx_version": case.aspsx_version},
                                   case.data_limit, case.extra_flags, timeout)
    expected = case.expected
    return CaseResult(case, result, result.ok and result.instructions != expected)


def render_failure(item: CaseResult) -> str:
    if not item.result.ok:
        return item.result.diagnostic()
    return (f"{item.case.name}: assembly mismatch\n\n" +
            util.assembly_diff(item.case.expected,
                               item.result.instructions or []))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jobs", type=int,
                        default=min(4, os.cpu_count() or 1),
                        help="maximum concurrent assembler processes (default: 4)")
    parser.add_argument("--case", metavar="TEXT",
                        help="run cases whose name contains TEXT, e.g. gp:2.67")
    parser.add_argument("--timeout", type=float, default=util.DEFAULT_TIMEOUT,
                        help="per-process timeout in seconds (default: 30)")
    parser.add_argument("--verbose", action="store_true",
                        help="print passing cases as they complete")
    args = parser.parse_args(argv)
    if args.jobs < 1:
        parser.error("--jobs must be at least 1")

    cases = [case for case in discover_cases()
             if not args.case or args.case in case.name]
    if not cases:
        print("No matching cases.", file=sys.stderr)
        return 2

    started = time.monotonic()
    results: list[CaseResult | None] = [None] * len(cases)
    with ThreadPoolExecutor(max_workers=args.jobs,
                            thread_name_prefix="aspsx") as pool:
        pending = {pool.submit(run_case, case, args.timeout): index
                   for index, case in enumerate(cases)}
        for future in as_completed(pending):
            index = pending[future]
            try:
                item = future.result()
            except Exception as exc:  # runner bugs must not kill other cases
                case = cases[index]
                result = util.RunResult(case.source, case.aspsx_version,
                                        "harness", [], error=f"internal harness error: {exc}")
                item = CaseResult(case, result)
            results[index] = item
            if args.verbose:
                status = "PASS" if item.passed else "FAIL"
                print(f"{status} {item.case.name}", flush=True)

    completed = [item for item in results if item is not None]
    failures = [item for item in completed if not item.passed]
    for item in failures:
        print("\n" + render_failure(item))
    elapsed = time.monotonic() - started
    print(f"\n{len(completed)} cases: {len(completed) - len(failures)} passed, "
          f"{len(failures)} failed in {elapsed:.2f}s ({args.jobs} workers)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
