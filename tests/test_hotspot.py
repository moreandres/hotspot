import random
import unittest
import hotspot.hotspot as hotspot
import subprocess
import os

dirname = os.path.dirname(__file__)
program = os.path.realpath(dirname + '/../hotspot/hotspot.py')

class TestHotspot(unittest.TestCase):
    """Test hotspot program."""
    def test_help(self):
        """Check that --help works."""
        output = subprocess.check_output('{0} --help'.format(program),
                                         shell=True,
                                         stderr=subprocess.STDOUT)
        assert 'usage' in output, output
    def test_version(self):
        """Check that --version works."""
        output = subprocess.check_output('{0} --version'.format(program),
                                         shell=True,
                                         stderr=subprocess.STDOUT)
        assert '0.0.1' in output, output
    def test_default(self):
        """Check that default run works."""
        output = subprocess.check_output('{0}'.format(program),
                                         shell=True,
                                         stderr=subprocess.STDOUT)
        assert False, output

if __name__ == '__main__':
    unittest.main()
