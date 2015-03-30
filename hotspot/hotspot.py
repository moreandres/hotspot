#! /usr/bin/env python

"""
hotspot - Performance report generator.
"""

# TODO: replace all hotspot with filename

import ConfigParser

import argparse
import datetime
import logging
import math
import matplotlib.pyplot
import multiprocessing
import numpy
import os
# import sys

try:
    import cPickle as pickle
except ImportError:
    import pickle

import platform
import re
import scipy.stats
import socket
import subprocess
import time

class Singleton(type):
    """Singleton metaclass."""
    _instances = {}
    def __call__(mcs, *args, **kwargs):
        """Return singleton if exists, otherwise create it."""
        if mcs not in mcs._instances:
            instance = super(Singleton, mcs).__call__(*args, **kwargs)
            mcs._instances[mcs] = instance
        return mcs._instances[mcs]

class Tags:
    """Tags to be replaced at the report."""
    __metaclass__ = Singleton
    def __init__(self):
        """Tags are empty."""
        self.tags = {}
    def clear(self):
        """Clear current tags."""
        self.tags = {}
    def show(self):
        """Show current tags."""
        print self.tags

class Log:
    """Logging interface."""
    __metaclass__ = Singleton
    def __init__(self):
        """Store all logs in file, show also in console."""

        cwd = os.path.abspath('.')
        program = os.path.basename(cwd)
        timestamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')

        self.logger = logging.getLogger('hotspot')
        self.timestamp = timestamp
        self.logdir = '{0}/.hotspot/{1}/{2}'.format(os.path.expanduser("~"),
                                                    program,
                                                    self.timestamp)

        if not os.path.exists(self.logdir):
            os.makedirs(self.logdir)

        self.logger.setLevel(logging.DEBUG)

        fileh = logging.FileHandler(self.logdir + '/hotspot.log')
        fileh.setLevel(logging.DEBUG)
        consoleh = logging.StreamHandler()

        self.config = Config()
        consoleh.setLevel(logging.INFO)

        if self.config.args.debug:
            consoleh.setLevel(logging.DEBUG)

        fmt = '%(asctime)s: %(levelname)s: %(message)s'
        formatter = logging.Formatter(fmt,
                                      datefmt="%Y%m%d-%H%M%S")

        fileh.setFormatter(formatter)
        consoleh.setFormatter(formatter)

        self.logger.addHandler(fileh)
        self.logger.addHandler(consoleh)

        self.logger.debug('Logging to {0}'.format(self.logdir))

    def debug(self, message):
        """Print debugging messages."""
        self.logger.debug(message)

    def info(self, message):
        """Print informational messages."""
        self.logger.info(message)

    def error(self, message):
        """Print error messages."""
        self.logger.error(message)

    def close(self):
        """Close logging."""
        return self

    def get(self):
        """Get logger instance."""
        return self.logger

class Config:
    """ Parse configuration."""
    __metaclass__ = Singleton

    def __init__(self):

        """Empty configuration."""
        self.config = None
        self.parser = None
        self.args = None

    def load(self):

        """Load arguments and configuration from file."""
        description = 'Generate performance report for OpenMP programs.'
        epilog = 'Check https://github.com/moreandres/hotspot/ for details.'
        self.parser = argparse.ArgumentParser(description=description,
                                              epilog=epilog,
                                              version='0.0.1')

        # TODO: use action to verify that configuration file exists

        realpath = os.path.dirname(os.path.realpath(__file__))
        configpath = realpath + '/../cfg/hotspot.cfg'

        self.parser.add_argument('--config', '-c',
                                 help='path to configuration',
                                 default=configpath)
        self.parser.add_argument('--debug', '-d',
                                 action='store_true',
                                 help='enable verbose logging')
        self.parser.add_argument('--force', '-f',
                                 action='store_true',
                                 help='do not reuse cache')

        self.args = self.parser.parse_args()
        self.config = ConfigParser.ConfigParser()
        path = os.path.abspath(self.args.config)

        if not os.path.exists(path):
            print 'Configuration file not found.'
            raise SystemExit

        self.config.read(path)
        return self

    def get(self, key, section='hotspot'):
        """Get configuration attribute."""
        value = self.config.get(section, key)
        return value

    def items(self, section='hotspot'):
        """Get tags as a dictionary."""

        items = {}
        for option in self.config.options(section):
            items[option] = self.config.get(section, option)

        return items

