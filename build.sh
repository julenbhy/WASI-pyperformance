# Change max-memory to 4294901760 to fix the error: "wasm-ld: error: maximum memory too small, 20971520 bytes needed"
sed -i 's/--max-memory=10485760/--max-memory=4294901760/' cpython/configure
python3 ./cpython/Tools/wasm/wasm_build.py wasi-threads


mkdir -p cpython/benchmarks/pyperformance
cp -r pyperformance/pyperformance/data-files/benchmarks/* cpython/benchmarks/pyperformance

cp -r test_codes cpython/benchmarks/


# Fix pyperf for working with WASM. Solve executable not found error
sed -i 's/args = self.argparser.parse_args(args)/args = self.argparser.parse_args(args)\n        args.python="builddir\/wasi-threads\/python.wasm"/' pyperf/pyperf/_runner.py
cp -r pyperf/pyperf cpython/Lib/