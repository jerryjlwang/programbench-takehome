def test_version_and_help_text(run_janet):
    """CATCHES: version reporting and help text expose the documented Janet CLI surface."""
    version = run_janet(["--version"])
    assert version.returncode == 0, version.stderr
    assert version.stdout == "1.41.2-0fea20c8\n"
    assert version.stderr == ""

    help_result = run_janet(["--help"])
    assert help_result.returncode == 0, help_result.stderr
    assert help_result.stdout.startswith("usage: ")
    assert "--compile (-c) source output" in help_result.stdout
    assert "--expression (-E) code arguments..." in help_result.stdout
    assert help_result.stderr == ""


def test_eval_and_script_arguments(run_janet, tmp_path):
    """CATCHES: eval code runs before script files and script arguments are visible."""
    script = tmp_path / "args.janet"
    script.write_text(
        "\n".join(
            [
                "(print :from-script preloaded)",
                "(print :script-file (in (dyn :args) 0))",
                "(print :payload (in (dyn :args) 1) (in (dyn :args) 2))",
            ]
        )
    )

    result = run_janet(
        ["--eval", "(def preloaded 37)", str(script), "alpha", "beta"],
        cwd=tmp_path,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        "from-script37",
        f"script-file{script}",
        "payloadalphabeta",
    ]
    assert result.stderr == ""


def test_compile_and_load_image_roundtrip(run_janet, tmp_path):
    """CATCHES: source files compile to images that can be loaded and executed later."""
    source = tmp_path / "roundtrip.janet"
    image = tmp_path / "roundtrip.jimage"
    source.write_text('(print "image-loaded" (+ 20 22))\n')

    compiled = run_janet(["--compile", str(source), str(image)], cwd=tmp_path)
    assert compiled.returncode == 0, compiled.stderr
    assert compiled.stdout == "image-loaded42\n"
    assert compiled.stderr == ""

    loaded = run_janet(["--image", str(image)], cwd=tmp_path)
    assert loaded.returncode == 0, loaded.stderr
    assert loaded.stdout == ""
    assert loaded.stderr == ""
