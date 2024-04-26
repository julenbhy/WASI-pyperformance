import threading

def print_hello():
    print("Hello, World!")

if __name__ == "__main__":
    # Create a new thread
    t = threading.Thread(target=print_hello)
    # Start the thread
    t.start()
    # Wait for the thread to finish
    t.join()
