# Change max-memory to 4294901760 to fix the error: "wasm-ld: error: maximum memory too small, 20971520 bytes needed"
sed -i 's/--max-memory=10485760/--max-memory=4294901760/' cpython/configure
python3 ./cpython/Tools/wasm/wasm_build.py wasi-threads


mkdir -p cpython/benchmarks/pyperformance
cp -r pyperformance/pyperformance/data-files/benchmarks/* cpython/benchmarks/pyperformance

cp -r benchmarks/ cpython/



# Add pyperf to cpython
cp -r pyperf/pyperf cpython/Lib/

# Change the _manager.py to _manager_wasm.py to avoid using Popen and pipes
cp _manager_wasm.py cpython/Lib/pyperf/_manager.py

# Set hostname to "Wasm" to avoid using socket.gethostname()
sed -i 's/hostname = socket.gethostname()/hostname = "Wasm"/' cpython/Lib/pyperf/_collect_metadata.py

# Add pyperformance to libraries
cp -r cpython/benchmarks/pyperformance/bm_2to3/vendor/src/lib2to3 cpython/Lib/
