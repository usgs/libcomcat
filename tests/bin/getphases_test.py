#!/usr/bin/env python

# stdlib imports
import glob
import os.path
import re
import subprocess
import shutil
import tempfile

# third party imports
import numpy as np
import pandas as pd


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
    tmpdir = tempfile.mkdtemp()
    try:
        cmd = 'getphases -s 1960-09-03T12:11:00 -e 1960-09-03T13:01:00 %s' % tmpdir
        res, stdout, stderr = get_command_output(cmd)
        if not res:
            raise AssertionError(
                'getphases command %s failed with errors "%s"' % (cmd, stderr))
    except Exception as e:
        raise(e)
    finally:
        shutil.rmtree(tmpdir)

    cmp = 'iscgem880236 has no phase data.'
    assert stdout.decode('utf-8').strip(os.linesep) == cmp

    # Check for no products
    tmpdir = tempfile.mkdtemp()
    try:
        cmd = 'getphases -s 1900-09-03T12:11:00 -e 1900-09-03T13:01:00 %s' % tmpdir
        res, stdout, stderr = get_command_output(cmd)
        if not res:
            raise AssertionError(
                'getphases command %s failed with errors "%s"' % (cmd, stderr))
    except Exception as e:
        raise(e)
    finally:
        shutil.rmtree(tmpdir)

    cmp = 'No events found matching your search criteria. Exiting.'
    assert stdout.decode('utf-8').strip(os.linesep) == cmp

    # Check product
    tmpdir = tempfile.mkdtemp()
    try:
        cmd = ('getphases -s 2012-09-05T13:42:07 -e 2012-09-05T15:42:07 -b '
               '-86.315 -85.315 9.085 11.085  -t 2012-09-06 -m 7 8 %s' % tmpdir)
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
    assert files[0].find('usp000jrsw') != -1

    # Check product
    tmpdir = tempfile.mkdtemp()
    try:
        cmd = ('getphases -s 2012-09-05T13:42:07 -e 2012-09-05T15:42:07 -b '
               '-86.315 -85.315 9.085 11.085  -t 2012-09-06 -m 7 8 -f excel %s' % tmpdir)
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
    assert files[0].find('usp000jrsw') != -1

    # Check product
    tmpdir = tempfile.mkdtemp()
    try:
        cmd = ('getphases -i usp000jrsw -f excel %s' % tmpdir)
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
    assert files[0].find('usp000jrsw') != -1

    # Check product
    tmpdir = tempfile.mkdtemp()
    try:
        cmd = ('getphases -r 1 2 1 -b 1 2 1 2 -f excel %s' % tmpdir)
        res, stdout, stderr = get_command_output(cmd)

        cmp = 'Please specify either a bounding box OR radius search.'
        assert stdout.decode('utf-8').strip(os.linesep) == cmp

    except Exception as e:
        raise(e)
    finally:
        shutil.rmtree(tmpdir)


if __name__ == '__main__':
    test_phases()
