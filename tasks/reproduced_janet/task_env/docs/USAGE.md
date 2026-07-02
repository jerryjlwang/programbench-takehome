# Janet CLI Task

Implement a command-line Janet interpreter compatible with the provided
`executable` oracle.

The solver-facing command is:

```bash
./executable [options] script args...
```

Supported options shown by the oracle:

```text
usage: executable [options] script args...
Options are:
  --help (-h)             : Show this help
  --version (-v)          : Print the version string
  --stdin (-s)            : Use raw stdin instead of getline like functionality
  --eval (-e) code        : Execute a string of janet
  --expression (-E) code arguments... : Evaluate an expression as a short-fn with arguments
  --debug (-d)            : Set the debug flag in the REPL
  --repl (-r)             : Enter the REPL after running all scripts
  --noprofile (-R)        : Disables loading profile.janet when JANET_PROFILE is present
  --persistent (-p)       : Keep on executing if there is a top-level error (persistent)
  --quiet (-q)            : Hide logo (quiet)
  --flycheck (-k)         : Compile scripts but do not execute (flycheck)
  --syspath (-m) syspath  : Set system path for loading global modules
  --compile (-c) source output : Compile janet source code into an image
  --image (-i)            : Load the script argument as an image file instead of source code
  --nocolor (-n)          : Disable ANSI color output in the REPL
  --color (-N)            : Enable ANSI color output in the REPL
  --library (-l) lib      : Use a module before processing more arguments
  --lint-warn (-w) level  : Set the lint warning level - default is "normal"
  --lint-error (-x) level : Set the lint error level - default is "none"
  --install (-b) dirpath  : Install a bundle from a directory
  --reinstall (-B) name   : Reinstall a bundle by bundle name
  --uninstall (-u) name   : Uninstall a bundle by bundle name
  --update-all (-U)       : Reinstall all installed bundles
  --prune (-P)            : Uninstall all bundles that are orphaned
  --list (-L)             : List all installed bundles
  --                      : Stop handling options
```

The oracle reports Janet `1.41.2` with `--version` and exposes interpreter
behavior through stdout, stderr, exit status, script execution, evaluation
flags, module search paths, image compilation/loading, filesystem effects, and
standard library behavior.

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

The cleanroom intentionally contains no original Janet source tree, package-cache
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
scripts such as `janet.py`, source files, generated data files, or absolute
paths under `/workspace`.

Compatibility is judged end to end through command-line behavior, including:

- option parsing, version/help output, and exit statuses
- `--eval`, `--expression`, script execution, stdin handling, and script args
- module lookup through `--syspath`
- source compilation with `--compile` and image loading with `--image`
- stdout/stderr formatting for successful runs and errors
- deterministic standard library behavior for strings, numbers, arrays,
  tables, buffers, parsing, marshaling, fibers, filesystem IO, and related
  core interpreter features
- Janet language and runtime families including array, asm, buffer, bundle,
  capi, cfuns, compile, corelib, debug, ev, ffi, filewatch, inttypes, io,
  marshal, math, net, os, parse, peg, pretty-printing, special forms, string,
  strtod, struct, symcache, table, tuple, value, and vm behavior
