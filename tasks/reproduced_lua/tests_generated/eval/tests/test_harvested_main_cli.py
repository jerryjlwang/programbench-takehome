import pytest


def test_version_and_unrecognized_help_option(run_lua):
    """CATCHES: version output and invalid help option diagnostics stay stable."""
    version = run_lua(["-v"])
    assert version.returncode == 0
    assert version.stdout.startswith("Lua 5.5.1  Copyright")

    bad = run_lua(["-h"])
    assert bad.returncode != 0
    assert "unrecognized option '-h'" in bad.stderr
    assert "Available options are:" in bad.stderr
    assert "execute string 'stat'" in bad.stderr


def test_stdin_dash_keeps_later_dash_argument(run_lua):
    """CATCHES: dash stdin mode preserves later dash-prefixed script arguments."""
    result = run_lua(["-", "-h"], input_text="print(arg[1])\n")
    assert result.returncode == 0, result.stderr
    assert result.stdout == "-h\n"


def test_e_option_runs_chunks_in_order(run_lua):
    """CATCHES: multiple -e chunks execute in command-line order before scripts."""
    result = run_lua(["-eprint(1)", "-ea=3", "-e", "print(a)"])
    assert result.returncode == 0, result.stderr
    assert result.stdout == "1\n3\n"


def test_script_with_utf8_bom_and_bad_bom(run_lua, tmp_path):
    """CATCHES: UTF-8 BOM scripts run while malformed BOM bytes fail parsing."""
    script = tmp_path / "bom.lua"
    script.write_bytes(b"\xef\xbb\xbfprint(3)\n")
    ok = run_lua([str(script)])
    assert ok.returncode == 0, ok.stderr
    assert ok.stdout == "3\n"

    bad_script = tmp_path / "bad_bom.lua"
    bad_script.write_bytes(b"\xef\xbbprint(3)\n")
    bad = run_lua([str(bad_script)])
    assert bad.returncode != 0
    assert "unexpected symbol" in bad.stderr


def test_environment_paths_and_versioned_overrides(run_lua, tmp_path):
    """CATCHES: Lua package path environment variables and version overrides apply."""
    script = tmp_path / "path.lua"
    script.write_text("print(package.path)\n")

    base = run_lua([str(script)], env={"LUA_INIT": "", "LUA_PATH": "x"})
    assert base.returncode == 0, base.stderr
    assert base.stdout == "x\n"

    versioned = run_lua(
        [str(script)],
        env={"LUA_INIT": "", "LUA_PATH": "x", "LUA_PATH_5_5": "y"},
    )
    assert versioned.returncode == 0, versioned.stderr
    assert versioned.stdout == "y\n"


def test_lua_init_string_file_and_E_ignores_environment(run_lua, tmp_path):
    """CATCHES: LUA_INIT string/file execution and -E environment ignoring behavior."""
    script = tmp_path / "show_x.lua"
    script.write_text("print(X)\n")

    from_string = run_lua(
        [str(script), "3.2"],
        env={"LUA_INIT": "X=tonumber(arg[1])"},
    )
    assert from_string.returncode == 0, from_string.stderr
    assert from_string.stdout == "3.2\n"

    init_file = tmp_path / "init.lua"
    init_file.write_text("X = 10\n")
    from_file = run_lua([str(script)], env={"LUA_INIT": f"@{init_file}"})
    assert from_file.returncode == 0, from_file.stderr
    assert from_file.stdout == "10\n"

    ignored = run_lua(
        ["-E", "-e", "print(package.path:find('xxx') == nil)"],
        env={"LUA_INIT": "error(10)", "LUA_PATH": "xxx"},
    )
    assert ignored.returncode == 0, ignored.stderr
    assert ignored.stdout == "true\n"


def test_l_option_loads_libraries_and_assigns_globals(run_lua):
    """CATCHES: -l loads libraries and supports assigning them to global names."""
    result = run_lua(
        [
            "-l",
            "str=string",
            "-lm=math",
            "-e",
            "print(m.sin(0)); print(str.upper('alo alo'), m.max(10, 20))",
        ]
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "0.0\nALO ALO\t20\n"


def test_arg_table_for_script_after_options(run_lua, tmp_path):
    """CATCHES: script arg table preserves option separator and varargs after options."""
    script = tmp_path / "args.lua"
    script.write_text(
        "\n".join(
            [
                "print(#arg)",
                "print(arg[1], arg[2], arg[3])",
                "print(arg[-1])",
                "local a, b, c = ...",
                "print(a, b, c)",
            ]
        )
    )

    result = run_lua(["-e", "", "--", str(script), "a", "b", "c"])
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["3", "a\tb\tc", "--", "a\tb\tc"]


def test_warning_controls_with_W(run_lua, tmp_path):
    """CATCHES: -W enables warnings while @on and @off controls affect emission."""
    script = tmp_path / "warns.lua"
    script.write_text(
        """
warn("@allow")
warn("@off", "XXX", "@off")
warn("@off")
warn("@on", "YYY", "@on")
warn("@off")
warn("@on")
warn("", "@on")
warn("@on")
warn("Z", "Z", "Z")
"""
    )
    result = run_lua(["-W", str(script)])
    assert result.returncode == 0, result.stderr
    assert result.stderr == (
        "Lua warning: @offXXX@off\n"
        "Lua warning: @on\n"
        "Lua warning: ZZZ\n"
    )


@pytest.mark.parametrize(
    ("args", "first_line", "has_usage"),
    [
        (["---"], "unrecognized option '---'", True),
        (["-Ex", "--"], "unrecognized option '-Ex'", True),
        (["-vv"], "unrecognized option '-vv'", True),
        (["-iv"], "unrecognized option '-iv'", True),
        (["-e"], "'-e' needs argument", True),
        (["-e", "a"], "(command line):1: syntax error near <eof>", False),
        (["-l"], "'-l' needs argument", True),
        (["--", "-i"], "cannot open -i: No such file or directory", False),
    ],
)
def test_invalid_option_and_startup_errors(run_lua, args, first_line, has_usage):
    """CATCHES: invalid startup options report exact first-line diagnostics and usage."""
    result = run_lua(args)
    assert result.returncode != 0
    expected_first = f"{result.args[0]}: {first_line}\n"
    assert result.stderr.startswith(expected_first)
    expected_usage = (
        "usage: "
        f"{result.args[0]}"
        " [options] [script [args]]\n"
        "Available options are:\n"
        "  -e stat   execute string 'stat'\n"
        "  -i        enter interactive mode after executing 'script'\n"
        "  -l mod    require library 'mod' into global 'mod'\n"
        "  -l g=mod  require library 'mod' into global 'g'\n"
        "  -v        show version information\n"
        "  -E        ignore environment variables\n"
        "  -W        turn warnings on\n"
        "  --        stop handling options\n"
        "  -         stop handling options and execute stdin\n"
    )
    expected_stderr = expected_first + (expected_usage if has_usage else "")
    assert result.stderr == expected_stderr
