def test_upstream_user_mode_suite_passes(run_lua, lua_testes):
    """CATCHES: upstream user-mode Lua suite reaches key files and final success."""
    result = run_lua(["-e", "_U=true", "all.lua"], cwd=lua_testes, timeout=45)

    assert result.returncode == 0, result.stderr
    combined = result.stdout + result.stderr
    assert "\n\tStarting Tests\nrandom seeds:" in combined
    assert "***** FILE 'gc.lua'*****" in combined
    assert "***** FILE 'calls.lua'*****" in combined
    assert "***** FILE 'math.lua'*****" in combined
    assert "***** FILE 'files.lua'*****" in combined
    assert result.stdout.endswith("\nfinal OK !!!\n>>> closing state <<<\n\n")
