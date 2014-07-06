# hotspot

Performance report generator for OpenMP programs in GNU/Linux.

## Installation

The reports are generated using Latex.
System performance is measured using HPCC.
Program performance is measured using gprof and perf.
A toolchain is used to build the program for optimization or profiling.

### Ubuntu

```
$ sudo apt-get install texlive openmpi-bin linux-tools hpcc gcc gfortran build-essential git python-pip libpng3 libfreetype6 python-matplotlib python-numpy python-dateutil python-scipy ispell htop emacs sysstat texlive-latex-extra linux-tools-3.11.0-23-generic
$ sudo pip install hotspot
```

Note: The linux-tools-*-generic package should match the available kernel.

Note: Usual Ubuntu default PDF readers SIGFAULTS somehow, use mupdf or Adobe.

$ sudo apt-get install gdebi libgtk2.0-0:i386 libnss3-1d:i386 libnspr4-0d:i386 lib32nss-mdns* libxml2:i386 libxslt1.1:i386 libstdc++6:i386
$ wget http://ardownload.adobe.com/pub/adobe/reader/unix/9.x/9.5.5/enu/AdbeRdr9.5.5-1_i386linux_enu.deb
$ sudo gdebi AdbeRdr9.5.5-1_i386linux_enu.deb
$ acroread

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
