#!/usr/bin/env python

#stdlib
import argparse
import os
import sys

#third party
import numpy as np

#local
from libcomcat import ellipse

if __name__ == '__main__':
    desc = '''Convert between various representation of earthquake error ellipse.

    Tait-Bryan (QuakeML) representation to 3x3 matrix representation:

    getellipse.py -t 16.0 6.1 10.9 139.0 6.0 88.9075

    --------------------------------------------------------------
    SemiMajorAxis       : Azimuth 139.0 Plunge   6.0 Length  16.0
    SemiMinorAxis       : Azimuth 308.7 Plunge  83.9 Length   6.1
    SemiIntermediateAxis: Azimuth  48.9 Plunge   1.1 Length  10.9 
    -------------------------------------------------------------- 

    Tait-Bryan (QuakeML) representation to surface projection:

    getellipse.py -q 16.0 6.1 10.9 139.0 6.0 88.9075 95 0.76 0

    -------------------------------------------------------
    Surface Ellipse: Major:  13.7 Minor   9.4 Azimuth 319.1  
    -------------------------------------------------------

    3x3 Matrix representation to surface projection:

    getellipse.py -m 139.0 6.0 16.0 308.7 83.9 6.1 48.9 1.1 10.9 95 0.76 0

    -------------------------------------------------------
    Surface Ellipse: Major:  13.7 Minor   9.4 Azimuth 319.1
    -------------------------------------------------------
    
    3x3 matrix representation to Tait-Bryan (QuakeML) representation:

    getellipse.py -r 139.0 6.0 16.0 308.7 83.9 6.1 48.9 1.1 10.9

    -----------------------------------------------------------------------------
    SemiMajor Axis       : Azimuth 139.0 Plunge   6.0 Rotation  88.9 Length  16.0
    SemiMinor Axis       : Azimuth   nan Plunge   nan Rotation   nan Length   6.1
    SemiIntermediate Axis: Azimuth   nan Plunge   nan Rotation   nan Length  10.9
    -----------------------------------------------------------------------------
    '''
    parser = argparse.ArgumentParser(description=desc,formatter_class=argparse.RawDescriptionHelpFormatter)
    #optional arguments
    parser.add_argument('-t','--tait2matrix', 
                        metavar=('alen','blen','clen','azimuth','plunge','rotation'),
                        type=float,
                        nargs=6,
                        help='Convert Tait-Bryan error ellipse to 3x3 matrix')
    parser.add_argument('-r','--matrix2tait', 
                        metavar=('AAzim','APlunge','ALen','BAzim','BPlunge','BLen','CAzim','CPlunge','CLen'),
                        type=float,
                        nargs=9,
                        help='Convert 3x3 matrix error ellipse to Tait-Bryan representation')
    parser.add_argument('-q','--tait2surface', 
                        metavar=('alen','blen','clen','azimuth','plunge','rotation','ndef','stderr','isfixed'),
                        type=float,
                        nargs=9,
                        help='Project Tait-Bryan error ellipse to surface')
    parser.add_argument('-m','--matrix2surface', 
                        metavar=('AAzim','APlunge','ALen','BAzim','BPlunge','BLen','CAzim','CPlunge','CLen','ndef','stderr','isfixed'),
                        type=float,
                        nargs=12,
                        help='Project 3x3 matrix error ellipse to surface')
    args = parser.parse_args()
    if args.tait2matrix is not None:
        alen,blen,clen,azim,plunge,rot = args.tait2matrix
        matrix = ellipse.tait2vec(alen,blen,clen,azim,plunge,rot)
        print 'SemiMajorAxis       : Azimuth %5.1f Plunge %5.1f Length %5.1f' % (matrix[0][0],matrix[0][1],matrix[0][2])
        print 'SemiMinorAxis       : Azimuth %5.1f Plunge %5.1f Length %5.1f' % (matrix[1][0],matrix[1][1],matrix[1][2])
        print 'SemiIntermediateAxis: Azimuth %5.1f Plunge %5.1f Length %5.1f' % (matrix[2][0],matrix[2][1],matrix[2][2])
        sys.exit(0)

    if args.matrix2tait is not None:
        prax = np.array(args.matrix2tait).reshape(3,3)
        alen,blen,clen,aazimuth,aplunge,arot = ellipse.vec2tait(prax)
        tpl = (aazimuth,aplunge,arot,alen)
        print 'SemiMajor Axis       : Azimuth %5.1f Plunge %5.1f Rotation %5.1f Length %5.1f' % tpl
        print 'SemiMinor Axis       : Azimuth %5s Plunge %5s Rotation %5s Length %5s' % (np.nan,np.nan,np.nan,blen)
        print 'SemiIntermediate Axis: Azimuth %5s Plunge %5s Rotation %5s Length %5s' % (np.nan,np.nan,np.nan,clen)
        sys.exit(0)

    if args.tait2surface is not None:
        alen,blen,clen,azim,plunge,rot,ndef,stderr,isfixed = args.tait2surface
        major,minor,azimuth = ellipse.tait2surface(alen,blen,clen,azim,plunge,rot,ndef,stderr,isfixed)
        print 'Surface Ellipse: Major: %5.1f Minor %5.1f Azimuth %5.1f' % (major,minor,azimuth)
        sys.exit(0)

    if args.matrix2surface is not None:
        prax = np.array(args.matrix2surface[0:9]).reshape(3,3)
        ndef,stderr,isfixed = args.matrix2surface[9:]
        major,minor,azimuth = ellipse.vec2surface(prax,ndef,stderr,isfixed)
        print 'Surface Ellipse: Major: %5.1f Minor %5.1f Azimuth %5.1f' % (major,minor,azimuth)
        sys.exit(0)
