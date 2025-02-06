#!/bin/env python3
from sys import argv


def valid_func(line: str):
    funcs = ["@cm"]
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
    return args

def run_func(args):
    func = args[0]
    args = args[1:]
    if func == "@cm":
        file = args[0][1:-1]
        args = args[1:]
        print(f"Running template {file} with args {args}")
        return entry(file)

    raise Exception(f"Unknown macro function {func}")

def expand_line(line: str):
    start = line.find("@")
    if start == -1:
        return line
    if start == 0:
        if valid_func(line):
            funcCall = get_call(line)
            return run_func(funcCall)
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
    import os
    proc = subprocess.Popen(["clang", "-E", "-x", "c", f"{path}"], stdout=subprocess.PIPE)
    out = proc.communicate()[0]
    return out

def entry(path):
    import os
    path = os.getcwd() + "/" + path
    pp = run_preprocessor(path).decode("utf-8")
    cwd = os.getcwd()
    print(path)
    os.chdir(os.path.dirname(path))
    expanded = expand_file(pp)
    os.chdir(os.getcwd())
    return expanded

path = argv[1]
print(entry(path))
