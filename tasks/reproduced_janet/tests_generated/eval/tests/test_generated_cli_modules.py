def test_syspath_imports_local_module(run_janet, tmp_path):
    """CATCHES: syspath controls module discovery for imported Janet source files."""
    mods = tmp_path / "mods"
    mods.mkdir()
    (mods / "thing.janet").write_text("(def value 144)\n")
    script = tmp_path / "use_module.janet"
    script.write_text("(import thing) (print :module thing/value)\n")

    result = run_janet(["--syspath", str(mods), str(script)], cwd=tmp_path)

    assert result.returncode == 0, result.stderr
    assert result.stdout == "module144\n"
    assert result.stderr == ""


def test_eval_syntax_error_reports_parse_location(run_janet):
    """CATCHES: eval parse errors report stable syntax diagnostics and traceback frames."""
    result = run_janet(["--eval", "(defn broken [x] (+ x )"])

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr.startswith("error: unexpected end of source, ( opened at line 1, column 1\n")
    assert "parse-all [boot.janet]" in result.stderr
    assert "eval-string [boot.janet]" in result.stderr


def test_runtime_error_reports_eval_trace(run_janet):
    """CATCHES: runtime errors from eval include the error value and eval traceback frame."""
    result = run_janet(["--eval", '(error "boom-time")'])

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr.startswith("error: boom-time\n")
    assert "in thunk [eval] (tail call)" in result.stderr
    assert "cli-main [boot.janet]" in result.stderr
