def test_upstream_user_mode_suite_passes(run_lua, lua_testes):
    result = run_lua(["-e", "_U=true", "all.lua"], cwd=lua_testes, timeout=45)

    assert result.returncode == 0, result.stderr
    combined = result.stdout + result.stderr
    assert "Starting Tests" in combined
    assert "***** FILE 'gc.lua'*****" in combined
    assert "***** FILE 'calls.lua'*****" in combined
    assert "***** FILE 'math.lua'*****" in combined
    assert "***** FILE 'files.lua'*****" in combined
    assert "final OK !!!" in combined
