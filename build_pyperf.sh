
# Install pyperf
# Add pyperf to cpython
cp -r pyperf/pyperf cpython/Lib/

# Change the _manager.py to _manager_wasm.py to avoid using Popen and pipes
cp _manager_wasm.py cpython/Lib/pyperf/_manager.py

# Set hostname to "Wasm" to avoid using socket.gethostname()
sed -i 's/hostname = socket.gethostname()/hostname = "Wasm"/' cpython/Lib/pyperf/_collect_metadata.py



# Copy every dir in Libs to cpython/Lib

cp -r Libs/* cpython/Lib/
