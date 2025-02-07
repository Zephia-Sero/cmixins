#!/bin/env python3
from sys import argv
from sys import stderr
from typing import Dict

includedCache: Dict[str, str] = {}
binaryCache = {}
import line_profiler

@line_profiler.profile
def valid_func(line: str):
    funcs = ["@mixin", "@mixinsys", "@include", "@includesys",
             "@embed", "@length"]
    vars = []
    for func in funcs:
        if line.startswith(func):
            if line[len(func)] == "(":
                return True
            raise Exception("Expected ( after macro function name.") #))
    for var in vars:
        if line.startswith(var):
            if line[len(var)] == "(":
                raise Exception("Macro variable cannot be called.") #)
            return True
    return False

@line_profiler.profile
def get_call(line: str):
    funcname = line.split("(")[0] # )
    if (end := line.find(")")) == -1:
        raise Exception("Expected closing ) for macro call")
    argsStr = line.split("(")[1][:end - len(funcname) - 1] # )
    args = [funcname, *argsStr.split(",")]
    return (args, "(".join(line.split("(")[1:])[end - len(funcname):]) # ))

@line_profiler.profile
def make_binary(path):
    if path in binaryCache.keys():
        return binaryCache[path]
    source = entry(path)
    proc = subprocess.Popen(["mktemp", "-t", "cmixins.cachedBinary.XXXXXXXX"], stdout=subprocess.PIPE)
    tmpF = proc.communicate()[0].strip()
    proc = subprocess.Popen(["tcc", "-O3", "-o", tmpF, "-x", "c", "-"], stdin=subprocess.PIPE)
    proc.communicate(input=bytes(source, "utf-8"))
    binaryCache[path] = tmpF
    return tmpF

@line_profiler.profile
def run_func(args, origin=""):
    func = args[0]
    args = args[1:]
    if func == "@mixin":
        file = args[0][1:-1]
        args = args[1:]
        args = [arg.strip()[1:-1] for arg in args] # strip surrounding ""
        # print(f"Running template {file} with args {args}", file=stderr)
        binary = make_binary(file)
        proc = subprocess.Popen([binary, *args], stdout=subprocess.PIPE)
        out = proc.communicate()[0]
        if proc.returncode != 0:
            if origin != "":
                func = origin
            raise Exception(f"Macro function '{func}' exited with return code {proc.returncode}.")
        return out.decode("utf-8")
    if func == "@mixinsys":
        file = args[0][1:-1]
        args = args[1:]
        args = [arg.strip()[1:-1] for arg in args] # strip surrounding ""
        binary = make_binary(f"/usr/local/include/cmixins/{file}")
        proc = subprocess.Popen([binary, *args], stdout=subprocess.PIPE)
        out = proc.communicate()[0]
        if proc.returncode != 0:
            if origin != "":
                func = origin
            raise Exception(f"Macro function '{func}' exited with return code {proc.returncode}.")
        return out.decode("utf-8")
    if func == "@include":
        file = args[0][1:-1]
        source = entry(file)
        return source
    if func == "@includesys":
        file = f"/usr/local/include/cmixins/include/{args[0][1:-1]}"
        source = entry(file)
        return source
    if func == "@embed":
        return run_func(["@mixinsys", "\"embed.cm\"", args[0]], func)
    if func == "@length":
        return run_func(["@mixinsys", "\"length.cm\"", args[0]], func)

    raise Exception(f"Unknown macro function {func}")

@line_profiler.profile
def expand_line(line: str):
    start = line.find("@")
    if start == -1:
        return line
    if start == 0:
        if valid_func(line):
            funcCall, right = get_call(line)
            return run_func(funcCall) + expand_line(right)
        else:
            return line
    left = line[:start]
    right = expand_line(line[start:])
    return left + right

@line_profiler.profile
def expand_file(fileText):
    lines = fileText.split("\n")
    outLines = []
    for line in lines:
        outLines.append(expand_line(line))
    return "\n".join(outLines)

import subprocess

@line_profiler.profile
def run_preprocessor(path):
    proc = subprocess.Popen(["tcc", "-O3", "-E", "-x", "c", f"{path}"], stdout=subprocess.PIPE)
    out = proc.communicate()[0]
    return out

@line_profiler.profile
def entry(path) -> str:
    import os
    if not path.startswith("/"):
        path = os.getcwd() + "/" + path
    if path in includedCache.keys():
        return includedCache[path]
    pp = run_preprocessor(path).decode("utf-8")
    cwd = os.getcwd()
    os.chdir(os.path.dirname(path))
    expanded = expand_file(pp)
    includedCache[path] = expanded
    os.chdir(cwd)
    return expanded

path = argv[1]
print(entry(path))

for path in binaryCache.values():
    import os
    if os.path.isfile(path):
        os.remove(path)
