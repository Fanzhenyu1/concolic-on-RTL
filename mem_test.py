import subprocess

def run_in_subprocess():
    result = subprocess.run(
        ["python", "-c", "CDFG_1_1.py"],
        capture_output=True
    )

def main():
    run_in_subprocess()

if __name__ == "__main__":
    main()