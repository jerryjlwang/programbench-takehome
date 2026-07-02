def test_version_and_help_text(run_pocket):
    """CATCHES: PocketLang version and help expose the documented CLI surface."""
    version = run_pocket(["--version"])
    assert version.returncode == 0, version.stderr
    assert version.stdout == "pocketlang 0.1.0\n"
    assert version.stderr == ""

    help_result = run_pocket(["--help"])
    assert help_result.returncode == 0, help_result.stderr
    assert help_result.stdout == (
        "Usage: pocket ... [-c cmd | file] ...\n"
        "    -c, --cmd=<str>   Evaluate and run the passed string.\n"
        "    -d, --debug       Compile and run the debug version.\n"
        "    -h, --help        Prints this help message and exit.\n"
        "    -q, --quiet       Don't print version and copyright statement on REPL startup.\n"
        "    -v, --version     Prints the pocketlang version and exit.\n"
    )
    assert help_result.stderr == ""


def test_command_string_and_script_file_execution(run_pocket, tmp_path):
    """CATCHES: -c command strings and script files both execute with exact stdout."""
    command = run_pocket(["-c", "print(1 + 2 * 3); print('pocket:' + str(42))"], cwd=tmp_path)
    assert command.returncode == 0, command.stderr
    assert command.stdout == "7\npocket:42\n"
    assert command.stderr == ""

    script = tmp_path / "fib.pk"
    script.write_text(
        "\n".join(
            [
                "def fib(n)",
                "  if n < 2 then return n end",
                "  return fib(n-1) + fib(n-2)",
                "end",
                "for i in 0..7",
                "  print(fib(i))",
                "end",
            ]
        )
        + "\n"
    )
    result = run_pocket([str(script)], cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert result.stdout == "0\n1\n1\n2\n3\n5\n8\n"
    assert result.stderr == ""
