# hotspot

Performance report generator for OpenMP programs in GNU/Linux.

## Installation

The reports are generated using Latex.
System performance is measured using HPCC.
Program performance is measured using gprof and perf.
A toolchain is used to build the program for optimization or profiling.

### Ubuntu

```
$ sudo apt-get install texlive openmpi-bin linux-tools hpcc gcc gfortran build-essential git python-pip libpng3 libfreetype6 python-matplotlib python-numpy python-dateutil python-scipy ispell htop emacs sysstat texlive-latex-extra
$ sudo pip install hotspot
```

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