class Section:
    """Report section."""
    def __init__(self, name):
        """Store section name, config and tags."""
        self.name = name
        self.tags = Tags().tags
        self.config = Config()
        self.counter = {}
        self.output = None
        self.elapsed = -1
        self.log = Log()
        self.log.info('Creating {0} section'.format(self.name))
    def command(self, cmd):
        """Run command keeping logs and caching output."""

        try:
            self.counter[self.name] += 1
        except KeyError:
            self.counter[self.name] = 0

        output = None
        elapsed = -1

        output_suffix = '/../{0}.{1}.output'.format(self.name,
                                                    self.counter[self.name])
        elapsed_suffix = '/../{0}.{1}.elapsed'.format(self.name,
                                                      self.counter[self.name])

        output_file = os.path.abspath(self.log.logdir + output_suffix)
        elapsed_file = os.path.abspath(self.log.logdir + elapsed_suffix)

        try:
            if self.config.args.force:
                raise IOError
            output = pickle.load(open(output_file, "rb"))
            elapsed = pickle.load(open(elapsed_file, "rb"))
            self.log.debug('Loading ' + output_file)
        except IOError:
            self.log.debug('Dumping ' + output_file)
            start = time.time()
            output = subprocess.check_output(cmd,
                                             shell=True,
                                             stderr=subprocess.STDOUT)
            elapsed = time.time() - start
            output.strip()
            pickle.dump(output, open(output_file, "wb"))
            pickle.dump(elapsed, open(elapsed_file, "wb"))

        self.output = output
        self.elapsed = elapsed

        self.log.debug('Run {0} for {1} in {2}'.format(cmd, output, elapsed))

        return self

    def gather(self):
        """Populate section contents."""
        self.error.debug('Empty gather in {0} section'.format(self.name))
        return self
    def get(self):
        """Return tags."""
        msg = 'Returning tags from {0} section'
        self.log.debug(msg.format(self.name))
        return self.tags
    def chart(self):
        """Generate chart."""
        return self
    def show(self):
        """Show section name and tags in console."""
        self.log.debug('Showing {0} section'.format(self.name))
        for key, value in sorted(self.tags.iteritems()):
            self.log.debug('Tag {0} is {1}'.format(key, value))
        return self

class HardwareSection(Section):
    """Gather hardware information."""
    def __init__(self):
        """Create hardware section."""
        Section.__init__(self, 'hardware')
    def gather(self):
        """Gather hardware information."""

        listing = 'which lshw >/dev/null && lshw -short -sanitize 2>/dev/null | cut -b25- | '
        items = 'memory|processor|bridge|network|storage'
        grep = 'grep -E "{0}" | grep -v "^storage\s*$"'.format(items)
        self.tags['hardware'] = self.command(listing + grep).output
        self.tags['cores'] = str(multiprocessing.cpu_count())

        return self

class ProgramSection(Section):
    """Gather program information."""
    def __init__(self):
        """Create program section."""
        Section.__init__(self, 'program')
    def gather(self):
        """Gather program information."""
        self.tags['timestamp'] = self.log.timestamp
        self.tags['log'] = self.log.logdir
        self.tags['host'] = socket.getfqdn()
        self.tags['distro'] = ', '.join(platform.linux_distribution())
        self.tags['platform'] = platform.platform()
        self.tags['cwd'] = os.path.abspath('.')
        self.tags['program'] = os.path.basename(self.tags['cwd'])

        return self

class SoftwareSection(Section):
    """Gather software information."""
    def __init__(self):
        """Create program section."""
        Section.__init__(self, 'software')
    def gather(self):
        """Get compiler and C library version."""

        compiler = 'which gcc >/dev/null && gcc --version'
        self.tags['compiler'] = re.split('\n', self.command(compiler).output)[0]

        libc = '/lib/x86_64-linux-gnu/libc.so.6'
        version = re.split('\n', self.command(libc).output)[0]
        self.tags['libc'] = re.split(',', version)[0]

        return self

class SanitySection(Section):
    """Gather sanity information."""
    def __init__(self):
        """Create sanity section."""
        Section.__init__(self, 'sanity')
        self.dir = 'cd {0}'.format(self.tags['cwd'])
        self.build = self.tags['build'].format('-O3')
        self.run = self.tags['run']
        self.cores = self.tags['cores']
        self.first = self.tags['first']
        self.program = self.tags['program']
    def gather(self):
        """Build and run the program using a small input size."""
        test = ' && '.join([self.dir,
                            self.build,
                            self.run.format(self.cores,
                                            self.first,
                                            self.program),
                             'cd -'])
        self.command(test)
        return self

