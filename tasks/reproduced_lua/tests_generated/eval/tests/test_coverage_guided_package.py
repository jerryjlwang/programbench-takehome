def test_package_searchpath_replaces_separators_and_reports_misses(run_lua, tmp_path):
    """CATCHES: package.searchpath replaces separators and reports missing files."""
    modules = tmp_path / "mods"
    modules.mkdir()
    nested = modules / "a" / "b"
    nested.mkdir(parents=True)
    (nested / "init.lua").write_text("return 'nested'\n")
    (tmp_path / "XXxX").write_text("")

    script = tmp_path / "searchpath.lua"
    script.write_text(
        f"""
local found = assert(package.searchpath("a.b", "{modules}/?/init.lua"))
print(found:match("a/b/init%.lua") ~= nil)
local miss, err = package.searchpath("none", "{modules}/?.lua")
print(miss == nil, err:find("no file") ~= nil)
local custom = package.searchpath("--x-", "?", "-", "X")
print(custom)
"""
    )
    result = run_lua([str(script)], cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["true", "true\ttrue", "XXxX"]


def test_require_uses_preload_and_returns_loader_extra_value(run_lua, tmp_path):
    """CATCHES: require uses package.preload and returns loader extra values."""
    script = tmp_path / "preload.lua"
    script.write_text(
        """
package.preload.pl = function(name)
  return {name, "payload"}, ":preload:"
end
local mod, where = require "pl"
print(mod[1], mod[2], where)
print(require "pl" == mod)
"""
    )
    result = run_lua([str(script)])
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["pl\tpayload\t:preload:", "true"]


def test_require_rejects_non_table_searchers(run_lua, tmp_path):
    """CATCHES: require rejects a non-table package.searchers value with diagnostics."""
    script = tmp_path / "bad_searchers.lua"
    script.write_text(
        """
package.searchers = true
local ok, err = pcall(require, "anything")
print(ok)
print(err:find("package.searchers") ~= nil)
print(err:find("must be a table") ~= nil)
"""
    )
    result = run_lua([str(script)])
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["false", "true", "true"]


def test_require_rejects_non_string_package_path(run_lua, tmp_path):
    """CATCHES: require rejects a non-string package.path value with diagnostics."""
    script = tmp_path / "bad_path.lua"
    script.write_text(
        """
package.path = {}
local ok, err = pcall(require, "anything")
print(ok)
print(err:find("package.path") ~= nil)
print(err:find("must be a string") ~= nil)
"""
    )
    result = run_lua([str(script)])
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["false", "true", "true"]


def test_package_loadlib_reports_open_and_init_failures(run_lua, tmp_path):
    """CATCHES: package.loadlib reports dynamic-library open failures structurally."""
    not_a_library = tmp_path / "not-a-library.so"
    not_a_library.write_text("definitely not an ELF shared library\n")
    script = tmp_path / "loadlib_fail.lua"
    script.write_text(
        f"""
local f, err, where = package.loadlib("{not_a_library}", "luaopen_missing")
print(f == nil, type(err), where)
local f2, err2, where2 = package.loadlib("{not_a_library}", "*")
print(f2 == nil, type(err2), where2)
"""
    )
    result = run_lua([str(script)])
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["true\tstring\topen", "true\tstring\topen"]


def test_require_reports_file_load_syntax_error(run_lua, tmp_path):
    """CATCHES: require reports syntax errors from module files it locates."""
    mods = tmp_path / "mods"
    mods.mkdir()
    (mods / "bad.lua").write_text("return function(\n")
    script = tmp_path / "bad_require.lua"
    script.write_text(
        f"""
package.path = "{mods}/?.lua"
local ok, err = pcall(require, "bad")
print(ok)
print(err:find("error loading module 'bad'") ~= nil)
print(err:find("near <eof>") ~= nil)
"""
    )
    result = run_lua([str(script)])
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["false", "true", "true"]
