#! /usr/bin/env python

"""
hotspot - Performance report generator.
"""

# TODO: when used cached information get timing from there

# TODO: properly handle missing Linux tooling

import ConfigParser

import argparse
import datetime
import logging
import math
import matplotlib.pyplot
import multiprocessing
import numpy
import os

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
    def __call__(cls, *args, **kwargs):
        """Return singleton if already there, otherwise create it."""
        if cls not in cls._instances:
            instance = super(Singleton, cls).__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]

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

# TODO: cli option to select log level in console

        # logs are hidden in ~/.hotspot/PROGRAM/TIMESTAMP
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

        fileh = logging.FileHandler(self.logdir + '/full.log')
        fileh.setLevel(logging.DEBUG)
        consoleh = logging.StreamHandler()
        consoleh.setLevel(logging.DEBUG)
        fmt = '%(asctime)s: %(levelname)s: %(message)s'
        formatter = logging.Formatter(fmt, datefmt="%Y%m%d-%H%M%S")

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

# TODO: fix logging in unit tests

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

        self.args = self.parser.parse_args()
        self.config = ConfigParser.ConfigParser()
        path = os.path.abspath(self.args.config)

        if not os.path.exists(path):
            print 'Configuration file not found.'
            raise SystemExit

        # TODO: use $CWD/hotspot.cfg, create it if not there?

        self.config.read(path)
        return self

    def get(self, key, section='default'):
        """Get configuration attribute."""
        value = self.config.get(section, key)
        Log().debug('Getting {0} from config: {1}'.format(key, value))
        return value

    def items(self, section='default'):
        """Get tags as a dictionary."""
        Log().debug('Getting all items from config')

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
        self.log = Log()
        self.log.debug('Creating section named {0}'.format(self.name))
    def command(self, cmd):
        """Run command keeping logs and caching output."""

        # keep count to cache multiple executions of the same command
        try:
            self.counter[cmd] += 1
        except KeyError:
            self.counter[cmd] = 0

        suffix = '/../{0}.{1}.cache'.format(self.name, self.counter[cmd])
        temp = os.path.abspath(self.log.logdir + suffix)
        output = None

        try:
            output = pickle.load(open(temp, "rb"))
            self.log.debug('Loading ' + temp)
        except IOError:
            self.log.debug('Dumping ' + temp)
            output = subprocess.check_output(cmd, shell = True, stderr=subprocess.STDOUT)
            output.strip()
            pickle.dump(output, open(temp, "wb"))

        with open(self.log.logdir + '/' + self.name + '.log', 'w') as log:
            log.write(output)

        self.output = output

        return self

    def gather(self):
        """Populate section contents."""
        self.log.debug('Empty gather in section named {0}'.format(self.name))
        return self
    def get(self):
        """Return tags."""
        msg = 'Returning tags from section named {0}'
        self.log.debug(msg.format(self.name))
        return self.tags
    def chart(self):
        """Generate chart."""
        return self
    def show(self):
        """Show section name and tags in console."""
        self.log.debug('Showing section named {0}'.format(self.name))
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

        listing = 'sudo lshw -short -sanitize | cut -b25- | '
        grep = 'grep -E "memory|processor|bridge|network|storage"'
        self.tags['hardware'] = self.command(listing + grep).output

        return self

