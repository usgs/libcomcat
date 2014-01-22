#!/usr/bin/env python

#stdlib imports
import math

#third party imports
import numpy as np
from neicutil import text

#local imports
import jacobi

DEG2RAD = np.pi/180.0
RAD2DEG = 180.0/np.pi

def rotatePointAroundAxis(p,theta,r):
    #p and r are three element vectors of [n e z]
    dNormFact = np.sqrt(r['n']*r['n'] + r['e']*r['e'] + r['z']*r['z'])
    r['n'] /= dNormFact
    r['e'] /= dNormFact
    r['z'] /= dNormFact

    costheta = np.cos(np.radians(theta))
    sintheta = np.sin(np.radians(theta))

    q = {}
    q['n'] = (costheta + (1 - costheta) * r['n'] * r['n']) * p['n'] + \
    ((1 - costheta) * r['n'] * r['e'] - r['z'] * sintheta) * p['e'] + \
    ((1 - costheta) * r['n'] * r['z'] + r['e'] * sintheta) * p['z']

    q['e'] = ((1 - costheta) * r['n'] * r['e'] + r['z'] * sintheta) * p['n'] + \
    (costheta + (1 - costheta) * r['e'] * r['e']) * p['e']       + \
    ((1 - costheta) * r['e'] * r['z'] - r['n'] * sintheta) * p['z']

    q['z'] = ((1 - costheta) * r['n'] * r['z'] - r['e'] * sintheta) * p['n'] + \
    ((1 - costheta) * r['e'] * r['z'] + r['n'] * sintheta) * p['e'] + \
    (costheta + (1 - costheta) * r['z'] * r['z']) * p['z']

    return q

def calcReliableAzm(dNorth,dEast):
    dAzm1    = 90.0 - (np.arcsin(dNorth) / (DEG2RAD))
    dAzm2    = 90.0 - (np.arccos(dEast) / (DEG2RAD))

    if ((dAzm1 > dAzm2 and dAzm1 - dAzm2 < 1.0) or (dAzm2 >= dAzm1 and dAzm2 - dAzm1 < 1.0)):
        return(dAzm1)
    elif (dAzm1 >= 0.0 and dAzm1 <= 90.0):
        dAzm = dAzm2
    elif (dAzm2 >= 0.0 and dAzm2 <= 90.0):
        dAzm = dAzm1
    else:
        dAzm = 360.0 - dAzm1

    if (dAzm < 0):
        dAzm += 360.0

    return dAzm

