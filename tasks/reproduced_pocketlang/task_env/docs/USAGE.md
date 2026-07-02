# PocketLang CLI Task

Implement a command-line PocketLang interpreter compatible with the provided
`executable` oracle.

The solver-facing command is:

```bash
./executable [options] [-c command | script.pk] [script-args...]
```

The oracle supports these visible command-line options:

```text
Usage: pocket ... [-c cmd | file] ...
    -c, --cmd=<str>   Evaluate and run the passed string.
    -d, --debug       Compile and run the debug version.
    -h, --help        Prints this help message and exit.
    -q, --quiet       Don't print version and copyright statement on REPL startup.
    -v, --version     Prints the pocketlang version and exit.
```

The oracle reports `pocketlang 0.1.0` with `--version` and exposes behavior
through stdout, stderr, exit status, command-string execution with `-c` and
`--cmd`, script file execution, imports, modules, classes, closures, fibers,
JSON/path/math/io/os/time/types library behavior, `types.ByteBuffer` and
`types.Vector` behavior, filesystem/environment helpers, and runtime/compiler
errors.

## Solver Contract

You may run `./executable` as a black-box oracle to observe behavior. Your
submission should replace it with a compatible executable named `./executable`.

Do not inspect, preserve, or reuse the oracle binary itself. In particular, do
not run `strings`, `objdump`, `readelf`, `xxd`, `hexdump`, `od`, `strace`,
`ltrace`, `gdb`, `sha256sum`, or similar tools on `./executable`; do not read it
with `cat`, Python `open(..., "rb")`, `Path.read_bytes()`, or similar byte-level
APIs; do not copy or rename it; and do not embed its bytes in generated source.
Only interact with the oracle through normal CLI execution, stdin, stdout,
stderr, file effects, and exit status.

The cleanroom intentionally contains no original PocketLang source tree,
package-cache source, or hidden source archive. Do not search system directories
or caches for the upstream implementation; build an original replacement from
observed behavior.

The evaluator runs `./compile.sh` in an offline `gcc:13-bookworm` environment
with network disabled. The final compile step must create an executable file at
`./executable`. In the solver cleanroom, however, `./executable` starts as the
protected oracle. The provided `compile.sh` therefore builds `./candidate` while
that oracle is present, so you can run `./candidate` for development checks
without destroying the oracle. During final scoring, the evaluator removes any
prebuilt `./executable` before running `compile.sh`, so the same script builds
the scored `./executable`.

You may edit `compile.sh`, but preserve this distinction: do not overwrite
`./executable` during observation. The final build must work without downloading
dependencies.

After compilation, scoring runs only the produced `./executable` in the
hidden-test container. Other submitted files are not available at runtime. The
executable must therefore be self-contained: do not make it depend on sibling
scripts, generated data files, or absolute paths under `/workspace`.
