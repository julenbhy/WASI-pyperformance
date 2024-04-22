
CUR_DIR=$(pwd)
DIR="$CUR_DIR/cpython::/"
ENV="PYTHONPATH=/builddir/wasi-threads/build/lib.wasi-wasm32-3.13"
EXE="$CUR_DIR/cpython/builddir/wasi-threads/python.wasm"

#WORKING:
#exec /home/julen/.wasmtime/bin/wasmtime run -S threads --wasm max-wasm-stack=8388608 --wasi preview2 --dir /home/julen/Cloudlab/python/WASI-python-benchmarks/cpython::/ --env PYTHONPATH=/builddir/wasi-threads/build/lib.wasi-wasm32-3.13 /home/julen/Cloudlab/python/WASI-python-benchmarks/cpython/builddir/wasi-threads/python.wasm "$@"

exec /home/julen/.wasmtime/bin/wasmtime run -S threads --wasm max-wasm-stack=8388608 --dir $DIR --env $ENV $EXE "$@"