def getEllipsoid(axisdict):
    majorazimuth = axisdict['major']['azimuth']
    majordip = axisdict['major']['dip']
    majorrot = axisdict['major']['rotation']

    #Define Pt0.  This Is The Point That Represents The Minor Axis
    #After The Initial Azimuthal Rotation (Given By Majoraxisazimuth
    #Around The Z Or Intermediate Axis), But Prior To The Rotation
    #Around The Major Axis.  East Is 90 Degrees Past N, So Add 90
    #To The Angle.  Note That Because Trig Functions Go
    #Counter-Clockwise And Start In The +X(East) Direction, But Azm Is
    #Clockwise And Starts At +Y(North), We Have To Do Some
    #Transformation Hanky Panky To Get Things To Work Out.  I.E
    #Transform The Angle X Via F(X) = 90 - X
    #and don't forget the always fun degrees/radians conversion.
    pt0 = {}
    pt0['n'] = np.sin(np.radians((90-(majorazimuth +90))))
    pt0['e'] = np.cos(np.radians((90-(majorazimuth +90))))
    pt0['z'] = 0.0
        
    # define ptmajor.  This is the point that represents Major Axis
    # Vector (after the Azimuthal and Dip rotations)
    ptmajor = {}
    ptmajor['n'] = np.sin(np.radians((90-(majorazimuth))))
    ptmajor['e'] = np.cos(np.radians((90-(majorazimuth))))
    ptmajor['z'] = np.sin(np.radians(majordip))

    #calculate the orientation of the Minor vector by applying the QuakeML rotation angle
    ptminor = rotatePointAroundAxis(pt0,majorrot,ptmajor)

    # /* Normalize the unit vector ptminor so that N2+E2 = 1, so we can apply trig functions */   
    dNormFactor = 1.0/np.sqrt(ptminor['n']*ptminor['n'] + ptminor['e']*ptminor['e'])
    # /* Calculate the Azimuth via arcsin() and arccos() */
    dAzmMinor = calcReliableAzm(ptminor['n']*dNormFactor, ptminor['e']*dNormFactor);
    # /* Calculate the Dip via arcsin() */
    dDipMinor = np.arcsin(ptminor['z']) / DEG2RAD


    #calculate the orientation of the Intermediate vector(originally Z), which is 90 deg past the minor vector
    ptIntermed = rotatePointAroundAxis(ptminor, 90, ptmajor)

    #Normalize the unit vector ptIntermed so that N2+E2 = 1, so we can apply trig functions
    dNormFactor = 1/np.sqrt(ptIntermed['n']*ptIntermed['n'] + ptIntermed['e']*ptIntermed['e'])
    #Calculate the Azimuth via arcsin() and arccos()
    dAzmIntermed = calcReliableAzm(ptIntermed['n']*dNormFactor, ptIntermed['e']*dNormFactor)
    #Calculate the Dip via arcsin()
    dDipMinor = np.arcsin(ptminor['z']) / DEG2RAD
    dDipIntermed = np.arcsin(ptIntermed['z']) / DEG2RAD

    axisdict = axisdict.copy()
    axisdict['minor']['azimuth'] = dAzmMinor
    axisdict['minor']['dip'] = dDipMinor
    axisdict['intermediate']['azimuth'] = dAzmIntermed
    axisdict['intermediate']['dip'] = dDipIntermed

    return axisdict

def Fisher10(nu1,nu2):
    fisher10 = float('nan')
    xnu = [1.0/30.0, 1.0/40.0, 1.0/60.0, 1.0/120.0, 0.0]
    # /* inverses of 30, 40, 60, 120, and infinity */
    tab = np.resize(np.array([49.50,  9.00,  5.46,  4.32,  3.78,  3.46,  3.26,  3.11,
                  3.01,  2.92,  2.86,  2.81,  2.76,  2.73,  2.70,  2.67,
                  2.64,  2.62,  2.61,  2.59,  2.57,  2.56,  2.55,  2.54,
                  2.53,  2.52,  2.51,  2.50,  2.50,  2.49,  2.44,  2.39,
                  2.35,  2.30, 53.59,  9.16,  5.39,  4.19,  3.62,  3.29, 
                  3.07,  2.92,  2.81,  2.73,  2.66,  2.61,  2.56,  2.52, 
                  2.49,  2.46,  2.44,  2.42,  2.40,  2.38,  2.36,  2.35, 
                  2.34,  2.33,  2.32,  2.31,  2.30,  2.29,  2.28,  2.28, 
                  2.23,  2.18,  2.13,  2.08, 55.83,  9.24,  5.34,  4.11, 
                  3.52,  3.18,  2.96,  2.81,  2.69,  2.61,  2.54,  2.48, 
                  2.43,  2.39,  2.36,  2.33,  2.31,  2.29,  2.27,  2.25, 
                  2.23,  2.22,  2.21,  2.19,  2.18,  2.17,  2.17,  2.16, 
                  2.15,  2.14,  2.09,  2.04,  1.99,  1.94]),(3,34))
    idx = nu1 - 2
    if nu2 <= 30:
        fisher10 = tab[idx][nu2-1]
        return fisher10

    znu = 1.0/nu2
    for i in range(1,5):
        if znu >= xnu[i]:
            fisher10 = fisher10 = (znu - xnu[i-1]) * (tab[idx][29+i] - tab[idx][28+i])/  (xnu[i] - xnu[i-1]) + tab[idx][28+i]
            return fisher10

