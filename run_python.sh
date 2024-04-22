WASMTIME=/home/julen/.wasmtime/bin/wasmtime


#exec $WASMTIME run --wasm max-wasm-stack=8388608 --wasm threads=y --wasi threads=y --dir /home/julen/Cloudlab/python/cpython::/ --env PYTHONPATH=/builddir/wasi-threads/build/lib.wasi-wasm32-3.13-pydebug /home/julen/Cloudlab/python/cpython/builddir/wasi-threads/python.wasm "$@"
exec $WASMTIME run --wasm max-wasm-stack=8388608 --wasm threads=y --wasi threads=y --dir /home/julen/Cloudlab/python/WASI-python-benchmarks::/ --env PYTHONPATH=/builddir/wasi-threads/build/lib.wasi-wasm32-3.13-pydebug /home/julen/Cloudlab/python/WASI-python-benchmarks/builddir/wasi-threads/python.wasm "$@"