class BenchmarkSection(Section):
    """Gather benchmark information."""
    def __init__(self):
        """Create benchmark section."""
        Section.__init__(self, 'benchmark')
    def gather(self):
        """Run HPCC and gather metrics."""
        # TBD: make this a tag

        mpirun = 'which mpirun >/dev/null && which hpcc >/dev/null && mpirun -np {0} `which hpcc` && cat hpccoutf.txt'
        output = self.command(mpirun.format(self.tags['cores'])).output

        metrics = [('success', r'Success=(\d+.*)', None),
                   ('hpl', r'HPL_Tflops=(\d+.*)', 'TFlops'),
                   ('dgemm', r'StarDGEMM_Gflops=(\d+.*)', 'GFlops'),
                   ('ptrans', r'PTRANS_GBs=(\d+.*)', 'GBs'),
                   ('random', r'StarRandomAccess_GUPs=(\d+.*)', 'GUPs'),
                   ('stream', r'StarSTREAM_Triad=(\d+.*)', 'MBs'),
                   ('fft', r'StarFFT_Gflops=(\d+.*)', 'GFlops'), ]

        for metric in metrics:
            try:
                match = re.search(metric[1], output).group(1)
            except AttributeError:
                match = 'Unknown'

            value = '{0} {1}'.format(match, metric[2])
            self.tags['hpcc-{0}'.format(metric[0])] = value

        self.log.debug("System baseline completed")

        return self

class WorkloadSection(Section):
    """Gather workload information."""
    def __init__(self):
        """Create workload section."""
        Section.__init__(self, 'workload')

        self.count = self.tags['count']
        self.run = self.tags['run']
        self.cores = self.tags['cores']
        self.first = self.tags['first']
        self.program = self.tags['program']
        self.dir = self.tags['cwd']

    def gather(self):
        """Run program multiple times, check geomean and deviation."""

        # TODO: clean/compile before running

        outputs = []
        times = []
        for i in range(0, int(self.count)):
            cmd = ' && '.join(['cd {0}'.format(self.dir),
                               self.run.format(self.cores,
                                               self.first,
                                               self.program),
                               'cd -'])

            command = self.command(cmd)
            output = command.output
            elapsed = command.elapsed

            times.append(elapsed)
            outputs.append(output)
            msg = "Control {0} took {1:.2f} seconds"
            self.log.info(msg.format(i, elapsed))

        array = numpy.array(times)
        deviation = "Deviation: gmean {0:.2f} std {1:.2f}"
        gmean = scipy.stats.gmean(array)
        std = numpy.std(array)
        average = numpy.average(array)
        self.log.info(deviation.format(gmean, std))

        self.tags['geomean'] = "%.5f" % gmean
        self.tags['average'] = "%.5f" % average
        self.tags['stddev'] = "%.5f" % std

        self.tags['max'] = "%.5f" % numpy.max(array)
        self.tags['min'] = "%.5f" % numpy.min(array)

        # TODO: refactor chart-related into its own method

        number = 2 * math.ceil(math.sqrt(int(self.tags['count'])))

        matplotlib.pyplot.gcf().set_size_inches(12, 4)
        buckets, bins, patches = matplotlib.pyplot.hist(times,
                                                        bins=number,
                                                        normed=True)
        matplotlib.pyplot.plot(bins,
                               scipy.stats.norm.pdf(bins,
                                                    loc=numpy.mean(array),
                                                    scale=array.std()),
                               'r--')
        matplotlib.pyplot.xlabel('time in seconds')
        matplotlib.pyplot.ylabel('ocurrences in units')
        matplotlib.pyplot.title('histogram')
        matplotlib.pyplot.grid(True)
        matplotlib.pyplot.savefig('hist.pdf', bbox_inches=0)
        matplotlib.pyplot.clf()
        self.log.debug("Plotted histogram")

        return self

# TODO: detect/report outliers

class ScalingSection(Section):
    """Gather scaling information."""
    def __init__(self):
        """Create scaling section.."""

        Section.__init__(self, 'scaling')
        self.tags = Tags().tags

    def gather(self):
        """Run program."""

        build = self.tags['build'].format(self.tags['cflags'])
        cleanup = 'cd {0}; {1}; {2}'.format(self.tags['cwd'],
                                            self.tags['clean'],
                                            build)
        self.command(cleanup)

        data = {}
        outputs = []

        for size in range(int(self.tags['first']),
                          int(self.tags['last']) + 1,
                          int(self.tags['increment'])):

            run = self.tags['run'].format(self.tags['cores'],
                                          size, self.tags['program'])
            chdir = 'cd {0}'.format(self.tags['cwd'])
            command = self.command(' && '.join([chdir, run, 'cd -']))
            output = command.output
            elapsed = command.elapsed
            outputs.append(output)

            data[size] = elapsed
            msg = "Problem at {0} took {1:.2f} seconds"
            self.log.info(msg.format(size, elapsed))