class ProgramSection(Section):
    """Gather program information."""
    def __init__(self):
        """Create program section."""
        Section.__init__(self, 'program')
        self.log = Log()
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

        compiler = 'gcc --version'
        self.tags['compiler'] = re.split('\n', self.command(compiler).output)[0]

        libc = '/lib/x86_64-linux-gnu/libc.so.6'
        self.tags['libc'] = re.split('\n', self.command(libc).output)[0]

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
        test = ' && '.join([ self.dir,
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
        cores = str(multiprocessing.cpu_count())
        mpirun = 'mpirun -np {0} `which hpcc` && cat hpccoutf.txt'
        output = self.command(mpirun.format(cores)).output

        metrics = [ ('success', r'Success=(\d+.*)', None),
                    ('hpl', r'HPL_Tflops=(\d+.*)', 'TFlops'),
                    ('dgemm', r'StarDGEMM_Gflops=(\d+.*)', 'GFlops'),
                    ('ptrans', r'PTRANS_GBs=(\d+.*)', 'GBs'),
                    ('random', r'StarRandomAccess_GUPs=(\d+.*)', 'GUPs'),
                    ('stream', r'StarSTREAM_Triad=(\d+.*)', 'MBs'),
                    ('fft', r'StarFFT_Gflops=(\d+.*)', 'GFlops'), ]

        for metric in metrics:
            if metric:
                try:
                    match = re.search(metric[1], output).group(1)
                except AttributeError:
                    match = 'Unknown'

        if metric:
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

        # TODO: compile before running

        outputs = []
        times = []
        for i in range(0, int(self.count)):
            start = time.time()
            cmd = ' && '.join([ 'cd {0}'.format(self.dir),
                                self.run.format(self.cores,
                                                self.first,
                                                self.program),
                                'cd -' ])

            output = self.command(cmd)

            end = time.time()
            elapsed = end - start
            times.append(elapsed)
            outputs.append(output)
            msg = "Control {0} took {1:.2f} seconds"
            self.log.debug(msg.format(i, elapsed))

        array = numpy.array(times)
        deviation = "Deviation: gmean {0:.2f} std {1:.2f}"
        gmean = scipy.stats.gmean(array)
        std = numpy.std(array)
        self.log.debug(deviation.format(gmean, std))

        self.tags['geomean'] = "%.5f" % gmean
        self.tags['stddev'] = "%.5f" % std

        self.tags['max'] = "%.5f" % numpy.max(array)
        self.tags['min'] = "%.5f" % numpy.min(array)

        # TODO: refactor chart-related into its own method

        number = math.ceil(math.sqrt(int(self.tags['count'])))

        buckets, bins, patches = matplotlib.pyplot.hist(times,
                                                        bins=number,
                                                        normed=True)
        matplotlib.pyplot.plot(bins, 
                               scipy.stats.norm.pdf(bins,
                                                    loc = numpy.mean(array),
                                                    scale = array.std()),
                               'r--')
        matplotlib.pyplot.xlabel('time in seconds')
        matplotlib.pyplot.ylabel('ocurrences in units')
        matplotlib.pyplot.title('histogram')
        matplotlib.pyplot.grid(True)  
        matplotlib.pyplot.savefig('hist.pdf', bbox_inches=0)
        matplotlib.pyplot.clf()
        Log().debug("Plotted histogram")

        return self

# TODO: detect/report outliers

class ScalingSection(Section):
    """Gather scaling information."""
    def __init__(self):
        """Create scaling section.."""
        # TODO: first, last, increment should be read from self.tags
        Section.__init__(self, 'scaling')

        self.tags = Tags().tags
        self.first = self.tags['first']
        self.last = self.tags['last']
        self.increment = self.tags['increment']
        self.run = self.tags['run']
        self.cores = self.tags['cores']
        self.program = self.tags['program']
        self.dir = self.tags['cwd']
        self.cflags = self.tags['cflags']
        self.clean = self.tags['clean']
        self.build = self.tags['build']

    def gather(self):
        """Run program."""

        cleanup = 'cd {0}; {1}; {2}'.format(self.dir,
                                            self.clean,
                                            self.build.format(self.cflags))
        subprocess.check_output(cleanup, shell = True, stderr=subprocess.STDOUT)

        data = {}
        outputs = []

        for size in range(int(self.first),
                          int(self.last) + 1,
                          int(self.increment)):

# TODO: include timing inside command method

            start = time.time()
            run = self.run.format(self.cores, size, self.program)
            output = self.command(' && '.join([ 'cd {0}'.format(self.dir),
                                                run, 'cd -' ]))
            end = time.time()
            outputs.append(output)
            elapsed = end - start
            data[size] = elapsed
            msg = "Problem at {0} took {1:.2f} seconds"
            self.log.debug(msg.format(size, elapsed))

# TODO: kill execution if time takes more than a limit

        xvalues = data.keys()
        xvalues.sort()

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
            start = time.time()
            run = self.tags['run'].format(core,
                                          self.tags['last'],
                                          self.tags['program'])
            output = subprocess.check_output(run, shell = True, stderr=subprocess.STDOUT)
            end = time.time()
            outputs.append(output)
            elapsed = end - start
            procs.append(elapsed)
            message = "Threads at {0} took {1:.2f} seconds"
            self.log.debug(message.format(core, elapsed))

        # TODO: procs[1] less than half procs[0] then supralinear then FAIL

        parallel = 2 * (procs[0] - procs[1]) / procs[0]
        serial = (procs[0] - 2 * (procs[0] - procs[1])) / procs[0]
        self.tags['serial'] = "%.5f" % serial
        self.tags['parallel'] = "%.5f" % parallel
        
        self.tags['amdalah'] = "%.5f" % ( 1 / (serial + (1/1024) * (1 - serial)) )
        self.tags['gustafson'] = "%.5f" % ( 1024 - (serial * (1024 - 1)) )

        self.log.debug("Computed scaling laws")

        # TODO: move graph-related to its own method

        matplotlib.pyplot.plot(procs, label="actual")
        matplotlib.pyplot.grid(True)  

        ideal = [ procs[0] ]
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
            start = time.time()
            build = self.tags['build'].format('-O{0}'.format(opt))
            run = self.tags['run'].format(self.tags['cores'], self.tags['first'], self.tags['program'])
            command = ' && '.join([ build, run ])
            output = subprocess.check_output(command,
                                             shell = True,
                                             stderr=subprocess.STDOUT)
            end = time.time()
            outputs.append(output)
            elapsed = end - start
            opts.append(elapsed)
            optimizations = "Optimizations at {0} took {1:.2f} seconds"
            self.log.debug(optimizations.format(opt, elapsed))

        # TODO: refactor graph-related to its own method

        matplotlib.pyplot.plot(opts)
        matplotlib.pyplot.savefig('opts.pdf', bbox_inches=0)
        matplotlib.pyplot.clf()
        self.log.debug("Plotted optimizations")

class ProfileSection(Section):
    """Gather performance profile information."""
    def __init__(self):
        """Create profile section."""
        Section.__init__(self, 'profile')
    def gather(self):
        """Run gprof and gather results."""

        gprofgrep = 'gprof -l -b {0} | grep [a-zA-Z0-9]'
        command = ' && '.join([ self.tags['build'].format('"-O3 -g -pg"'),
                                self.tags['run'].format(self.tags['cores'],
                                                        self.tags['first'],
                                                        self.tags['program']),
                                gprofgrep.format(self.tags['program']) ])
        output = subprocess.check_output(command, shell = True,
                                         stderr=subprocess.STDOUT)

        self.tags['profile'] = output
        self.log.debug("Profiling report completed")

class ResourcesSection(Section):
    """Gather system resources information."""
    def __init__(self):
        """Create resources section."""
        Section.__init__(self, 'resources')
    def gather(self):
        """Run program under pidstat."""

        cmd = 'pidstat -s -r -d -u -h -p $! 1'
        pidstat = '& {0} | sed "s| \+|,|g" | grep ^, | cut -b2-'.format(cmd)
        command = self.tags['run'].format(self.tags['cores'], self.tags['last'], self.tags['program']) + pidstat
        output = self.command(command).output

# TODO: refactor this into resources section

        lines = output.splitlines()

# TODO: this should be parsed from output's header, not hardcoded

        header = 'Time,PID,%usr,%system,%guest,%CPU,CPU,minflt/s,majflt/s,VSZ,RSS,%MEM,StkSize,StkRef,kB_rd/s,kB_wr/s,kB_ccwr/s,Command'
        fields = header.split(',')

        data = {}
        for i in range(0, len(fields)):
            field = fields[i]
            if field in ['%CPU', '%MEM']:

            # TODO: add disk read/writes plots

                data[field] = []
                for line in lines:
                    data[field].append(line.split(',')[i])

                    matplotlib.pyplot.plot(data[field])
                    matplotlib.pyplot.xlabel('{0} usage rate'.format(field))
                    matplotlib.pyplot.grid(True)
                    label = 'percentage of available resources'
                    matplotlib.pyplot.ylabel(label)
                    matplotlib.pyplot.title('resource usage')
                    name = '{0}.pdf'.format(field, bbox_inches=0)
                    name.replace('%','')
                    matplotlib.pyplot.savefig(name)
                    matplotlib.pyplot.clf()

        self.tags['resources'] = output
        self.log.debug("Resource usage plotting completed")

        return self

class AnnotatedSection(Section):
    """Generate annotated source code."""
    def __init__(self):
        """Create annotated section."""
        Section.__init__(self, 'annotated')
    def gather(self):
        """Run perf to record execution and then generate annotated source code."""
        environment = self.tags['run'].format(self.tags['cores'], self.tags['first'], self.tags['program']).split('./')[0]
        record = 'perf record ./{0}'.format(self.tags['program'])

# TODO: use a throw-away mktemp file

        annotate = 'perf annotate > /tmp/test'
        command = ' && '.join([ self.tags['build'].format('"-O3 -g"'),
                                environment + record,
                                annotate ])
        output = subprocess.check_output(command, shell = True, stderr=subprocess.STDOUT)
        cattest = 'cat /tmp/test | grep -v "^\s*:\s*$" | grep -v "0.00"'
        output = subprocess.check_output(cattest, shell = True, stderr=subprocess.STDOUT)

        self.tags['annotation'] = output
        self.log.debug("Source annotation completed")

class VectorizationSection(Section):
    """Gather vectorization information."""
    def __init__(self):
        """Create vectorization section."""
        Section.__init__(self, 'vectorization')
    def gather(self):
        """Run oprofile."""
        flags = '"-O3 -ftree-vectorizer-verbose=7" 2>&1'
        command = self.tags['build'].format(flags)
        output = subprocess.check_output(command, shell = True,
                                         stderr=subprocess.STDOUT)
        self.tags['vectorizer'] = output
        self.log.debug("Vectorization report completed")

class CountersSection(Section):
    """Gather hardware counters information."""
    def __init__(self):
        """Create hardware counters section."""
        Section.__init__(self, 'counters')
    def gather(self):
        """Run program and gather counter statistics."""

        counters = 'N={0} perf stat -r 3 ./{1}'.format(self.tags['last'], self.tags['program'])
        output = subprocess.check_output(counters, shell = True, stderr=subprocess.STDOUT)
        self.tags['counters'] = output

        self.log.debug("Hardware counters gathering completed")

        return self

class ConfigSection(Section):
    """Gather configuration information."""
    def __init__(self):
        """Create configuration section."""
        Section.__init__(self, 'config')
    def gather(self):
        """Load configuration and update tags."""
        return self

def main():
    """Gather information into tags, replace on a .tex file and compile."""

    Config().load()

    cfg = Config()
    log = Log()
    tags = Tags().tags

    tags.update(Config().items())

    # TODO: write down default logic

    tags['count'] = cfg.get('count')
    tags['build'] = cfg.get('build')
    tags['run'] = cfg.get('run')
    
    tags['first'], tags['last'], tags['increment'] = cfg.get('range').split(',')
    tags['range'] = str(range(int(tags['first']), int(tags['last']), int(tags['increment'])))
    tags['cores'] = str(multiprocessing.cpu_count())

    tags.update(HardwareSection().gather().show().get())

# TODO: check if baseline results are valid
# TODO: choose size to fit in 1 minute
# TODO: cli option to not do any smart thing like choosing problem size

    tags.update(ProgramSection().gather().show().get())
    tags.update(SoftwareSection().gather().show().get())
    tags.update(SanitySection().gather().show().get())

    tags.update(ResourcesSection().gather().show().get())

# TODO: program should be read from a tag

# TODO: get/log human readable output, then process using Python

    tags.update(BenchmarkSection().gather().show().get())
    tags.update(WorkloadSection().gather().show().get())
    tags.update(ScalingSection().gather().show().get())

# TODO: historical comparison?

# TODO: get .tex file from install path

    path = __file__ + '/../../cfg/hotspot.tex'
    filename = os.path.abspath(path)

    template = open(filename, 'r').read()
    for key, value in sorted(tags.iteritems()):
        log.debug("Replacing macro {0} with {1}".format(key, value))
        template = template.replace('@@' + key.upper() + '@@',
                                    value.replace('%', '?'))
    open(tags['program'] + '.tex', 'w').write(template)

    latex = 'pdflatex {0}.tex && pdflatex {0}.tex && pdflatex {0}.tex'
    command = latex.format(tags['program'])
    subprocess.call(command, shell = True)

if __name__ == "__main__":
    main()
