SUBROUTINE deg2rad(x,x_rad)
implicit none
 REAL*8:: x, x_rad
 REAL*8,PARAMETER:: pi=4.d0*atan(1.d0)
 x_rad = x * pi/180
END SUBROUTINE deg2rad

SUBROUTINE GPSdistance(n,P1,P2,D)
! Calculate distance (in kilometers) between two points given as
!    (lon, lat) pairs based on Haversine formula:
!          http://en.wikipedia.org/wiki/Haversine_formula
!    R0 = 6371km is the radious of the earth
implicit none
 INTEGER:: n
 REAL*8,PARAMETER:: R0 = 6371
 REAL*8,DIMENSION(n),intent(in):: P1,P2
 REAL*8,intent(out):: D
 REAL*8:: P1rad_lon, P1rad_lat, P2rad_lon, P2rad_lat
 REAL*8:: D_lon, D_lat
 REAL*8:: aux
CALL deg2rad(P1(1),P1rad_lon)
CALL deg2rad(P1(2),P1rad_lat)
CALL deg2rad(P2(1),P2rad_lon)
CALL deg2rad(P2(2),P2rad_lat)
D_lon = P2rad_lon - P1rad_lon
D_lat = P2rad_lat - P1rad_lat
aux = SIN(D_lat/2)**2 + COS(P1rad_lat) * COS(P2rad_lat) * SIN(D_lon/2)**2
aux = 2 * ATAN2(SQRT(aux), SQRT(1-aux))
D = R0*aux
END SUBROUTINE GPSdistance

SUBROUTINE dists(nx,ny,X,Y,P0,D_matrix)
! Given 2 grids of X & Y coordinates, return distance of each node to a point
implicit none
 INTEGER:: nx, ny
 REAL*8,DIMENSION(nx,ny),intent(in):: X,Y
 REAL*8,DIMENSION(2),intent(in)::P0
 REAL*8,DIMENSION(nx,ny),intent(out):: D_matrix
 REAL*8,DIMENSION(2)::P
 INTEGER:: i,j
 REAL*8::d
do i = 1,nx
   do j = 1,ny
      P(1) = X(i,j)
      P(2) = Y(i,j)
      CALL GPSdistance(2,P,P0, d)
      D_matrix(i,j) = d
    end do
end do
END SUBROUTINE dists