# TODO: kill execution if time takes more than a limit

        xvalues = data.keys()
        xvalues.sort()

        matplotlib.pyplot.gcf().set_size_inches(12, 4)
        matplotlib.pyplot.plot(data.values())
        matplotlib.pyplot.xlabel('problem size in bytes')
        matplotlib.pyplot.xticks(range(0, len(data.values())), xvalues)
        matplotlib.pyplot.grid(True)

# TODO: add problem size as labels in X axis

        matplotlib.pyplot.ylabel('time in seconds')
        matplotlib.pyplot.title('data size scaling')
        matplotlib.pyplot.savefig('data.pdf', bbox_inches=0)
        matplotlib.pyplot.clf()
        self.log.debug("Plotted problem scaling")

        return self

class ThreadsSection(Section):
    """Gather multi-threading information."""
    def __init__(self):
        """Create multi-threading section."""
        Section.__init__(self, 'threading')
    def gather(self):
        """Run program using increasing thread count."""
        outputs = []
        procs = []
        for core in range(1, int(self.tags['cores']) + 1):

            run = self.tags['run'].format(core,
                                          self.tags['last'],
                                          self.tags['program'])

            command = self.command(run)
            output = command.output
            elapsed = command.elapsed
            outputs.append(output)
            procs.append(elapsed)

            message = "Threads at {0} took {1:.2f} seconds"
            self.log.info(message.format(core, elapsed))

        # TODO: procs[1] less than half procs[0] then supralinear then FAIL

        parallel = 2 * (procs[0] - procs[1]) / procs[0]
        serial = (procs[0] - 2 * (procs[0] - procs[1])) / procs[0]
        self.tags['serial'] = "%.5f" % serial
        self.tags['parallel'] = "%.5f" % parallel

        amdalah = (1 / (serial + (1/1024) * (1 - serial)))
        self.tags['amdalah'] = "%.5f" % amdalah
        gustafson = (1024 - (serial * (1024 - 1)))
        self.tags['gustafson'] = "%.5f" % gustafson

        self.log.debug("Computed scaling laws")

        # TODO: move graph-related to its own method

        matplotlib.pyplot.gcf().set_size_inches(12, 4)
        matplotlib.pyplot.plot(procs, label="actual")
        matplotlib.pyplot.grid(True)

        ideal = [procs[0]]
        for proc in range(1, len(procs)):
            ideal.append(procs[proc]/proc+1)

        matplotlib.pyplot.plot(ideal, label="ideal")

        matplotlib.pyplot.xlabel('cores in units')
        matplotlib.pyplot.xticks(range(0, int(self.tags['cores'])),
                                 range(1, int(self.tags['cores']) + 1))
        matplotlib.pyplot.ylabel('time in seconds')
        matplotlib.pyplot.title('thread count scaling')
        matplotlib.pyplot.savefig('procs.pdf', bbox_inches=0)
        matplotlib.pyplot.grid(True)
        matplotlib.pyplot.clf()
        self.log.debug("Plotted thread scaling")
        return self

class OptimizationSection(Section):
    """Gather optimizations information."""
    def __init__(self):
        """Create optimizations section."""
        Section.__init__(self, 'optimizations')
    def gather(self):
        """Run program with increasing optimization levels."""
        outputs = []
        opts = []
        for opt in range(0, 4):

            # TODO: add configured cflags as a prefix here

            build = self.tags['build'].format('-O{0}'.format(opt))
            cores = self.tags['cores']
            last = self.tags['last']
            program = self.tags['program']
            run = self.tags['run'].format(cores, last, program)
            command = ' && '.join([build, run])

            cmd = self.command(command)
            output = cmd.output
            elapsed = cmd.elapsed
            outputs.append(output)
            opts.append(elapsed)
            optimizations = "Optimizations at {0} took {1:.2f} seconds"
            self.log.info(optimizations.format(opt, elapsed))

        # TODO: refactor graph-related to its own method

        matplotlib.pyplot.xticks(range(0, 4), [0, 1, 2, 3])
        matplotlib.pyplot.bar([0, 1, 2, 3], opts)
        matplotlib.pyplot.ylabel('time in seconds')
        matplotlib.pyplot.xlabel('optimization level')
        matplotlib.pyplot.title('compiler optimizations')
        matplotlib.pyplot.grid(True)
        matplotlib.pyplot.savefig('opts.pdf', bbox_inches=0)
        matplotlib.pyplot.clf()
        self.log.debug("Plotted optimizations")
        return self

