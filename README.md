# hotspot

Performance report generator for OpenMP programs in GNU/Linux.

## Installation

The reports are generated using Latex.
System performance is measured using HPCC.
Program performance is measured using gprof and perf.
A toolchain is used to build the program for optimization or profiling.

### Ubuntu 14.04.2 LTS

```
$ sudo apt-get install texlive texlive-lang-spanish openmpi-bin hpcc gcc gfortran build-essential git python-pip libpng3 libfreetype6 python-matplotlib python-numpy python-dateutil python-scipy ispell htop emacs ipython sysstat texlive-latex-extra linux-tools-generic python graphviz firefox mupdf dwarves linux-tools-3.13.0-32 -y
$ sudo pip install hotspot
```

Note: perf needs a kernel specific package named linux-tools-*
Note: if PDF viewer SIGFAULTS, use mupdf as alternative.

## Configuration

A configuration file is used to configure how to build and run the program.
An anotated sample configuration file can be used as starting point.

```
$ vim hotspot.cfg
```

## Usage

A command line utility is used to run a set of program executions under different conditions to extrapolate performance information.

```
$ hotspot --help
usage: hotspot [-h] [-v] [--config CONFIG] [--debug]

Generate performance report for OpenMP programs.

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  --config CONFIG, -c CONFIG
                        path to configuration
  --debug, -d           enable verbose logging

Check https://github.com/moreandres/hotspot for details.
$ hotspot
```

### Examples

Built-in samples are available with well-known compute kernels.

```
$ hotspot matrix
$ hotspot heat2d
$ hotspot mandel
```

### Configuration File

```
# hotspot configuration file

[hotspot]

# python format method is used to pass parameters

# range is a seq-like definition for problem size
range=1024,2048,256

# cflags are the compiler flags to use when building
cflags=-O3 -Wall -Wextra

# build is the command used to build the program
build=CFLAGS='{0}' make

# clean is the cleanup command to execute
clean=make clean

# run is the program execution command
run=OMP_NUM_THREADS={0} N={1} ./{2}

# count is the number of runs to check workload stabilization
count=16
```
