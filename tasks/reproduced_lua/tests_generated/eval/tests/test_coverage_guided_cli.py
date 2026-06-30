def test_no_option_stdin_executes_as_file(run_lua):
    """CATCHES: stdin without CLI options is executed as a Lua source file."""
    result = run_lua([], input_text="print(10)\nprint(2)\n")
    assert result.returncode == 0, result.stderr
    assert result.stdout == "10\n2\n"


def test_interactive_mode_evaluates_expressions_and_continuations(run_lua):
    """CATCHES: interactive mode evaluates expressions, continuations, and stored globals."""
    result = run_lua(
        ["-e", "_PROMPT='' _PROMPT2=''", "-i"],
        input_text="(6*2-6)\na =\n17 + 4\nprint(a)\na+1\n",
    )
    assert result.returncode == 0, result.stderr
    echo_lines = {"(6*2-6)", "a =", "17 + 4", "print(a)", "a+1"}
    semantic_lines = [line for line in result.stdout.splitlines() if line not in echo_lines]
    assert semantic_lines == [
        "Lua 5.5.1  Copyright (C) 1994-2026 Lua.org, PUC-Rio",
        "6",
        "21",
        "22",
        "",
    ]


def test_interactive_mode_reports_incomplete_syntax(run_lua):
    """CATCHES: interactive parser reports incomplete field syntax at end of input."""
    result = run_lua(["-i"], input_text="a.\n")
    assert result.returncode == 0
    assert result.stderr == "stdin:1: <name> expected near <eof>\n"


def test_interactive_mode_warns_that_locals_do_not_survive(run_lua):
    """CATCHES: interactive mode warns when local declarations cannot survive lines."""
    result = run_lua(["-i"], input_text="  local x\n")
    assert result.returncode == 0
    assert "warning: locals do not survive across lines" in result.stderr


def test_interactive_print_failure_is_reported(run_lua):
    """CATCHES: interactive expression printing reports failures from the print hook."""
    result = run_lua(["-e", "print=nil", "-i"], input_text="10\n")
    assert result.returncode == 0
    assert "error calling 'print'" in result.stderr


def test_error_object_uses_tostring_metamethod(run_lua, tmp_path):
    """CATCHES: runtime errors stringify non-string objects through __tostring."""
    script = tmp_path / "error_object.lua"
    script.write_text(
        """
local debug = require "debug"
local m = {x = 0}
setmetatable(m, {
  __tostring = function(x)
    return tostring(debug.getinfo(4).currentline + x.x)
  end
})
error(m)
"""
    )
    result = run_lua([str(script)])
    assert result.returncode != 0
    assert result.stderr.endswith(": 9\n")


def test_non_string_error_object_is_described(run_lua, tmp_path):
    """CATCHES: runtime errors without string conversion describe object value types."""
    script = tmp_path / "table_error.lua"
    script.write_text("error({})\n")
    result = run_lua([str(script)])
    assert result.returncode != 0
    assert "error object is a table value" in result.stderr


def test_script_close_variables_run_before_os_exit(run_lua, tmp_path):
    """CATCHES: close variables run in reverse order before os.exit terminates."""
    script = tmp_path / "close_exit.lua"
    script.write_text(
        """
local x <close> = setmetatable({}, {
  __close = function(self, err)
    assert(err == nil)
    print("Ok")
  end
})
local e1 <close> = setmetatable({}, {__close = function() print(120) end})
os.exit(true, true)
"""
    )
    result = run_lua([str(script)])
    assert result.returncode == 0, result.stderr
    assert result.stdout == "120\nOk\n"