class ProfileSection(Section):
    """Gather performance profile information."""
    def __init__(self):
        """Create profile section."""
        Section.__init__(self, 'profile')
    def gather(self):
        """Run gprof and gather results."""

        gprofgrep = 'which gprof >/dev/null && gprof -l -b {0} | grep [a-zA-Z0-9] | grep -v "^\s*0.[0-9]"'

        # TODO: add configured CFLAGS as prefix to this set

        run = self.tags['run'].format(self.tags['cores'],
                                      self.tags['last'],
                                      self.tags['program'])
        command = ' && '.join([self.tags['build'].format('-O3 -g -pg'),
                               run,
                               gprofgrep.format(self.tags['program'])])

        output = re.split('Index by function name',
                          self.command(command).output)[0]

        self.tags['profile'] = output
        self.log.debug("Profiling report completed")
        return self

class ResourcesSection(Section):
    """Gather system resources information."""
    def __init__(self):
        """Create resources section."""
        Section.__init__(self, 'resources')
    def gather(self):
        """Run program under pidstat."""

        cmd = 'which pidstat >/dev/null && pidstat -s -r -d -u -h -p $! 1'
        pidstat = '& {0} | sed "s| \+|,|g" | grep ^, | cut -b2-'.format(cmd)
        cores = self.tags['cores']
        last = self.tags['last']
        program = self.tags['program']
        command = self.tags['run'].format(cores, last, program) + pidstat
        output = self.command(command).output

# TODO: refactor this into resources section

        lines = output.splitlines()

# TODO: this should be parsed from output's header, not hardcoded

        header = """Time,PID,%usr,%system,%guest,%CPU,CPU,minflt/s,
majflt/s,VSZ,RSS,%MEM,StkSize,StkRef,kB_rd/s,kB_wr/s,kB_ccwr/s,Command"""
        fields = header.split(',')

        data = {}
        for i in range(0, len(fields)):
            field = fields[i]
            if field in ['%CPU', '%MEM', 'kB_rd/s', 'kB_wr/s']:

                data[field] = []
                for line in lines:
                    data[field].append(line.split(',')[i])

                matplotlib.pyplot.gcf().set_size_inches(12, 4)
                matplotlib.pyplot.plot(data[field])

                matplotlib.pyplot.xlabel('runtime in seconds'.format(field))
                matplotlib.pyplot.grid(True)
                label = 'percentage of available resources'
                matplotlib.pyplot.ylabel(label)
                matplotlib.pyplot.title('{0} usage'.format(field))
                name = '{0}.pdf'.format(field, bbox_inches=0)
                name = name.replace('%', '').replace('_', '').replace('/', '')
                matplotlib.pyplot.savefig(name)
                matplotlib.pyplot.clf()

        self.tags['resources'] = output
        self.log.debug("Resource usage plotting completed")

        return self

# TODO: use a throw-away mktemp file
# TODO: use long options everywhere

# perf script | gprof2dot.py -f perf | dot -Tpng -o output.png

class AnnotatedSection(Section):
    """Generate annotated source code."""
    def __init__(self):
        """Create annotated section."""
        Section.__init__(self, 'annotated')
    def gather(self):
        """Run perf to record execution and generate annotated source code."""
        environment = self.tags['run'].format(self.tags['cores'],
                                              self.tags['last'],
                                              self.tags['program']).split('./')[0]
        record = 'which perf >/dev/null && echo "{0} perf record -q -- ./{1}" > /tmp/test; bash -i /tmp/test >/dev/null 2>/dev/null'.format(environment, self.tags['program'])
        annotate = "perf annotate --stdio | grep -v '^\s*:\s*$' | grep -v '0.0' | grep -C 5 '\s*[0-9].*:'"

# TODO: use cflags tag here instead of -O3

        command = ' && '.join([self.tags['build'].format('-O3 -g'),
                               record,
                               annotate])

        output = self.command(command).output

        self.tags['annotation'] = output
        self.log.debug("Source annotation completed")
        return self

