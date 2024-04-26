cd cpython

#./builddir/build/python benchmarks/pyperformance/bm_django_template/run_benchmark.py -t -p 1

# run  every benchmark in benchmarks/pyperformance/dir_name/run_benchmark.py 

# Create failed list
failed_list=()

# Iterate over directories in benchmarks/pyperformance
for dir in benchmarks/pyperformance/*/
do
    # Get the directory name
    dir_name=$(basename $dir)
    echo -e "\e[32m\nRunning benchmark $dir_name\e[0m"
    cmd="./builddir/build/python benchmarks/pyperformance/$dir_name/run_benchmark.py -t -p 1"

    if ! $cmd; then
        echo -e "\e[31mError:\e[0m $dir_name failed"
        failed_list+=($dir_name)
    fi
done

# Print how many benchmarks failed from the total
total=$(ls benchmarks/pyperformance/ -1 | wc -l)
failed=$(echo ${#failed_list[@]})
echo -e "\n\e[32m$((total-failed))/$total benchmarks passed\e[0m"


# Print failed list
echo -e "\n\e[31mFailed benchmarks:\e[0m"
for failed in "${failed_list[@]}"
do
    echo "  $failed"
done
