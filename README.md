# WASI-python-benchmarks

## Build:

### Clone this repository:

    git clone --recursive https://github.com/julenbhy/WASI-python-benchmarks

### Install WASI-SDK at the deffault path:
    curl -sL https://github.com/WebAssembly/wasi-sdk/releases/download/wasi-sdk-22/wasi-sdk-22.0-linux.tar.gz | sudo tar -xz -C /opt/ && sudo mv /opt/wasi-sdk-22.0 /opt/wasi-sdk

### Build the repository:
    ./build.sh


## Run

### Run Python interactive shell:

    ./run_python.sh 

### Run Python script:

    ./run_python.sh path/from/cpython/to/input.py

Keep in mind that Python will take CPython as the root directory. The path to the script should be indicated by taking the CPython directory as the root.

For example:

#### Run test code

    ./run_python.sh benchmarks/test_codes/test.py

#### Run pyperformace benchmark

    ./run_python.sh benchmarks/pyperformance/bm_pidigits/run_benchmark.py --python=builddir/wasi-threads/python.wasm

Currently not working:

```diff
- AttributeError: module 'os' has no attribute 'pipe'. Did you mean: 'popen'? 
```

## Adding additional libraries:
Download the Python code of the required library and add it to the directory cpython/Lib. You can follow the example of pyperf library.



    