#!/usr/bin/env python

# stdlib imports
import os.path
import subprocess
import shutil
import tempfile


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


def test_url():
    # SMOKE TEST
    # Test no result
    tmpdir = tempfile.mkdtemp()
    temp_file = os.path.join(tmpdir, "temp.csv")
    try:
        parameters = (
            "findid -w 180 -r 20 --eventinfo 1900-06-03T00:03:18 "
            "-1.020000 -19.128000"
        )
        cmd = "%s" % (parameters)
        res, stdout, stderr = get_command_output(cmd)
        if not res:
            raise AssertionError(
                'findid command %s failed with errors "%s"' % (cmd, stderr)
            )
    except Exception as e:
        raise (e)
    finally:
        shutil.rmtree(tmpdir)
    target_msg = b"findid.main: No events found matching your search criteria. Exiting."
    assert target_msg in stderr

    # Test return
    tmpdir = tempfile.mkdtemp()
    temp_file = os.path.join(tmpdir, "temp.csv")
    try:
        parameters = (
            "findid -w 180 -r 20 --eventinfo 1918-06-03T00:03:18 "
            "-1.020000 -19.128000 -a"
        )
        cmd = "%s" % (parameters)
        res, stdout, stderr = get_command_output(cmd)
        if not res:
            raise AssertionError(
                'findid command %s failed with errors "%s"' % (cmd, stderr)
            )
    except Exception as e:
        raise (e)
    finally:
        shutil.rmtree(tmpdir)
    assert stdout.find(b"iscgem913159") != -1

    # Test return
    tmpdir = tempfile.mkdtemp()
    temp_file = os.path.join(tmpdir, "temp.csv")
    try:
        parameters = (
            "findid -u -w 180 -r 20 --eventinfo 1918-06-03T00:03:18 "
            "-1.020000 -19.128000"
        )
        cmd = "%s" % (parameters)
        res, stdout, stderr = get_command_output(cmd)
        if not res:
            raise AssertionError(
                'findid command %s failed with errors "%s"' % (cmd, stderr)
            )
    except Exception as e:
        raise (e)
    finally:
        shutil.rmtree(tmpdir)
    target_url = "https://earthquake.usgs.gov/earthquakes/eventpage/iscgem913159"
    assert target_url == stdout.decode("utf-8").strip(os.linesep)

    # Test return
    tmpdir = tempfile.mkdtemp()
    temp_file = os.path.join(tmpdir, "temp.csv")
    try:
        parameters = (
            "findid -w 180 -r 20 --eventinfo 1918-06-03T00:03:18 "
            "-1.020000 -19.128000"
        )
        cmd = "%s" % (parameters)
        res, stdout, stderr = get_command_output(cmd)
        if not res:
            raise AssertionError(
                'findid command %s failed with errors "%s"' % (cmd, stderr)
            )
    except Exception as e:
        raise (e)
    finally:
        shutil.rmtree(tmpdir)


def test_authoritative():
    cmd = "findid -i pt19187000"
    res, stdout, stderr = get_command_output(cmd)
    if not res:
        raise AssertionError(
            'findid command %s failed with errors "%s"' % (cmd, stderr)
        )
    lines = stdout.decode("utf-8").split(os.linesep)
    assert "ci38457511" in lines[0]


if __name__ == "__main__":
    test_authoritative()
    test_url()