def errcon(n,ievt,se,prax):
    #n - number of phases used to calculate error ellipse (??)
    #ievt - boolean whether depth was fixed or free (do I know this?)
    #se - std error from origin quality
    #prax - Matrix with values:
    #[minorazimuth minorplunge minorlength;
    # interazimuth interplunge interlength;
    # majorazimuth majorplunge majorlength]
    #output - 2x2

    #     /* initialize some values */
    nFree = 8
    tol   = 1.0e-15
    tol2  = 2.0e-15
    m     = 3
    m1    = 2
    m2    = 4

    a = np.zeros((2,2))
    s2  = (nFree + (n-m2)*se*se)/(nFree + n - m2)
    f10 = Fisher10(m, nFree + n - m2)
    fac = 1.0/(m * s2 * f10)

    x = np.zeros((2,1))
    for k in range(0,m):
        ce = np.cos(DEG2RAD * prax[k][1])
        x[0] = -ce  * np.cos(DEG2RAD * prax[k][0])
        x[1] =  ce  * np.sin(DEG2RAD * prax[k][0])
        ce   =  fac * prax[k][2] * prax[k][2]  
        for j in range(0,m1):
            for i in range(0,m1):
                a[j][i] = a[j][i] + ce * x[i] * x[j]
                
    ellipse2d = np.zeros((3,3))
    #we're running into a problem with jacobi - namely, the diagonal values aren't exactly
    #equal (differ at 15th decimal).  We'll round them both to nearest billionth.
    a[0][1] = text.roundToNearest(a[0][1],1e-9)
    a[1][0] = text.roundToNearest(a[0][1],1e-9)
    eigenvalue,eigenvector,sweeps = jacobi.jacobi(a)
    idx = eigenvalue.argsort()[::-1]
    eigenvalue = eigenvalue[idx]
    eigenvector = eigenvector[:,idx]

    for i in range(0,m1):
        ce = 1.0
        if np.fabs(eigenvector[0][i]) + np.fabs(eigenvector[1][i]) > tol2:
            ellipse2d[i][0] = RAD2DEG * np.arctan2(ce * eigenvector[1][i], -ce * eigenvector[0][i])
        if (ellipse2d[i][0] < 0.0):
            ellipse2d[i][0] += 360.0
        ellipse2d[i][2] = np.sqrt(fac * max(eigenvalue[i], 0.0))

    return ellipse2d

if __name__ == '__main__':
    major = {'length':74.7,
             'dip':0,
             'azimuth':272,
             'rotation':155}
    minor = {'length':3.1,
             'dip':float('nan'),
             'azimuth':float('nan')}
    intermediate = {'length':8.9,
                    'dip':float('nan'),
                    'azimuth':float('nan')}
    axdict = {'major':major,'minor':minor,'intermediate':intermediate}
    axdict2 = getEllipsoid(axdict)

    print 'Minor Azimuth: %i' % int(axdict2['minor']['azimuth'])
    print 'Minor Dip: %i' % int(axdict2['minor']['dip'])
    print
    print 'Intermediate Azimuth: %i' % int(axdict2['intermediate']['azimuth'])
    print 'Intermediate Dip: %i' % int(axdict2['intermediate']['dip'])

    nphases = 50
    depthFixed = False
    std = 0.67
    minor = [axdict2['minor']['azimuth'],axdict2['minor']['dip'],axdict2['minor']['length']]
    inter = [axdict2['intermediate']['azimuth'],axdict2['intermediate']['dip'],axdict2['intermediate']['length']]
    major = [axdict2['major']['azimuth'],axdict2['major']['dip'],axdict2['major']['length']]
    ellipse3d = np.array([minor,inter,major])
    ellipse2d = errcon(nphases,depthFixed,std,ellipse3d)

    print ellipse3d
    print
    print ellipse2d
    
        
    
    
