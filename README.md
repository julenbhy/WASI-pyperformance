# WASI-python-benchmarks

## Build:

### Install WASI-SDK at the deffault path:
    curl -sL https://github.com/WebAssembly/wasi-sdk/releases/download/wasi-sdk-22/wasi-sdk-22.0-linux.tar.gz | sudo tar -xz -C /opt/ && sudo mv /opt/wasi-sdk-22.0 /opt/wasi-sdk

### Clone the repo:

    git clone --recursive https://github.com/julenbhy/WASI-python-benchmarks

### Build the repo:
    ./build.sh


## Run

### Run Python interactive shell:

    ./run_python.sh 

### Run Python script:

    ./run_python.sh path/from/cpython/to/input.py

Keep in mind that Python will take CPython as the root directory. The path to the script should be indicated by taking the CPython directory as the root.
e.g.

    ./run_python.sh benchmarks/test_codes/test.py

### Run pyperformace benchmark

    ./run_python.sh benchmarks/pyperformance/bm_pidigits/run_benchmark.py --python=builddir/wasi-threads/python.wasm


    