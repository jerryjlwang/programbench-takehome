# Lua CLI Task

Implement a command-line Lua interpreter compatible with the provided
`executable` oracle.

The solver-facing command is:

```bash
./executable [options] [script [args]]
```

Supported options shown by the oracle:

```text
usage: executable [options] [script [args]]
Available options are:
  -e stat   execute string 'stat'
  -i        enter interactive mode after executing 'script'
  -l mod    require library 'mod' into global 'mod'
  -l g=mod  require library 'mod' into global 'g'
  -v        show version information
  -E        ignore environment variables
  -W        turn warnings on
  --        stop handling options
  -         stop handling options and execute stdin
```

The oracle reports `Lua 5.5.1` with `-v` and exposes standard Lua interpreter
behavior through stdout, stderr, exit status, command-line arguments,
environment handling, and filesystem effects from scripts.

## Solver contract

You may run `./executable` as a black-box oracle to observe behavior. Your
submission should replace it with a compatible executable named `./executable`.

Do not inspect, preserve, or reuse the oracle binary itself. In particular, do
not run `strings`, `objdump`, `readelf`, `xxd`, `hexdump`, `od`, `strace`,
`ltrace`, `gdb`, `sha256sum`, or similar tools on `./executable`; do not read it
with `cat`, Python `open(..., "rb")`, `Path.read_bytes()`, or similar byte-level
APIs; do not copy or rename it; and do not embed its bytes in generated source.
Only interact with the oracle through normal CLI execution, stdin, stdout,
stderr, file effects, and exit status.

The cleanroom intentionally contains no original Lua source tree, package-cache
source, or hidden source archive. Do not search system directories or caches for
the upstream implementation; build an original replacement from observed
behavior.

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
scripts, source files, generated data files, or absolute paths under
`/workspace`.

Compatibility is judged end to end through command-line behavior, including:

- option parsing, version/help output, and exit statuses
- `-e` chunks, scripts, stdin execution, `arg`, and command-line arguments
- environment handling, including `-E`, `LUA_INIT`, and module search paths
- `-l` library loading, warnings, errors, and stderr formatting
- filesystem-visible effects from scripts
- deterministic standard library behavior for strings, numbers, tables,
  functions, coroutines, modules, package loading, IO, OS helpers, debug hooks,
  parsing/compilation, and related core interpreter features
- Lua language and runtime families including arithmetic and bitwise operators,
  strings and pattern matching, UTF-8 helpers, tables, metatables, closures,
  locals/upvalues, varargs, goto/control flow, coroutines, garbage collection,
  finalizers/close variables, errors, debug library behavior, package/module
  search paths, dynamic library failure behavior, binary chunks, bytecode
  dumping/loading, math, sorting, IO, OS helpers, warnings, environment
  variables, stdin/script execution, and interactive REPL behavior
