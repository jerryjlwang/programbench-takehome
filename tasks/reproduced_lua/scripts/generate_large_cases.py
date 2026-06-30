#!/usr/bin/env python3
"""Generate small Lua behavioral cases and capture gold outputs.

Run this inside a linux/amd64 container because the gold executable is Linux.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path


def q(s: str) -> str:
    return json.dumps(s)


def sanitize(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9_]+", "_", value).strip("_").lower()
    return value[:80] or "case"


def candidates() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []

    for i in range(1, 181):
        a = i
        b = (i * 7) % 53 + 1
        out.append((f"arith_add_{i}", f"print({a} + {b})"))
        out.append((f"arith_mix_{i}", f"print(({a} * {b}) - ({b} // 2))"))
        out.append((f"arith_mod_{i}", f"print(({a * b}) % {b + 3})"))
        out.append((f"arith_pow_{i}", f"print(({i % 8 + 2}) ^ 3)"))

    words = [
        "alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta",
        "iota", "kappa", "lambda", "mu", "nu", "xi", "omicron", "pi",
        "rho", "sigma", "tau", "upsilon", "phi", "chi", "psi", "omega",
    ]
    for i in range(220):
        w = words[i % len(words)]
        suffix = str(i % 17)
        s = f"{w}-{suffix}"
        out.append((f"string_upper_{i}", f"print(string.upper({q(s)}))"))
        out.append((f"string_reverse_{i}", f"print(string.reverse({q(s)}))"))
        out.append((f"string_sub_{i}", f"print(string.sub({q(s)}, 2, -2))"))
        out.append((f"string_format_{i}", f"print(string.format('%s:%03d', {q(w)}, {i}))"))

    for i in range(180):
        vals = [(i + j * 3) % 97 for j in range(1, 6)]
        arr = "{" + ",".join(str(v) for v in vals) + "}"
        out.append((f"table_len_{i}", f"local t={arr}; print(#t, t[1], t[#t])"))
        out.append((f"table_concat_{i}", f"local t={{'a',{q(str(i))},'z'}}; print(table.concat(t, ':'))"))
        out.append((f"table_sort_{i}", f"local t={arr}; table.sort(t); print(table.concat(t, ','))"))
        key = f"k{i % 31}"
        out.append((f"table_key_{i}", f"local t={{[{q(key)}]={i}}}; print(t[{q(key)}] + 1)"))

    for i in range(170):
        n = i % 25 + 1
        out.append((f"loop_sum_{i}", f"local s=0; for j=1,{n} do s=s+j end; print(s)"))
        out.append((f"loop_while_{i}", f"local j,s=0,1; while j<{n} do j=j+1; s=s*2 end; print(j,s)"))
        out.append((f"loop_repeat_{i}", f"local j=0; repeat j=j+3 until j>{n}; print(j)"))
        out.append((f"loop_break_{i}", f"local s=0; for j=1,99 do if j>{n} then break end; s=s+j end; print(s)"))

    for i in range(180):
        n = i % 20 + 2
        out.append((f"func_call_{i}", f"local function f(x,y) return x*2+y end; print(f({n},{i % 9}))"))
        out.append((f"func_closure_{i}", f"local function mk(x) return function(y) return x+y end end; print(mk({n})({i % 13}))"))
        out.append((f"func_vararg_{i}", "local function f(...) return select('#', ...), select(2, ...) end; print(f('a','b','c'))"))
        out.append((f"func_multi_{i}", f"local function f() return {n},{n+1},{n+2} end; local a,b,c=f(); print(a,b,c)"))

    patterns = [
        ("abc123def", "%d+"),
        ("one two three", "%a+"),
        ("x=42;y=99", "(%a)=(%d+)"),
        ("hello.lua", "%.lua$"),
        ("2026-06-29", "(%d+)%-(%d+)%-(%d+)"),
    ]
    for i in range(160):
        s, pat = patterns[i % len(patterns)]
        out.append((f"pattern_find_{i}", f"local a,b,c,d=string.find({q(s)}, {q(pat)}); print(a,b,c or '',d or '')"))
        out.append((f"pattern_gsub_{i}", f"print((string.gsub({q(s)}, {q(pat)}, '#')))"))

    for i in range(160):
        n = i % 63 + 1
        out.append((f"bit_band_{i}", f"print(({n} & {n * 3}) | 1)"))
        out.append((f"bit_shift_{i}", f"print(({n} << 2) >> 1)"))
        out.append((f"bit_xor_{i}", f"print(({n} ~ {n + 5}) & 255)"))

    for i in range(160):
        n = i % 40 + 1
        out.append((f"math_minmax_{i}", f"print(math.min({n}, {n+7}), math.max({n}, {n+7}))"))
        out.append((f"math_type_{i}", f"print(math.type({n}), math.type({n}.5))"))
        out.append((f"math_abs_{i}", f"print(math.abs(-{n}), math.tointeger({n}.0))"))

    for i in range(130):
        out.append((f"coroutine_basic_{i}", f"local co=coroutine.create(function() coroutine.yield({i}); return {i+1} end); print(coroutine.resume(co)); print(coroutine.resume(co))"))
        out.append((f"pcall_basic_{i}", f"local ok,msg=pcall(function() error('case-{i}') end); print(ok, msg:match('case%-{i}') ~= nil)"))
        out.append((f"metatable_index_{i}", f"local t=setmetatable({{}}, {{__index=function(_,k) return k..':{i}' end}}); print(t.answer)"))

    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--executable", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--target", type=int, required=True)
    args = parser.parse_args()

    cases = []
    seen_ids = set()
    for raw_id, code in candidates():
        case_id = sanitize(raw_id)
        if case_id in seen_ids:
            continue
        seen_ids.add(case_id)
        result = subprocess.run(
            [args.executable, "-e", code],
            text=True,
            capture_output=True,
            timeout=5,
        )
        if result.returncode != 0 or result.stderr or not result.stdout:
            continue
        cases.append(
            {
                "id": case_id,
                "args": ["-e", code],
                "stdin": None,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        )
        if len(cases) == args.target:
            break

    if len(cases) != args.target:
        raise SystemExit(f"generated {len(cases)} cases, wanted {args.target}")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(cases, indent=2) + "\n")
    print(f"wrote {len(cases)} cases to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
