import multiprocessing

def print_hello():
    print("Hello, World!")

if __name__ == "__main__":
    # Create a new process
    p = multiprocessing.Process(target=print_hello)
    # Start the process
    p.start()
    # Wait for the process to finish
    p.join()
