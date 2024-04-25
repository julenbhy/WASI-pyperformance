#!/bin/bash

# Default values
DIR="."
ENV="PYTHONPATH=/builddir/wasi-threads/build/lib.wasi-wasm32-3.13"
EXE="./builddir/wasi-threads/python.wasm"
RUNTIME="wasmtime"  # Default runtime

# Parse command line options
while getopts "r:" opt; do
  case $opt in
    r) RUNTIME="$OPTARG";;
    \?) echo "Invalid option -$OPTARG" >&2
        exit 1;;
  esac
done

# Shift arguments to process non-option arguments
shift $((OPTIND -1))

# cd to cpython directory if it exists
if [ -d "cpython" ]; then
    cd cpython
else
    echo "\e[31mError:\e[0m cpython directory not found"
    exit 1
fi

# If input file specified, check if input file exists under cpython directory
if [ -n "$1" ]; then
    if [ -f "$1" ]; then
        EXE="$1"
    else
        echo -e "\e[31mError:\e[0m File does not exist under cpython directory: $1"
        echo "      Files could be mapped to a different path inside the WASI host"
        echo "      set path/to/your/script.py from inside cpython directory"
        exit 1
        exit 1
    fi
fi

# Run with the selected runtime
case $RUNTIME in
    wasmtime)
        CMD="wasmtime run -S threads --wasm max-wasm-stack=8388608 --dir $DIR --env $ENV $EXE "$@"";;
    wasmer)
        CMD="wasmer run --stack-size=8388608 --dir $DIR --env $ENV $EXE "$@"";;
    iwasm)
        CMD="iwasm --dir=$DIR --env=$ENV $EXE "$@"";;
    *)
        echo -e "\e[31mError\e[0m Invalid runtime specified: $RUNTIME"
        exit 1;;
esac


# Run the command, if it fails, print error and exit
echo -e "\n$CMD\n"
if ! $CMD; then
    echo -e "\e[31mError:\e[0m $RUNTIME failed"
    exit 1
fi
