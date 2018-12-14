#!/usr/bin/env python

# stdlib imports
import os.path
import subprocess
import shutil
import tempfile

# local imports
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


def test_get_impact():
    filedir = os.path.dirname(os.path.abspath(__file__))
    getimpact = os.path.join(filedir, '..', '..', 'bin', 'getimpact')

    print('iscgem910478 limited sources')
    targetfile = os.path.join(filedir, '..', 'data', 'impact_iscgem910478.csv')
    parameters = '--host dev01-earthquake.cr.usgs.gov'
    tmpdir = tempfile.mkdtemp()
    temp_file = os.path.join(tmpdir, 'temp.csv')
    try:
        parameters = '-i iscgem910478 -f csv --host dev01-earthquake.cr.usgs.gov'
        cmd = '%s %s %s' % (getimpact, temp_file, parameters)
        res, stdout, stderr = get_command_output(cmd)
        if not res:
            raise AssertionError(
                'getimpact command %s failed with errors "%s"' % (cmd, stderr))
        print(stdout)
        excel = pd.read_csv(temp_file)
    except Exception as e:
        raise(e)
    finally:
        shutil.rmtree(tmpdir)
    targetexcel = pd.read_csv(targetfile)
    pd.util.testing.assert_frame_equal(excel, targetexcel)

    print('iscgem910478 all sources')
    targetfile = os.path.join(filedir, '..', 'data',
            'impact_iscgem910478_allsources.csv')
    parameters = '--host dev01-earthquake.cr.usgs.gov'
    tmpdir = tempfile.mkdtemp()
    temp_file = os.path.join(tmpdir, 'temp.csv')
    try:
        parameters = '-i iscgem910478 -f csv --host dev01-earthquake.cr.usgs.gov '
        parameters += '-a'
        cmd = '%s %s %s' % (getimpact, temp_file, parameters)
        res, stdout, stderr = get_command_output(cmd)
        if not res:
            raise AssertionError(
                'getimpact command %s failed with errors "%s"' % (cmd, stderr))
        print(stdout)
        excel = pd.read_csv(temp_file)
    except Exception as e:
        raise(e)
    finally:
        shutil.rmtree(tmpdir)
    targetexcel = pd.read_csv(targetfile)
    pd.util.testing.assert_frame_equal(excel, targetexcel)

    print('iscgem910478 limited sources and shaking')
    targetfile = os.path.join(filedir, '..', 'data',
            'impact_iscgem910478_shaking.csv')
    parameters = '--host dev01-earthquake.cr.usgs.gov'
    tmpdir = tempfile.mkdtemp()
    temp_file = os.path.join(tmpdir, 'temp.csv')
    try:
        parameters = '-i iscgem910478 -f csv --host dev01-earthquake.cr.usgs.gov '
        parameters += '-t shaking'
        cmd = '%s %s %s' % (getimpact, temp_file, parameters)
        res, stdout, stderr = get_command_output(cmd)
        if not res:
            raise AssertionError(
                'getimpact command %s failed with errors "%s"' % (cmd, stderr))
        print(stdout)
        excel = pd.read_csv(temp_file)
    except Exception as e:
        raise(e)
    finally:
        shutil.rmtree(tmpdir)
    targetexcel = pd.read_csv(targetfile)
    pd.util.testing.assert_frame_equal(excel, targetexcel)

    print('usp0005rcg without contributing')
    targetfile = os.path.join(filedir, '..', 'data',
            'impact_usp0005rcg.csv')
    parameters = '--host dev01-earthquake.cr.usgs.gov'
    tmpdir = tempfile.mkdtemp()
    temp_file = os.path.join(tmpdir, 'temp.csv')
    try:
        parameters = '-i usp0005rcg -f csv --host dev01-earthquake.cr.usgs.gov '
        cmd = '%s %s %s' % (getimpact, temp_file, parameters)
        res, stdout, stderr = get_command_output(cmd)
        if not res:
            raise AssertionError(
                'getimpact command %s failed with errors "%s"' % (cmd, stderr))
        print(stdout)
        excel = pd.read_csv(temp_file)
    except Exception as e:
        raise(e)
    finally:
        shutil.rmtree(tmpdir)
    targetexcel = pd.read_csv(targetfile)
    pd.util.testing.assert_frame_equal(excel, targetexcel)

    print('usp0005rcg without contributing all sources')
    targetfile = os.path.join(filedir, '..', 'data',
            'impact_usp0005rcg_allsources.csv')
    parameters = '--host dev01-earthquake.cr.usgs.gov'
    tmpdir = tempfile.mkdtemp()
    temp_file = os.path.join(tmpdir, 'temp.csv')
    try:
        parameters = '-i usp0005rcg -f csv --host dev01-earthquake.cr.usgs.gov '
        parameters += '-a'
        cmd = '%s %s %s' % (getimpact, temp_file, parameters)
        res, stdout, stderr = get_command_output(cmd)
        if not res:
            raise AssertionError(
                'getimpact command %s failed with errors "%s"' % (cmd, stderr))
        print(stdout)
        excel = pd.read_csv(temp_file)
    except Exception as e:
        raise(e)
    finally:
        shutil.rmtree(tmpdir)
    targetexcel = pd.read_csv(targetfile)
    pd.util.testing.assert_frame_equal(excel, targetexcel)

    print('usp0005rcg with contributing all sources')
    targetfile = os.path.join(filedir, '..', 'data',
            'impact_usp0005rcg_allsources_contributing.csv')
    parameters = '--host dev01-earthquake.cr.usgs.gov'
    tmpdir = tempfile.mkdtemp()
    temp_file = os.path.join(tmpdir, 'temp.csv')
    try:
        parameters = '-i usp0005rcg -f csv --host dev01-earthquake.cr.usgs.gov '
        parameters += '-a -c'
        cmd = '%s %s %s' % (getimpact, temp_file, parameters)
        res, stdout, stderr = get_command_output(cmd)
        if not res:
            raise AssertionError(
                'getimpact command %s failed with errors "%s"' % (cmd, stderr))
        print(stdout)
        excel = pd.read_csv(temp_file)
    except Exception as e:
        raise(e)
    finally:
        shutil.rmtree(tmpdir)
    targetexcel = pd.read_csv(targetfile)
    pd.util.testing.assert_frame_equal(excel, targetexcel)

    print('usp0005rcg with contributing')
    targetfile = os.path.join(filedir, '..', 'data',
            'impact_usp0005rcg_contributing.csv')
    parameters = '--host dev01-earthquake.cr.usgs.gov'
    tmpdir = tempfile.mkdtemp()
    temp_file = os.path.join(tmpdir, 'temp.csv')
    try:
        parameters = '-i usp0005rcg -f csv --host dev01-earthquake.cr.usgs.gov '
        parameters += '-c'
        cmd = '%s %s %s' % (getimpact, temp_file, parameters)
        res, stdout, stderr = get_command_output(cmd)
        if not res:
            raise AssertionError(
                'getimpact command %s failed with errors "%s"' % (cmd, stderr))
        print(stdout)
        excel = pd.read_csv(temp_file)
    except Exception as e:
        raise(e)
    finally:
        shutil.rmtree(tmpdir)
    targetexcel = pd.read_csv(targetfile)
    pd.util.testing.assert_frame_equal(excel, targetexcel)

    print('usp0005rcg landslide and shaking')
    targetfile = os.path.join(filedir, '..', 'data',
            'impact_usp0005rcg_landslide_shaking.csv')
    parameters = '--host dev01-earthquake.cr.usgs.gov'
    tmpdir = tempfile.mkdtemp()
    temp_file = os.path.join(tmpdir, 'temp.csv')
    try:
        parameters = '-i usp0005rcg -f csv --host dev01-earthquake.cr.usgs.gov '
        parameters += '-t landslide shaking'
        cmd = '%s %s %s' % (getimpact, temp_file, parameters)
        res, stdout, stderr = get_command_output(cmd)
        if not res:
            raise AssertionError(
                'getimpact command %s failed with errors "%s"' % (cmd, stderr))
        print(stdout)
        excel = pd.read_csv(temp_file)
    except Exception as e:
        raise(e)
    finally:
        shutil.rmtree(tmpdir)
    targetexcel = pd.read_csv(targetfile)
    pd.util.testing.assert_frame_equal(excel, targetexcel)

    print('usp0005rcg destroyed')
    targetfile = os.path.join(filedir, '..', 'data',
            'impact_usp0005rcg_destroyed.csv')
    parameters = '--host dev01-earthquake.cr.usgs.gov'
    tmpdir = tempfile.mkdtemp()
    temp_file = os.path.join(tmpdir, 'temp.csv')
    try:
        parameters = '-i usp0005rcg -f csv --host dev01-earthquake.cr.usgs.gov '
        parameters += '-x destroyed'
        cmd = '%s %s %s' % (getimpact, temp_file, parameters)
        res, stdout, stderr = get_command_output(cmd)
        if not res:
            raise AssertionError(
                'getimpact command %s failed with errors "%s"' % (cmd, stderr))
        print(stdout)
        excel = pd.read_csv(temp_file)
    except Exception as e:
        raise(e)
    finally:
        shutil.rmtree(tmpdir)
    targetexcel = pd.read_csv(targetfile)
    pd.util.testing.assert_frame_equal(excel, targetexcel)

if __name__ == '__main__':
    test_get_impact()
