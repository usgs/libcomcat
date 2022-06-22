#!/usr/bin/env python

# stdlib imports
import os.path
import re
import subprocess
import shutil
import tempfile

# third party imports
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
    proc = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stdout, stderr = proc.communicate()
    retcode = proc.returncode
    if retcode == 0:
        retcode = True
    else:
        retcode = False
    return (retcode, stdout, stderr)


def test_getcsv():
    # SMOKE TEST
    # Test invalid country code
    tmpdir = tempfile.mkdtemp()
    temp_file = os.path.join(tmpdir, "temp.csv")
    try:
        cmd = (
            "getcsv %s -x -r -1.020000 -19.128000 1 -s "
            "1900-01-03T00:02:18 -e 1900-01-03T00:05:18" % temp_file
        )
        res, stdout, stderr = get_command_output(cmd)
        if not res:
            raise AssertionError(
                'getcsv command %s failed with errors "%s"' % (cmd, stderr)
            )
    except Exception as e:
        raise (e)
    finally:
        shutil.rmtree(tmpdir)
    cmp = "There are 0 events matching input criteria."
    assert stdout.decode("utf-8").strip(os.linesep) == cmp

    # test 1 event returned radius
    tmpdir = tempfile.mkdtemp()
    temp_file = os.path.join(tmpdir, "temp.csv")
    try:
        cmd = (
            "getcsv %s -x -r -1.020000 -19.128000 5.0 -s "
            "1918-06-03T00:02:18 -e 1918-06-03T00:05:18" % temp_file
        )
        res, stdout, stderr = get_command_output(cmd)
        if not res:
            raise AssertionError(
                'getcsv command %s failed with errors "%s"' % (cmd, stderr)
            )
    except Exception as e:
        raise (e)
    finally:
        shutil.rmtree(tmpdir)
    cmp = "There are 1 events matching input criteria."
    assert stdout.decode("utf-8").strip(os.linesep) == cmp

    # test 0 event returned radius
    tmpdir = tempfile.mkdtemp()
    temp_file = os.path.join(tmpdir, "temp.csv")
    try:
        cmd = (
            "getcsv %s -x -r -1.020000 -19.128000 1 -s "
            "1900-06-03T00:02:18 -e 1900-06-03T00:05:18" % temp_file
        )
        res, stdout, stderr = get_command_output(cmd)
        if not res:
            raise AssertionError(
                'getcsv command %s failed with errors "%s"' % (cmd, stderr)
            )
    except Exception as e:
        raise (e)
    finally:
        shutil.rmtree(tmpdir)
    cmp = "There are 0 events matching input criteria."
    assert stdout.decode("utf-8").strip(os.linesep) == cmp

    # test events returned bounding
    tmpdir = tempfile.mkdtemp()
    temp_file = os.path.join(tmpdir, "temp.csv")
    try:
        cmd = (
            "getcsv %s -x -b 163.213 -178.945 -48.980 -32.324"
            " -s 2013-01-01 -e 2014-01-01" % temp_file
        )
        res, stdout, stderr = get_command_output(cmd)
        if not res:
            raise AssertionError(
                'getcsv command %s failed with errors "%s"' % (cmd, stderr)
            )
    except Exception as e:
        raise (e)
    finally:
        shutil.rmtree(tmpdir)
    num = re.findall(r"\d+", str(stdout))[0]
    assert int(num) > 250

    # test events returned bounding
    tmpdir = tempfile.mkdtemp()
    temp_file = os.path.join(tmpdir, "temp.csv")
    try:
        cmd = (
            "getcsv %s -b 163.213 -178.945 -48.980 -32.324"
            " -s 2013-01-01 -e 2014-01-01" % temp_file
        )
        res, stdout, stderr = get_command_output(cmd)
        if not res:
            raise AssertionError(
                'getcsv command %s failed with errors "%s"' % (cmd, stderr)
            )
    except Exception as e:
        raise (e)
    finally:
        shutil.rmtree(tmpdir)
    assert b"...creating summary table" in stderr

    # test events returned bounding
    tmpdir = tempfile.mkdtemp()
    temp_file = os.path.join(tmpdir, "temp.csv")
    try:
        cmd = (
            "getcsv %s -b 163.213 -178.945 -48.980 -32.324"
            " -s 2013-01-01 -e 2014-01-01" % temp_file
        )
        res, stdout, stderr = get_command_output(cmd)
        if not res:
            raise AssertionError(
                'getcsv command %s failed with errors "%s"' % (cmd, stderr)
            )
    except Exception as e:
        raise (e)
    finally:
        shutil.rmtree(tmpdir)

    # test no events
    tmpdir = tempfile.mkdtemp()
    temp_file = os.path.join(tmpdir, "temp.csv")
    try:
        cmd = (
            "getcsv %s -x -b 163.213 -178.945 -48.980 -32.324"
            " -s 1900-01-01 -e 1900-01-02" % temp_file
        )
        res, stdout, stderr = get_command_output(cmd)
        if not res:
            raise AssertionError(
                'getcsv command %s failed with errors "%s"' % (cmd, stderr)
            )
    except Exception as e:
        raise (e)
    finally:
        shutil.rmtree(tmpdir)
    cmp = "There are 0 events matching input criteria."
    assert stdout.decode("utf-8").strip(os.linesep) == cmp

    # test no events
    tmpdir = tempfile.mkdtemp()
    temp_file = os.path.join(tmpdir, "temp.csv")
    try:
        cmd = (
            "getcsv %s -b 163.213 -178.945 -48.980 -32.324"
            " -s 1900-01-01 -e 1900-01-02" % temp_file
        )
        res, stdout, stderr = get_command_output(cmd)
        if not res:
            raise AssertionError(
                'getcsv command %s failed with errors "%s"' % (cmd, stderr)
            )
    except Exception as e:
        raise (e)
    finally:
        shutil.rmtree(tmpdir)
    assert b"No events found matching your search criteria. Exiting." in stderr

    # test bounding and code
    tmpdir = tempfile.mkdtemp()
    temp_file = os.path.join(tmpdir, "temp.csv")
    try:
        cmd = (
            "getcsv %s -r -1.020000 -19.128000 1 -s "
            "1918-06-03T00:02:18 -e 1918-06-03T00:05:18 --country abs" % temp_file
        )
        res, stdout, stderr = get_command_output(cmd)
        assert b"Please specify a bounding box, radius, or country code." in stderr
    except Exception as e:
        raise (e)
    finally:
        shutil.rmtree(tmpdir)

    # test bounding and code
    tmpdir = tempfile.mkdtemp()
    temp_file = os.path.join(tmpdir, "temp.csv")
    try:
        cmd = "getcsv %s --country abs" % temp_file
        res, stdout, stderr = get_command_output(cmd)
        assert (
            b"abs is not a valid ISO 3166 country code. See https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2 for the list."
            in stderr
        )
    except Exception as e:
        raise (e)
    finally:
        shutil.rmtree(tmpdir)

    # test events returned bounding
    tmpdir = tempfile.mkdtemp()
    temp_file = os.path.join(tmpdir, "temp.csv")
    try:
        cmd = (
            "getcsv %s -b 163.213 -178.945 -48.980 -32.324"
            " -s 2013-01-01 -e 2014-01-01 -f tab" % temp_file
        )
        res, stdout, stderr = get_command_output(cmd)
        if not res:
            raise AssertionError(
                'getcsv command %s failed with errors "%s"' % (cmd, stderr)
            )
    except Exception as e:
        raise (e)
    finally:
        shutil.rmtree(tmpdir)
    assert b"Created table...saving" in stderr

    # test events returned bounding
    tmpdir = tempfile.mkdtemp()
    temp_file = os.path.join(tmpdir, "temp.xlsx")
    try:
        cmd = (
            "getcsv %s -b 163.213 -178.945 -48.980 -32.324"
            " -s 2013-01-01 -e 2014-01-01 -f excel" % temp_file
        )
        res, stdout, stderr = get_command_output(cmd)
        if not res:
            raise AssertionError(
                'getcsv command %s failed with errors "%s"' % (cmd, stderr)
            )
    except Exception as e:
        raise (e)
    finally:
        shutil.rmtree(tmpdir)
    target = b"records saved to %b" % temp_file.encode("utf-8")
    assert target in stderr

    # test that --numdays works as expected
    tmpdir = tempfile.mkdtemp()
    temp_file = os.path.join(tmpdir, "temp.xlsx")
    try:
        cmd = (
            "getcsv %s -b 163.213 -178.945 -48.980 -32.324"
            " -s 2013-01-01 --numdays 10 -f excel" % temp_file
        )
        res, stdout, stderr = get_command_output(cmd)
        if not res:
            raise AssertionError(
                'getcsv command %s failed with errors "%s"' % (cmd, stderr)
            )
        df = pd.read_excel(temp_file)
        assert df["time"].min().day == 6
        assert df["time"].max().day == 9
    except Exception as e:
        raise (e)
    finally:
        shutil.rmtree(tmpdir)
    target = b"records saved to %b" % temp_file.encode("utf-8")
    assert target in stderr

    # test that significance works as expected
    tmpdir = tempfile.mkdtemp()
    temp_file = os.path.join(tmpdir, "temp.xlsx")
    try:
        cmd = (
            "getcsv %s -b -180 180 -90 90"
            " -s 2019-10-20 -e 2019-10-29 -f excel "
            "--sig-range 600 10000" % temp_file
        )
        res, stdout, stderr = get_command_output(cmd)
        if not res:
            raise AssertionError(
                'getcsv command %s failed with errors "%s"' % (cmd, stderr)
            )
        df = pd.read_excel(temp_file)
        assert len(df) >= 2
    except Exception as e:
        raise (e)
    finally:
        shutil.rmtree(tmpdir)
    target = b"records saved to %b" % temp_file.encode("utf-8")
    assert target in stderr


if __name__ == "__main__":
    test_getcsv()
