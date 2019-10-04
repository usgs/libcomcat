#!/usr/bin/env python

# stdlib imports
import os.path
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


def test_pager():
    # SMOKE TESTS
    # Check for events without pager products
    tmpdir = tempfile.mkdtemp()
    tmpfile = os.path.join(tmpdir, 'temp.csv')
    try:
        cmd = 'getpager -i official19600522191120_30 %s' % tmpfile
        res, stdout, stderr = get_command_output(cmd)
        if not res:
            raise AssertionError(
                'getpager command %s failed with errors "%s"' % (cmd, stderr))
    except Exception as e:
        raise(e)
    finally:
        shutil.rmtree(tmpdir)

    cmp = 'No Pager products found for requested event(s)'
    lines = stderr.decode('utf-8').split(os.linesep)
    lines = [line for line in lines if line]
    assert lines[-1].strip(os.linesep) == cmp

    # Check for events with pager dataframes
    tmpdir = tempfile.mkdtemp()
    tmpfile = os.path.join(tmpdir, 'temp.csv')
    try:
        cmd = 'getpager -i usp000jhjb %s' % tmpfile
        res, stdout, stderr = get_command_output(cmd)
        if not res:
            raise AssertionError(
                'getpager command %s failed with errors "%s"' % (cmd, stderr))
        df = pd.read_csv(tmpfile, comment='#')
    except Exception as e:
        raise(e)
    finally:
        shutil.rmtree(tmpdir)
    cols = df.columns
    id = df['id'][0]
    location = df['location'][0]
    target_cols = ['id', 'location', 'time', 'latitude', 'longitude',
                   'depth', 'magnitude', 'country', 'pager_version',
                   'mmi1', 'mmi2', 'mmi3', 'mmi4', 'mmi5', 'mmi6',
                   'mmi7', 'mmi8', 'mmi9', 'mmi10']
    target_id = 'usp000jhjb'
    target_location = 'off the west coast of northern Sumatra'
    np.testing.assert_array_equal(cols, target_cols)
    assert id == target_id
    assert location == target_location

    # Check for events with pager dataframes
    tmpdir = tempfile.mkdtemp()
    tmpfile = os.path.join(tmpdir, 'temp.xlsx')
    try:
        cmd = 'getpager -i usp000jhjb %s -f excel' % tmpfile
        res, stdout, stderr = get_command_output(cmd)
        if not res:
            raise AssertionError(
                'getpager command %s failed with errors "%s"' % (cmd, stderr))
        df = pd.read_excel(tmpfile, skiprows=11)
    except Exception as e:
        raise(e)
    finally:
        shutil.rmtree(tmpdir)
    cols = df.columns
    id = df['id'][0]
    location = df['location'][0]
    target_cols = ['id', 'location', 'time', 'latitude', 'longitude',
                   'depth', 'magnitude', 'country', 'pager_version',
                   'mmi1', 'mmi2', 'mmi3', 'mmi4', 'mmi5', 'mmi6',
                   'mmi7', 'mmi8', 'mmi9', 'mmi10']
    target_id = 'usp000jhjb'
    target_location = 'off the west coast of northern Sumatra'
    np.testing.assert_array_equal(cols, target_cols)
    assert id == target_id
    assert location == target_location

    # Check for events with pager dataframes
    tmpdir = tempfile.mkdtemp()
    tmpfile = os.path.join(tmpdir, 'temp.xlsx')
    try:
        cmd = ('getpager -s 2012-04-11T09:43:10 -e 2012-04-11T11:43:10'
               ' -r 0.802 92.463 1 %s -f excel' % tmpfile)
        res, stdout, stderr = get_command_output(cmd)
        if not res:
            raise AssertionError(
                'getpager command %s failed with errors "%s"' % (cmd, stderr))
        df = pd.read_excel(tmpfile, skiprows=11)
    except Exception as e:
        raise(e)
    finally:
        shutil.rmtree(tmpdir)
    cols = df.columns
    id = df['id'][0]
    location = df['location'][0]
    target_cols = ['id', 'location', 'time', 'latitude', 'longitude',
                   'depth', 'magnitude', 'country', 'pager_version',
                   'mmi1', 'mmi2', 'mmi3', 'mmi4', 'mmi5', 'mmi6',
                   'mmi7', 'mmi8', 'mmi9', 'mmi10']
    target_id = 'usp000jhjb'
    target_location = 'off the west coast of northern Sumatra'
    np.testing.assert_array_equal(cols, target_cols)
    assert id == target_id
    assert location == target_location

    # Check for events with pager dataframes
    tmpdir = tempfile.mkdtemp()
    tmpfile = os.path.join(tmpdir, 'temp.xlsx')
    try:
        cmd = ('getpager -s 2012-04-11T09:43:10 -e 2012-04-11T11:43:10'
               ' -r 0.802 92.463 1 -b 1 2 1 2 %s -f excel' % tmpfile)
        res, stdout, stderr = get_command_output(cmd)

        cmp = 'Please specify either a bounding box OR radius search.'
        assert stdout.decode('utf-8').strip(os.linesep) == cmp

    except Exception as e:
        raise(e)
    finally:
        shutil.rmtree(tmpdir)


if __name__ == '__main__':
    test_pager()
