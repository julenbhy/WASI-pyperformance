DIR=".::/"
ENV="PYTHONPATH=/builddir/wasi-threads/build/lib.wasi-wasm32-3.13"
EXE="./builddir/wasi-threads/python.wasm"


cd cpython

# Run previous command, if it fails, print error and exit
if ! wasmtime run -S threads --wasm max-wasm-stack=8388608 --dir $DIR --env $ENV $EXE "$@"; then
    echo -e "\e[31mError: wasmtime failed\e[0m"
    echo "      Files clould be mapped to a different path inside the WASI host"
    echo "      set path/to/your/script.py from inside cpython directory"
    exit 1
fi