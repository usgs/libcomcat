#!/usr/bin/env python

# stdlib imports
import glob
import os.path
import shutil
import subprocess
import sys
import tempfile

# third party imports
import pytest


def get_command_output(cmd):
    """
    Method for calling external system command.

    Args:
        cmd: String command (e.g., 'ls -l', etc.).

    Returns:
        Three-element tuple containing a boolean indicating success or failure,
        the stdout from running the command, and stderr.
    """
    proc = subprocess.Popen(cmd,
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE
                            )
    stdout, stderr = proc.communicate()
    retcode = proc.returncode
    if retcode == 0:
        retcode = True
    else:
        retcode = False
    return (retcode, stdout, stderr)


def test_phases():
    # SMOKE TESTS
    # Check for events without phases products
    try:
        cmd = ('getproduct -s 2012-09-05T13:42:07 -e 2012-09-05T15:42:07 -b'
               ' -86.315 -85.315 9.085 11.085 -m 7 8 pager --get-version first')
        res, stdout, stderr = get_command_output(cmd)
        if not res:
            raise AssertionError(
                'getproduct command %s failed with errors "%s"' % (cmd, stderr))
    except Exception as e:
        raise(e)

    cmp = 'No events found matching your search criteria. Exiting.'
    assert stdout.decode('utf-8').strip(os.linesep) == cmp

    # Check for products
    tmpdir = tempfile.mkdtemp()
    try:
        cmd = ('getproduct shakemap "grid.xml" -d %s -b 163.213 -178.945'
               ' -48.980 -32.324 -s 2013-02-16T04:00:00 -e '
               '2013-02-16T06:00:00' % tmpdir)
        res, stdout, stderr = get_command_output(cmd)
        if not res:
            raise AssertionError(
                'getphases command %s failed with errors "%s"' % (cmd, stderr))
        files = glob.glob(os.path.join(tmpdir, '*'))
    except Exception as e:
        raise(e)
    finally:
        shutil.rmtree(tmpdir)
    assert len(files) == 1
    assert files[0].find('usc000f8cd') != 1

    # Check for products
    tmpdir = tempfile.mkdtemp()
    try:
        cmd = ('getproduct shakemap "grid.xml" -d %s -r -36.514 177.933  5 -s '
               '2013-02-16T04:00:00 -e 2013-02-16T06:00:00' % tmpdir)
        res, stdout, stderr = get_command_output(cmd)
        if not res:
            raise AssertionError(
                'getphases command %s failed with errors "%s"' % (cmd, stderr))
        files = glob.glob(os.path.join(tmpdir, '*'))
    except Exception as e:
        raise(e)
    finally:
        shutil.rmtree(tmpdir)
    assert len(files) == 1
    assert files[0].find('usc000f8cd') != 1


@pytest.mark.skipif(sys.platform == 'win32', reason="proj related functionality broken.")
def test_country():
    # Check for two
    tmpdir = tempfile.mkdtemp()
    try:
        cmd = ('getproduct shakemap "grid.xml" -d %s -r -36.514 177.933  5 -s '
               '2013-02-16T04:00:00 -e 2013-02-16T06:00:00 --country abc' % tmpdir)
        res, stdout, stderr = get_command_output(cmd)

        cmp = 'Please specify a bounding box, radius, or country code.'
        assert stdout.decode('utf-8').strip(os.linesep) == cmp

    except Exception as e:
        raise(e)
    finally:
        shutil.rmtree(tmpdir)

    # Check for bad code
    tmpdir = tempfile.mkdtemp()
    try:
        cmd = ('getproduct shakemap "grid.xml" -d %s -s '
               '2013-02-16T04:00:00 -e 2013-02-16T06:00:00 --country abc' % tmpdir)
        res, stdout, stderr = get_command_output(cmd)

        cmp = ('abc is not a valid ISO 3166 country code. '
               'See https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2 '
               'for the list.')
        assert stdout.decode('utf-8').strip(os.linesep) == cmp
    except Exception as e:
        raise(e)
    finally:
        shutil.rmtree(tmpdir)

    # Check for good code
    tmpdir = tempfile.mkdtemp()
    try:
        cmd = ('getproduct shakemap -d %s -s 2016-10-21T04:07:22 -e '
               '2016-10-21T06:07:22 --country JPN' % tmpdir)
        res, stdout, stderr = get_command_output(cmd)
        files = glob.glob(os.path.join(tmpdir, '*'))
    except Exception as e:
        raise(e)
    finally:
        shutil.rmtree(tmpdir)
    assert len(files) == 1
    assert files[0].find('us20007fta') != 1

    # Check for good code
    tmpdir = tempfile.mkdtemp()
    try:
        cmd = ('getproduct shakemap -d %s --country JPN' % tmpdir)
        res, stdout, stderr = get_command_output(cmd)
    except Exception as e:
        raise(e)
    finally:
        shutil.rmtree(tmpdir)


def test_scenario():
    tmpdir = tempfile.mkdtemp()
    try:
        fmt = ('getproduct shakemap-scenario cont_mi.json -i '
               'nclegacybartlettspringsm7p3_se -d %s --scenario')
        cmd = (fmt % tmpdir)
        res, stdout, stderr = get_command_output(cmd)
        if not res:
            raise AssertionError(
                'getproduct command %s failed with errors "%s"' % (cmd, stderr))
        outfile = stderr.split()[-1]
        if not os.path.isfile(outfile):
            fmt = ('getproduct command %s failed to create '
                   'output file - error stream "%s"')
            raise AssertionError(fmt % (cmd, stderr))
    except Exception as e:
        raise(e)
    finally:
        shutil.rmtree(tmpdir)


if __name__ == '__main__':
    test_scenario()
    test_phases()
