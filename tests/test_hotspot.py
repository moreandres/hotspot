import random
import unittest
import hotspot.hotspot as hotspot
import subprocess
import os

class TestLogger(unittest.TestCase):
    def test_init(self):
        pass
    def test_close(self):
        pass
    def test_get(self):
        pass

class TestConfigurationParser(unittest.TestCase):
    def test_init(self):
        pass
    def test_load(self):
        pass
    def test_get(self):
        pass

class TestSection(unittest.TestCase):
    def test_init(self):
        """Test how TestSection initialize."""
        hotspot.Tags().tags = {}
        assert hotspot.Section('name'), 'could not init Section without tags'
        hotspot.Tags().tags = { 'key0': 'value0', 'key1': 'value1'}
        assert hotspot.Section('name'), 'could not init Section with tags'
        
    def test_gather(self):
        hotspot.Tags().tags = {}
        assert hotspot.Section('name').gather(), 'could not gather Section'

    def test_get(self):
        hotspot.Tags().tags = { 'key0': 'value0', 'key1': 'value1'}
        assert hotspot.Section('name').get()['key0'] == 'value0', 'could not get Section tags'

    def test_show(self):
        hotspot.Tags().tags = { 'key0': 'value0', 'key1': 'value1'}
        assert hotspot.Section('name').show(), 'could not show Section'

class TestHardwareSection(unittest.TestCase):
    def test_init(self):
        assert hotspot.HardwareSection(), 'could not init HardwareSection'
    def test_gather(self):
        assert hotspot.HardwareSection().gather(), 'could not gather HardwareSection'
    def test_get(self):
        assert hotspot.HardwareSection().gather().get()['hardware'], 'could not get HardwareSection'

class TestProgramSection(unittest.TestCase):
    def test_init(self):
        assert hotspot.ProgramSection(), 'could not init ProgramSection'
    def test_gather(self):
        assert hotspot.ProgramSection().gather(), 'could not gather ProgramSection'
    def test_get(self):
        assert hotspot.ProgramSection().gather().get()['timestamp'], 'could not get ProgramSection'

class TestSoftwareSection(unittest.TestCase):
    def test_init(self):
        assert hotspot.SoftwareSection(), 'could not init SoftwareSection'
    def test_gather(self):
        assert hotspot.SoftwareSection().gather(), 'could not gather SoftwareSection'
    def test_get(self):
        assert hotspot.SoftwareSection().gather().get()['compiler'], 'could not get SoftwareSection'

class TestSanitySection(unittest.TestCase):
    def test_init(self):
        hotspot.Tags().tags = {
            'first': '512',
            'last': '1024',
            'increment': '64',
            'run': 'OMP_NUM_THREADS={0} N={1} ./{2}',
            'cores': '2',
            'size': '512',
            'program': 'matrix',
            'dir': 'tests/examples',
            'clean': 'make clean',
            'build': 'CFLAGS="{0}" make',
            'cflags': '-Wall -Wextra',
            }
        
        section = hotspot.SanitySection()
        assert section, 'could not init SanitySection'
        assert section.gather(), 'could not gather SanitySection'
        assert section.get(), 'could not get SanitySection'

class TestBenchmarkSection(unittest.TestCase):
    def test_init(self):
        assert hotspot.BenchmarkSection(), 'could not init BenchmarkSection'
    def test_gather(self):
        assert hotspot.BenchmarkSection().gather(), 'could not gather BenchmarkSection'
    def test_get(self):
        assert hotspot.BenchmarkSection().gather().get(), 'could not get BenchmarkSection'

class TestWorkloadSection(unittest.TestCase):
    def test_section(self):
        hotspot.Tags().tags = {
            'first': '512',
            'last': '512',
            'increment': '64',
            'run': 'OMP_NUM_THREADS={0} N={1} ./{2}',
            'cores': '2',
            'size': '512',
            'count': '32',
            'program': 'matrix',
            'dir': 'tests/examples',
            'clean': 'make clean',
            'build': 'CFLAGS="{0}" make',
            'cflags': '-Wall -Wextra',
            }
        section = hotspot.WorkloadSection()
        assert section, 'could not init WorkloadSection'
        assert section.gather(), 'could not init WorkloadSection'
        assert section.get(), 'could not get WorkloadSection'

class TestScalingSection(unittest.TestCase):        
    def test_section(self):
        hotspot.Tags().tags = {
            'first': '512',
            'last': '1024',
            'increment': '64',
            'run': 'OMP_NUM_THREADS={0} N={1} ./{2}',
            'cores': '2',
            'size': '512',
            'program': 'matrix',
            'dir': 'tests/examples',
            'clean': 'make clean',
            'build': 'CFLAGS="{0}" make',
            'cflags': '-Wall -Wextra',
            }
        section = hotspot.ScalingSection()
        assert section, 'could not init ScalingSection'
        assert section.gather(), 'could not gather ScalingSection'
        assert section.get(), 'could not get ScalingSection'

class TestProfileSection(unittest.TestCase):
    def test_init(self):
        assert hotspot.ProfileSection(), 'could not init ProfileSection'
    def test_gather(self):
        assert hotspot.ProfileSection().gather(), 'could not gather ProfileSection'
    def test_get(self):
        assert hotspot.ProfileSection().gather().get(), 'could not get ProfileSection'

class TestResourcesSection(unittest.TestCase):
    def test_init(self):
        assert hotspot.ResourcesSection(), 'could not init ResourcesSection'
    def test_gather(self):
        assert hotspot.ResourcesSection().gather(), 'could not gather ResourcesSection'
    def test_get(self):
        assert hotspot.ResourcesSection().gather().get(), 'could not get ResourcesSection'

class TestVectorizationSection(unittest.TestCase):
    def test_init(self):
        assert hotspot.VectorizationSection(), 'could not init VectorizationSection'
    def test_gather(self):
        assert hotspot.VectorizationSection().gather(), 'could not gather VectorizationSection'
    def test_get(self):
        assert hotspot.VectorizationSection().gather().get(), 'could not get VectorizationSection'

class TestCountersSection(unittest.TestCase):
    def test_init(self):
        assert hotspot.CountersSection(), 'could not init CountersSection'
    def test_gather(self):
        assert hotspot.CountersSection().gather(), 'could not gather CountersSection'
    def test_get(self):
        assert hotspot.CountersSection().gather().get(), 'could not get CountersSection'

class TestScript(unittest.TestCase):
    def test_clean(self):
        assert subprocess.check_output('python setup.py clean', shell=True)
    def test_clean(self):
        assert subprocess.check_output('python setup.py sdist', shell=True)
    def test_install(self):
        assert subprocess.check_output('sudo python setup.py install', shell=True)
    def test_help(self):
        assert subprocess.check_output('sudo python setup.py install; hotspot --help', shell=True)
    def test_version(self):
        assert subprocess.check_output('sudo python setup.py install; hotspot --version', shell=True)

if __name__ == '__main__':
    unittest.main()
