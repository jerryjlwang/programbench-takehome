import re

import pytest


EXPECTED_SUITE_COUNTS = {
    "suite-array.janet": 49,
    "suite-asm.janet": 6,
    "suite-boot.janet": 1551,
    "suite-buffer.janet": 77,
    "suite-bundle.janet": 46,
    "suite-capi.janet": 9,
    "suite-cfuns.janet": 2,
    "suite-compile.janet": 36,
    "suite-corelib.janet": 104,
    "suite-debug.janet": 1,
    "suite-ev.janet": 735,
    "suite-ev2.janet": 6,
    "suite-ffi.janet": 11,
    "suite-filewatch.janet": 51,
    "suite-inttypes.janet": 381,
    "suite-io.janet": 11,
    "suite-marsh.janet": 73,
    "suite-math.janet": 158,
    "suite-net.janet": 2,
    "suite-os.janet": 58,
    "suite-parse.janet": 60,
    "suite-peg.janet": 366,
    "suite-pp.janet": 12,
    "suite-specials.janet": 58,
    "suite-string.janet": 69,
    "suite-strtod.janet": 3,
    "suite-struct.janet": 32,
    "suite-symcache.janet": 4,
    "suite-table.janet": 15,
    "suite-tuple.janet": 4,
    "suite-unknown.janet": 67,
    "suite-value.janet": 23,
    "suite-vm.janet": 36,
}


EXAMPLE_SCRIPTS = [
    "3sum.janet",
    "abstract-unix-socket.janet",
    "assembly.janet",
    "async-execute.janet",
    "channel.janet",
    "chatserver.janet",
    "colors.janet",
    "debug.janet",
    "debugger.janet",
    "echoclient.janet",
    "echoserve.janet",
    "error.janet",
    "evlocks.janet",
    "evsleep.janet",
    "fizzbuzz.janet",
    "hello.janet",
    "iterate-fiber.janet",
    "lazyseqs.janet",
    "life.janet",
    "lineloop.janet",
    "marshal-stress.janet",
    "maxtriangle.janet",
    "posix-exec.janet",
    "primes.janet",
    "rtest.janet",
    "select.janet",
    "select2.janet",
    "sigaction.janet",
    "tcpclient.janet",
    "tcpserver.janet",
    "threaded-channels.janet",
    "udpclient.janet",
    "udpserver.janet",
    "urlloader.janet",
    "weak-tables.janet",
]


@pytest.mark.parametrize(
    ("suite", "expected_count"),
    sorted(EXPECTED_SUITE_COUNTS.items()),
)
def test_upstream_suite_passes_with_expected_count(run_janet, janet_fixture, suite, expected_count):
    """CATCHES: upstream Janet suite files report exact passing assertion counts."""
    result = run_janet([f"test/{suite}"], cwd=janet_fixture, timeout=45)

    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
    assert result.stderr.startswith(f"Starting suite test/{suite}...\n")
    finish_re = re.compile(
        rf"Finished suite test/{re.escape(suite)} in [0-9.]+ seconds - "
        rf"{expected_count} of {expected_count} tests passed \(0 skipped\)\.\n$"
    )
    assert finish_re.search(result.stderr), result.stderr


@pytest.mark.parametrize("example", EXAMPLE_SCRIPTS)
def test_upstream_example_compiles_with_marker(run_janet, janet_fixture, example):
    """CATCHES: upstream example programs compile successfully under flycheck mode."""
    marker = f"compiled-example:{example}"
    result = run_janet(
        ["--eval", f'(print "{marker}")', "--flycheck", f"examples/{example}"],
        cwd=janet_fixture,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout == f"{marker}\n"
    assert result.stderr == ""
