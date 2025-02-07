#!/bin/env python3
from sys import argv
from sys import stderr

includedCache = {}

def valid_func(line: str):
    funcs = ["@mixin", "@system", "@embed", "@length"]
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

def get_call(line: str):
    funcname = line.split("(")[0] # )
    if (end := line.find(")")) == -1:
        raise Exception("Expected closing ) for macro call")
    argsStr = line.split("(")[1][:end - len(funcname) - 1] # )
    args = [funcname, *argsStr.split(",")]
    return (args, "(".join(line.split("(")[1:])[end - len(funcname):]) # )

def run_func(args, origin=""):
    func = args[0]
    args = args[1:]
    if func == "@mixin":
        file = args[0][1:-1]
        args = args[1:]
        args = [arg.strip()[1:-1] for arg in args] # strip surrounding ""
        # print(f"Running template {file} with args {args}", file=stderr)
        processed = entry(file)
        proc = subprocess.Popen(["tcc", "-run", "-x", "c", "-", *args], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        out = proc.communicate(input=bytes(processed, "utf-8"))[0]
        if proc.returncode != 0:
            if origin != "":
                func = origin
            raise Exception(f"Macro function '{func}' exited with return code {proc.returncode}.")
        return out.decode("utf-8")
    if func == "@system":
        file = args[0][1:-1]
        args = args[1:]
        args = [arg.strip()[1:-1] for arg in args] # strip surrounding ""
        processed = entry(f"/usr/local/include/cmixins/{file}")
        proc = subprocess.Popen(["tcc", "-run", "-x", "c", "-", *args], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        out = proc.communicate(input=bytes(processed, "utf-8"))[0]
        if proc.returncode != 0:
            if origin != "":
                func = origin
            raise Exception(f"Macro function '{func}' exited with return code {proc.returncode}.")
        return out.decode("utf-8")
    if func == "@embed":
        return run_func(["@system", "\"embed.cm\"", args[0]], func)
    if func == "@length":
        return run_func(["@system", "\"length.cm\"", args[0]], func)

    raise Exception(f"Unknown macro function {func}")

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

def expand_file(fileText):
    lines = fileText.split("\n")
    outLines = []
    for line in lines:
        outLines.append(expand_line(line))
    return "\n".join(outLines)

import subprocess

def run_preprocessor(path):
    proc = subprocess.Popen(["tcc", "-E", "-x", "c", f"{path}"], stdout=subprocess.PIPE)
    out = proc.communicate()[0]
    return out

def entry(path):
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
