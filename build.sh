
cd cpython
# Change max-memory to 4294901760 to fix the error: "wasm-ld: error: maximum memory too small, 20971520 bytes needed"
sed -i 's/--max-memory=10485760/--max-memory=4294901760/' configure
python3 ./Tools/wasm/wasm_build.py wasi-threads