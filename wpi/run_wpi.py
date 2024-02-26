'''
This script runs checker-framework on all the benchmarks.
Fill in the correct values for the macros at
the top of the file before executing.
'''
import os
import shutil
import time
import subprocess
import shlex

BENCHMARKS_FOLDER = "../dataset/"
RESULTS_FOLDER = "checkerframework_3.34.0_results_WPI"
COMPILED_CLASSES_FOLDER = "cf_classes"
SRC_FILES = "cf_srcs.txt"
CF_BINARY = "../scripts/tools/checker-framework-3.34.0/checker/bin/javac"
CF_COMMAND = "-processor org.checkerframework.checker.nullness.NullnessChecker -Adetailedmsgtext -AassumePure"
SKIP_COMPLETED = False #skips if the output file is already there.
WPI_TIMEOUT = 6 * 60 * 60 # 6 * 60 minutes

#create the output folder if it doesn't exist
if not os.path.exists(RESULTS_FOLDER):
    os.mkdir(RESULTS_FOLDER)

#Loop through the benchmarks
print("Completed Benchmarks")
i, total = 1, len(os.listdir(BENCHMARKS_FOLDER))
for benchmark in os.listdir(BENCHMARKS_FOLDER):
    print(f"{i} of {total}: {benchmark}")
    if (SKIP_COMPLETED):
        if os.path.exists(f'{RESULTS_FOLDER}/{benchmark}-before-wpi.txt'):
            print("skipping completed benchmark.")
            i += 1
            continue
        else:
            print("running benchmark.")
    #skip non-directories
    if not os.path.isdir(f'{BENCHMARKS_FOLDER}/{benchmark}'):
        continue
    
    #create a folder for the compiled classes if it doesn't exist
    if not os.path.exists(COMPILED_CLASSES_FOLDER):
        os.mkdir(COMPILED_CLASSES_FOLDER)

    #Get a list of Java source code files.
    find_srcs_command = f'find {BENCHMARKS_FOLDER}/{benchmark}/src -name "*.java" > {SRC_FILES}'
    os.system(find_srcs_command)

    #get folder with libraries used by benchmark
    lib_folder = f'{BENCHMARKS_FOLDER}/{benchmark}/lib'

    command = (CF_BINARY
        + " " + CF_COMMAND
        # + " " + "-Aajava=" + BENCHMARKS_FOLDER + "/" + benchmark + "/" + "/wpi-out"
        + " " + "-J-Xmx32G"
        + " " + "-Xmaxerrs 10000"
        + " " + "-d"
        + " " + COMPILED_CLASSES_FOLDER
        + " -cp " + lib_folder
        + " @" + SRC_FILES
        + " 2> " +  RESULTS_FOLDER
        + "/" + benchmark + "-before-wpi.txt"
    )
    os.system(command)

    #execute infer on the source files
    time_start = time.time()
    # Run WPI.
    print(f"Running WPI on {benchmark}")
    with open(f'{BENCHMARKS_FOLDER}/{benchmark}/wpi-log.txt', 'w') as file:
        process = subprocess.Popen(shlex.split(f'./wpi/wpi.sh {BENCHMARKS_FOLDER}/{benchmark}'), stdout=file, stderr=subprocess.STDOUT)
        try:
            process.communicate(timeout=WPI_TIMEOUT)
        except subprocess.TimeoutExpired:
            print(f"Command timed out after {WPI_TIMEOUT} seconds")
            process.kill()
            process.wait()
            os.system("killall -9 java")
    
    command = (CF_BINARY
        + " " + CF_COMMAND
        + " " + "-Aajava=" + BENCHMARKS_FOLDER + "/" + benchmark + "/" + "/wpi-out"
        + " " + "-J-Xmx32G"
        + " " + "-Xmaxerrs 10000"
        + " " + "-d"
        + " " + COMPILED_CLASSES_FOLDER
        + " -cp " + lib_folder
        + " @" + SRC_FILES
        + " 2> " +  RESULTS_FOLDER
        + "/" + benchmark + "-after-wpi.txt"
    )
    os.system(command)
    time_end = time.time()
    total_time = time_end - time_start
    with open("checkerframework_timings.csv","a") as f:
        f.write(f'{benchmark},{str(total_time)}\n')
    
    #remove the classes folder
    shutil.rmtree(COMPILED_CLASSES_FOLDER)
    print("-------------------------------------------------- \n")
    i += 1
    exit()