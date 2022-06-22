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


def test_geteventhist():
    # SMOKE TEST
    tmpdir = tempfile.mkdtemp()
    try:
        cmd = "geteventhist iscgem913159 -d %s -f excel --split" % tmpdir
        res, stdout, stderr = get_command_output(cmd)
        print(stdout)
        if not res:
            raise AssertionError(
                'geteventhist command %s failed with errors "%s"' % (cmd, stderr)
            )
        fpath = os.path.join(tmpdir, "iscgem913159_origin.xlsx")
        df = pd.read_excel(fpath, skiprows=6)
    except Exception as e:
        raise (e)
    finally:
        shutil.rmtree(tmpdir)
    target_codes = np.array(
        [
            "iscgem913159",
            "iscgem913159",
            "iscgemsup913159",
            "iscgem913159",
            "iscgemsup913159",
        ]
    )
    target_version = np.array([1, 2, 3, 4, 5])
    target_depth = np.array([10, np.nan, 10, 10, np.nan])
    # The history up to now should not change
    np.testing.assert_array_equal(df["Code"].values, target_codes)
    np.testing.assert_array_equal(df["Product Version"], target_version)
    np.testing.assert_array_equal(df["Depth"], target_depth)

    # SMOKE TEST for multiple events
    tmpdir = tempfile.mkdtemp()
    try:
        cmd = "geteventhist us2000artt -d %s -r 100 -w 500" % tmpdir
        res, stdout, stderr = get_command_output(cmd)
        print(stdout)
        if not res:
            raise AssertionError(
                'geteventhist command %s failed with errors "%s"' % (cmd, stderr)
            )
        fpath = os.path.join(tmpdir, "us2000artt.csv")
        df = pd.read_csv(fpath, skiprows=6)
    except Exception as e:
        raise (e)
    finally:
        shutil.rmtree(tmpdir)
    # The history up to now should not change
    assert "us2000artt" in df["Code"].tolist()

    # SMOKE TEST for multiple events
    tmpdir = tempfile.mkdtemp()
    try:
        cmd = "geteventhist us2000artt --web -r 100 -w 500"
        res, stdout, stderr = get_command_output(cmd)
        if not res:
            raise AssertionError(
                'geteventhist command %s failed with errors "%s"' % (cmd, stderr)
            )
    except Exception as e:
        raise (e)
    finally:
        shutil.rmtree(tmpdir)
    # The history up to now should not change
    assert b"us2000artt" in stdout


if __name__ == "__main__":
    test_geteventhist()
