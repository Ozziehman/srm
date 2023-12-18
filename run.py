import os
import subprocess

def install_and_run():
    try:
        # Change the current working directory to the directory of this script
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

        subprocess.run(["pip", "install", "pip"])
        subprocess.run(["pip", "install", "-r", "requirements.txt"])
        subprocess.Popen(["flask", "run"])
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    install_and_run()
    input("Press Enter to continue...")