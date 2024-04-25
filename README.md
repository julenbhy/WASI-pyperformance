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

Currently not working

## Adding additional libraries:
Download the Python code of the required library and add it to the directory cpython/Lib. You can follow the example of pyperf library.





## Modifications: 

#### Set wasm cpython:
pyperf/_manager.py:

    def spawn_worker(self, calibrate_loops, calibrate_warmups):
    		...
            # set cmd command to run wasmtime: 
            wasmtime_cmd = ["wasmtime", "run", "-S", "threads", "--wasm", "max-wasm-stack=8388608", \
                            "--dir", "/home/julen/Cloudlab/WASI-python-benchmarks/cpython::/", \
                            "--env", "PYTHONPATH=/builddir/wasi-threads/build/lib.wasi-wasm32-3.13", \
                            "/home/julen/Cloudlab/WASI-python-benchmarks/cpython/builddir/wasi-threads/python.wasm"] 

            # Remove first element of cmd list and prepend wasmtime_cmd
            cmd.pop(0)
            cmd = wasmtime_cmd + cmd
            
            # Solve ERROR: Unable to locate the Python executable: ''
            cmd = cmd + ["--python", "/dev/null"]
            
            # change "'--pipe', '4' " to "'--pipe', '2'"
            cmd[14] = "2"
            print("Executig: ", cmd)

            proc = subprocess.run(cmd, env=env, **kw, capture_output=True)

            ...


#### Avoid AttributeError: module 'socket' has no attribute 'gethostname':
pyperf/__collect_metadata.py:

    def collect_system_metadata(metadata):
        ...
        # Hostname
        #hostname = socket.gethostname()
        hostname = "wasm-host"
        if hostname:
            metadata['hostname'] = hostname
        ...

