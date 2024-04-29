cd cpython

# Set python path to the python binary built from the cpython source
PYTHON=./builddir/build/python

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
benchmarks=("${bench_func[@]}" "${bench_command[@]}" "${bench_time_func[@]}" "${bench_async_func[@]}")


output_file="benchmarks/pyperformance/pyperformance_results.txt"

verbose=False


# Create failed list
failed_list=()

# Reset output file
echo -n "" > "$output_file"

# Iterate over directories in benchmarks/pyperformance
for benchmark in "${benchmarks[@]}"
do
    echo -e "\nRunning benchmark $benchmark"

    # Base command for all benchmarks
    cmd="$PYTHON -W ignore benchmarks/pyperformance/$benchmark/run_benchmark.py -p 1"

    # Set specific arguments for each benchmark
    if [ "$benchmark" == "bm_async_tree" ]; then
        cmd="$cmd none" # none, eager, io, eager_io, memoization, eager_memoization, cpu_io_mixed or eager_cpu_io_mixed
    elif [ "$benchmark" == "bm_sqlglot" ]; then
        cmd="$cmd normalize" # parse, transpile, optimize or normalize
    elif [ "$benchmark" == "bm_pickle" ]; then
        cmd="$cmd pickle" # pickle, pickle_dict, pickle_list, unpickle or unpickle_list
    fi


    if [ "$verbose" == "True" ]; then
        echo -e "$cmd"
    fi
    output=$($cmd 2>&1)    

    # Check if the execution was successful
    if [ $? -eq 0 ]; then
        clean_output=$(echo "$output" | grep -E '[0-9]')
        if [ "$verbose" == "True" ]; then
            echo -e "$clean_output"
        fi
        echo -e "$clean_output" >> "$output_file"
    else
        echo -e "\e[31mExecution failed\e[0m"
        if [ "$verbose" == "True" ]; then
            echo -e "\e[31m$output\e[0m"
        fi
        echo -e "$benchmark: Failed" >> "$output_file"
        failed_list+=($benchmark)
    fi
done

# Print end message. Print resulting info
echo -e "\n\e[32mBENCHMARKING FINISHED\e[0m"
echo -e "\nResults saved in $output_file"

# Print how many benchmarks failed
total=${#benchmarks[@]}
failed=${#failed_list[@]}
echo -e "\n$((total-failed))/$total benchmarks passed"

# Print failed list
echo -e "\n\e[31mFailed benchmarks:\e[0m"
for failed in "${failed_list[@]}"
do
    echo "  $failed"
done