class VectorizationSection(Section):
    """Gather vectorization information."""
    def __init__(self):
        """Create vectorization section."""
        Section.__init__(self, 'vectorization')
    def gather(self):
        """Run oprofile."""

        # TODO: add configured cflags as a prefix to this set

        flags = '-O3 -ftree-vectorizer-verbose=2'
        command = self.tags['build'].format(flags) + ' 2>&1 | grep -v "^$"'
        output = self.command(command).output
        self.tags['vectorizer'] = output
        self.log.debug("Vectorization report completed")
        return self

class FootprintSection(Section):
    """Gather footprint information."""
    def __init__(self):
        """Create footprint section."""
        Section.__init__(self, 'footprint')
    def gather(self):
        """Get binary size, check if stripped and run pahole."""

        flags = '-O3 -g'
        command = self.tags['clean'] + ' && ' + self.tags['build'].format(flags)
        self.command(command)

        output = self.command('file {0}'.format(self.tags['program'])).output
        self.tags['strip'] = output

        pahole = 'which pahole >/dev/null && pahole {0}'
        output = self.command(pahole.format(self.tags['program'])).output
        self.tags['pahole'] = output

        self.log.debug("Footprint report completed")
        return self

class CountersSection(Section):
    """Gather hardware counters information."""
    def __init__(self):
        """Create hardware counters section."""
        Section.__init__(self, 'counters')
    def gather(self):
        """Run program and gather counter statistics."""

        counters = 'which perf >/dev/null && N={0} perf stat -r 3 ./{1}'.format(self.tags['last'],
                                                                                self.tags['program'])
        output = self.command(counters).output
        self.tags['counters'] = output

        self.log.debug("Hardware counters gathering completed")

        return self

class ConfigSection(Section):
    """Gather configuration information."""
    def __init__(self):
        """Create configuration section."""
        Section.__init__(self, 'config')
        self.log = Log()
        self.config = Config()
        self.tags = Tags()
    def gather(self):
        """Load configuration and update tags."""
        return self

def main():
    """Gather information into tags, replace on a .tex file and compile."""

    start = time.time()

    # sys.tracebacklimit = 0

    Config().load()

    cfg = Config()
    log = Log()
    tags = Tags().tags

    log.info('Starting hotspot')

    tags.update(Config().items())

    # TODO: document write down default logic
    # TODO: document configuration file examples

    # TODO: these tags should be moved to ConfigurationSection

    tags['count'] = cfg.get('count')
    tags['build'] = cfg.get('build')
    tags['run'] = cfg.get('run')

    tags['first'], tags['last'], tags['increment'] = cfg.get('range').split(',')
    tags['range'] = str(range(int(tags['first']), int(tags['last']), int(tags['increment'])))
    tags['cores'] = str(multiprocessing.cpu_count())

    tags.update(HardwareSection().gather().get())

# TODO: check if baseline results are valid
# TODO: choose size to fit in 1 minute
# TODO: cli option to not do any smart thing like choosing problem size
# TODO: get/log human readable output, then process using Python

    tags.update(ProgramSection().gather().get())
    tags.update(SoftwareSection().gather().get())
    tags.update(SanitySection().gather().get())
    tags.update(FootprintSection().gather().get())
    tags.update(BenchmarkSection().gather().get())
    tags.update(WorkloadSection().gather().get())
    tags.update(ScalingSection().gather().get())
    tags.update(ThreadsSection().gather().get())
    tags.update(OptimizationSection().gather().get())
    tags.update(ProfileSection().gather().get())
    tags.update(ResourcesSection().gather().get())
    tags.update(AnnotatedSection().gather().get())
    tags.update(VectorizationSection().gather().get())
    tags.update(CountersSection().gather().show().get())

# TODO: historical comparison?

    log.info('Generating report')

    path = __file__ + '/../../cfg/hotspot.tex'
    filename = os.path.abspath(path)

    template = open(filename, 'r').read()
    for key, value in sorted(tags.iteritems()):
        log.debug("Replacing macro {0} with {1}".format(key, value))
        sanity = value.replace('%', '')
        template = template.replace('@@' + key.upper() + '@@', sanity)

    name = tags['program'] + '-' + log.timestamp + '.tex'
    open(name, 'w').write(template)

    latex = 'pdflatex {0} && pdflatex {0} && pdflatex {0}'
    command = latex.format(name)
    subprocess.check_output(command, shell=True)
    log.info('Completed execution in {0:.2f} seconds'.format(time.time() - start))

if __name__ == "__main__":
    main()
