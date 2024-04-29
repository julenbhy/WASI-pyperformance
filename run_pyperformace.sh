cd cpython

# Set python path to the python binary built from the cpython source
PYTHON=./builddir/build/python

all_benchmarks=(
    "bm_2to3" "bm_async_generators" "bm_asyncio_tcp" "bm_asyncio_websockets"
    "bm_async_tree" "bm_chameleon" "bm_chaos" "bm_comprehensions"
    "bm_concurrent_imap" "bm_coroutines" "bm_coverage" "bm_crypto_pyaes"
    "bm_dask" "bm_deepcopy" "bm_deltablue" "bm_django_template"
    "bm_docutils" "bm_dulwich_log" "bm_fannkuch" "bm_float"
    "bm_gc_collect" "bm_gc_traversal" "bm_generators" "bm_genshi"
    "bm_go" "bm_hexiom" "bm_hg_startup" "bm_html5lib" "bm_json_dumps"
    "bm_json_loads" "bm_logging" "bm_mako" "bm_mdp" "bm_meteor_contest"
    "bm_nbody" "bm_nqueens" "bm_pathlib" "bm_pickle" "bm_pidigits"
    "bm_pprint" "bm_pyflate" "bm_python_startup" "bm_raytrace"
    "bm_regex_compile" "bm_regex_dna" "bm_regex_effbot" "bm_regex_v8"
    "bm_richards" "bm_richards_super" "bm_scimark" "bm_spectral_norm"
    "bm_sqlalchemy_declarative" "bm_sqlalchemy_imperative" "bm_sqlglot"
    "bm_sqlite_synth" "bm_sympy" "bm_telco" "bm_tomli_loads"
    "bm_tornado_http" "bm_typing_runtime_protocols" "bm_unpack_sequence"
    "bm_xml_etree"
)


# List of benchmarks using bench_func
bench_func=(
    "bm_go" "bm_chameleon"  "bm_concurrent_imap" "bm_concurrent_imap" "bm_dulwich_log"
    "bm_chaos"  "bm_logging" "bm_logging" "bm_float" "bm_django_template" "bm_pprint"
    "bm_pprint" "bm_nqueens" "bm_json_dumps" "bm_richards_super" "bm_pidigits"
    "bm_html5lib" "bm_mako" "bm_json_loads" "bm_xml_etree" "bm_richards" "bm_deltablue" "bm_fannkuch"
)

# List of benchmarks using bench_command
bench_command=( "bm_2to3" "bm_python_startup" "bm_hg_startup" )

# List of benchmarks using bench_time_func
bench_time_func=(
    "bm_coroutines" "bm_sqlalchemy_declarative" "bm_meteor_contest" "bm_spectral_norm"
    "bm_telco" "bm_mdp" "bm_sympy" "bm_hexiom" "bm_regex_v8" "bm_sqlite_synth"
    "bm_generators" "bm_raytrace" "bm_gc_collect" "bm_logging" "bm_unpack_sequence"
    "bm_genshi" "bm_pathlib" "bm_nbody" "bm_sqlglot" "bm_pickle" "bm_coverage"
    "bm_scimark" "bm_regex_effbot" "bm_comprehensions" "bm_crypto_pyaes" "bm_deepcopy"
    "bm_regex_compile" "bm_tornado_http" "bm_xml_etree" "bm_pyflate" "bm_regex_dna"
    "bm_sqlalchemy_imperative" "bm_typing_runtime_protocols" "bm_tomli_loads"
    "bm_docutils" "bm_gc_traversal"
)

# List of benchmarks using bench_async_func
bench_async_func=(
    "bm_async_tree" "bm_dask" "bm_asyncio_websockets"
    "bm_asyncio_tcp" "bm_async_generators"
)


# SET BENCHMARKS TO RUN
benchmarks=("${bench_async_func[@]}")


# Create failed list
failed_list=()

# Iterate over directories in benchmarks/pyperformance
for benchmark in "${benchmarks[@]}"
do
    echo -e "\e[32m\nRunning benchmark $benchmark\e[0m"

    cmd="$PYTHON benchmarks/pyperformance/$benchmark/run_benchmark.py -p 1"

    # If benchmark is bm_sqlglot, add --benchmark parameter
    if [ "$benchmark" == "bm_sqlglot" ]; then
        cmd="$cmd normalize" # parse, transpile, optimize or normalize
    elif [ "$benchmark" == "bm_pickle" ]; then
        cmd="$cmd pickle" # pickle, pickle_dict, pickle_list, unpickle or unpickle_list
    fi

    echo $cmd
    if ! $cmd; then
        echo -e "\e[31mError:\e[0m $benchmark failed"
        failed_list+=($benchmark)
    fi
done

# Print how many benchmarks failed
total=${#benchmarks[@]}
failed=${#failed_list[@]}
echo -e "\n\e[32m$((total-failed))/$total benchmarks passed\e[0m"


# Print failed list
echo -e "\n\e[31mFailed benchmarks:\e[0m"
for failed in "${failed_list[@]}"
do
    echo "  $failed"
done
