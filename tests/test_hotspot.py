import unittest
import subprocess
import os

"""
test_hotspot.py - Test performance report generator.
"""

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
    def test_matrix(self):
        """Check that matrix example works."""
        command = 'cd {0}/examples/matrix; {1} --config hotspot.cfg'.format(dirname, program)
        output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        assert 'Output written' in output
    def test_mandel(self):
        """Check that mandel example works."""
        command = 'cd {0}/examples/mendel; {1} --config hotspot.cfg'.format(dirname, program)
        output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        assert 'Output written' in output
    def test_heat2d(self):
        """Check that heat2d example works."""
        command = 'cd {0}/examples/heat2d; {1} --config hotspot.cfg'.format(dirname, program)
        output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        assert 'Output written' in output

if __name__ == '__main__':
    unittest.main()
