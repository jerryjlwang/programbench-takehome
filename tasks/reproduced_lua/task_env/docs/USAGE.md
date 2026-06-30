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
