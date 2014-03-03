# Finding Eigen Values and Vectors for real symmetric matrices

from __future__ import division
import math
import numpy

# Error definitions
class MatrixError(Exception):
      pass

class DimensionError(Exception):
      pass

def jacobi(A, eps=1e-12):
    """This routine finds eigenvalues and -vectors for a symmetric matrix by a cyclic Jacobi rotation algorithm.
    @param A: A The matrix (NumPy array) whos eigenvalues and -vectors are to be determined.
    @keyword eps: The desired accuracy (zeroing limit).
    @return: [E, V, s] Numpy array of eigenvalues and of eigenvectors, as well as number of sweeps used.
    """
    [n,m] = A.shape
    #Error conditions
    if n != m:
       raise DimensionError('Error: Matrix must be quadratic')
    if (A != A.T).any():
       raise MatrixError('Error: Matrix must be symmetric')

    #Initialize
    A = A.astype('float64')   
    V = numpy.eye(n)                          #Initializing V as a idendity matrix
    s = 0                
    ssum = eps + 1   
       
    while ssum > eps:                         #Rotate until accuracy is reached
          for p in range(n):                  #Iterating above the diagonal
              for q in range(p+1,n):
                  if abs(A[p,q]) > eps:       #Rotate only if value is above eps
                     A,V = rotate(p,q,A,V)    #Rotation subroutine
                     s += 1                   #Update s
          ssum = 0
          for i,row in enumerate(A):          #summes the upper off diagonal elements in A to check if the sum is below eps
              ssum += sum(abs(row[i+1:]))     #the loop iterates over row indices and items of each row
  
    E = numpy.diag(A)                         #finds the eigenvalues from the diagonal of A
  
    return E, V, s

def rotate(p,q,A,V):
    """
    This subroutine performs Jacobi rotation on a matrix A, eliminating A[pq].
    @param p: indices of the element to be eliminated.
    @param q: indices of the element to be eliminated.
    @param A: The matrix to be diagonalised.
    @param V: The matrix of eigenvectors.
    @return: [A, V] Updated A and V matrices.
    """  
    n = A.shape[0]
    App, Aqq, Apq  = A[p,p], A[q,q], A[p,q]   #Initial values
    phi = 0.5*math.atan2(2*Apq, Aqq-App)      #Find the rotation value
    c, s = math.cos(phi), math.sin(phi)       #Calculate sin and cos

    #Update the matrix diagonal elements
    A[p,p] = c*c*App + s*s*Aqq - 2*s*c*Apq    
    A[q,q] = s*s*App + c*c*Aqq + 2*s*c*Apq
    A[p,q] = 0                                #This is zero by construction
    
 
    #Iterate over and update remaining off-diagonal elements
    for i in range(p):
        Aip, Aiq = A[i,p], A[i,q]
        A[i,p] = c*Aip - s*Aiq
        A[i,q] = c*Aiq + s*Aip
    
    for i in range(p+1,q):
        Api, Aiq = A[p,i], A[i,q]
        A[p,i] = c*Api - s*Aiq
        A[i,q] = c*Aiq + s*Api
  
    for i in range(q+1,n):
        Api, Aqi = A[p,i], A[q,i]
        A[p,i] = c*Api - s*Aqi
        A[q,i] = c*Aqi + s*Api
  
    #Update eigenvectors in matrix V
    for i in range(n):
        Vip, Viq = V[i,p], V[i,q]
        V[i,p] = c*Vip - s*Viq
        V[i,q] = s*Vip + c*Viq
  
    return A, V
