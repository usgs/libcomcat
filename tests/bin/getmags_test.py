#!/usr/bin/env python

# stdlib imports
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


def test_mag():
    # SMOKE TEST
    tmpdir = tempfile.mkdtemp()
    tmpfile = os.path.join(tmpdir, 'temp.csv')
    try:
        cmd = 'getmags -m 9.4 9.6 %s -s 1959-12-31 -e 1961-01-01' % tmpfile
        res, stdout, stderr = get_command_output(cmd)
        print(stdout)
        if not res:
            raise AssertionError(
                'getmags command %s failed with errors "%s"' % (cmd, stderr))
        df = pd.read_csv(tmpfile)
    except Exception as e:
        raise(e)
    finally:
        shutil.rmtree(tmpdir)
    # The largest recorded earthquake is a relatively stable check
    target_columns = ['id', 'time', 'lat', 'lon', 'depth', 'location',
                      'url', 'hypo_src', 'official-mw', 'us-NA']
    np.testing.assert_array_equal(df.columns, target_columns)
    target_id = 'official19600522191120_30'
    target_location = '1960 Great Chilean Earthquake (Valdivia Earthquake)'
    assert df['location'][0] == target_location
    assert df['id'][0] == target_id

    tmpdir = tempfile.mkdtemp()
    tmpfile = os.path.join(tmpdir, 'temp.xlsx')
    try:
        cmd = 'getmags -m 9.4 9.6 %s -s 1959-12-31 -e 1961-01-01 -f excel' % tmpfile
        res, stdout, stderr = get_command_output(cmd)
        print(stdout)
        if not res:
            raise AssertionError(
                'getmags command %s failed with errors "%s"' % (cmd, stderr))
        df = pd.read_excel(tmpfile)
    except Exception as e:
        raise(e)
    finally:
        shutil.rmtree(tmpdir)
    # The largest recorded earthquake is a relatively stable check
    target_columns = ['id', 'time', 'lat', 'lon', 'depth', 'location',
                      'url', 'hypo_src', 'official-mw', 'us-NA']
    np.testing.assert_array_equal(df.columns, target_columns)
    target_id = 'official19600522191120_30'
    target_location = '1960 Great Chilean Earthquake (Valdivia Earthquake)'
    assert df['location'][0] == target_location
    assert df['id'][0] == target_id

    # Test count
    try:
        cmd = 'getmags -m 9.4 9.6 -x %s -s 1959-12-31 -e 1961-01-01' % tmpfile
        res, stdout, stderr = get_command_output(cmd)
        print(stdout)
        if not res:
            raise AssertionError(
                'getmags command %s failed with errors "%s"' % (cmd, stderr))
    except Exception as e:
        raise(e)

    cmp = 'There are 1 events matching input criteria.'
    assert stdout.decode('utf-8').strip(os.linesep) == cmp

    # Test no events
    try:
        cmd = 'getmags -m 9.4 9.6 %s -s 1900-01-01 -e 1900-01-02' % tmpfile
        res, stdout, stderr = get_command_output(cmd)
        print(stdout)
        if not res:
            raise AssertionError(
                'getmags command %s failed with errors "%s"' % (cmd, stderr))
    except Exception as e:
        raise(e)

    cmp = 'No events found matching your search criteria. Exiting.'
    assert stdout.decode('utf-8').strip(os.linesep) == cmp

    # Test no events
    try:
        cmd = 'getmags -m 9.4 9.6 -x %s -r -38.143 73.407 1 -s 1900-01-01 -e 1900-01-02' % tmpfile
        res, stdout, stderr = get_command_output(cmd)
        print(stdout)
        if not res:
            raise AssertionError(
                'getmags command %s failed with errors "%s"' % (cmd, stderr))
    except Exception as e:
        raise(e)

    cmp = 'There are 0 events matching input criteria.'
    assert stdout.decode('utf-8').strip(os.linesep) == cmp

    # Test two citeria
    try:
        cmd = ('getmags -m 9.4 9.6 %s -r -38.143 73.407 1 -b 1 2 1 2 '
               '-s 1900-01-01 -e 1900-01-02' % tmpfile)
        res, stdout, stderr = get_command_output(cmd)
        print(stdout)

        cmp = 'Please specify either a bounding box OR radius search.'
        assert stdout.decode('utf-8').strip(os.linesep) == cmp

    except Exception as e:
        raise(e)


if __name__ == '__main__':
    test_mag()
