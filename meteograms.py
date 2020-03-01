#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import os
HOME = os.getenv('HOME')

import tool
import datetime as dt
import numpy as np
import numeric as num
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from colormaps import WindSpeed
import matplotlib.colors as colors
mpl.rcParams['grid.linestyle'] = 'dotted'

UTCshift = dt.datetime.now()-dt.datetime.utcnow()
UTCshift = round(UTCshift.total_seconds()/3600)
# UTCshift = dt.timedelta(hours = round(UTCshift.total_seconds()/3600))


import json
def get_meteogram(P0,date,data_fol,grid_folder,terrain_folder,fname,N=0,
                                                              place_name=''):
   lon,lat = P0
   sc = tool.get_sc(date)
   limits = json.load( open('../RASPlots/limits.json') )['lims']
   doms,areas = [],[]
   for dom,lim in limits.items():
      lim = lim[sc]
      lons = sorted(lim[:2])
      lats = sorted(lim[-2:])
      areas.append( ((np.max(lons)-np.min(lons)) * (np.max(lats)-np.min(lats))) )
      if lons[0] < lon < lons[1] and lats[0] < lat < lats[1]:
         doms.append(dom)
   if len(doms) == 0:
      LG.critical('Point outside of domain')
      return False
   elif len(doms) ==1: dom = doms[0]
   elif len(doms) == 2:
      ind = np.argmin(areas)
      dom = doms[ind]
   year = date.year
   month = date.month
   day = date.day
   fol = f'{data_fol}/{dom}/{sc}/{year}/{month:02d}/{day:02d}'
   grids = f'{grid_folder}/{dom}/{sc}'
   terrain = f'{terrain_folder}/{dom}/{sc}'
   if len(place_name)>0: title = f'{place_name} {date}'
   else: title = f'({lat:.2f},{lon:.2f}) {date}'
   plot_meteogram(lon,lat,fol,grids,terrain,dom,fname,N=0,title=title)
   return True

def plot_meteogram(lon,lat,fol,grids,terrain,dom,fname,N=0,title=''):
   """
   P0 in format (lon, lat)
   """

   lats = np.load(f'{grids}/lats.npy')
   lons = np.load(f'{grids}/lons.npy')

   P0 = lon,lat


   def get_ground(fol,P):
      lats = np.load(f'{fol}/lats.npy')
      lons = np.load(f'{fol}/lons.npy')
      hasl = np.load(f'{fol}/hasl.npy')
      dists = num.dists(lons,lats,P0)
      closest_index = np.unravel_index(np.argmin(dists),dists.shape)
      return hasl[closest_index]


   dists = num.dists(lons,lats,P0)
   closest_index = np.unravel_index(np.argmin(dists),dists.shape)
   P0 = lons[closest_index], lats[closest_index]
   real_point = list(reversed(P0))

   ground = get_ground(terrain,P0)

   if N>0:
      patch = [(closest_index[0]-N,closest_index[0]+N+1),
               (closest_index[1]-N,closest_index[1]+N+1)]
      weights = dists_matrix[patch[0][0]:patch[0][1],patch[1][0]:patch[1][1]]
      weights = 1/(weights+0.1)
      weights *= weights
      weights = np.tanh(weights)
   else:
      patch = [(closest_index[0],closest_index[0]+1), 
                (closest_index[1],closest_index[1]+1)]
      weights = None


   def get_value_err(M,closest,weights):
      N = 0  # closest point
      patch = [(closest[0]-N, closest[0]+N+1),
               (closest[1]-N, closest[1]+N+1)]
      M0 = M[patch[0][0]:patch[0][1],patch[1][0]:patch[1][1]]
      M0 = np.average(M0,weights=weights)
      N = 1  # neighbors
      patch = [(closest[0]-N, closest[0]+N+1),
               (closest[1]-N, closest[1]+N+1)]
      MN = M[patch[0][0]:patch[0][1],patch[1][0]:patch[1][1]]
      MN = np.average(MN,weights=weights)
      return M0,MN

   def get_data(fol,h,prop,closest,weights=None):
      fname = f'{fol}/{h*100:04d}_{prop}.data'
      M = np.loadtxt(fname,skiprows=4)
      return get_value_err(M,closest,weights)

   def get_data_mask(fol,h,prop,closest,weights=None):
      fname = f'{fol}/{h*100:04d}_{prop}'
      prop_base = f'{fname}.data'
      prop_pote = f'{fname}dif.data'
      prop_base = np.loadtxt(prop_base, skiprows=4)
      prop_pote = np.loadtxt(prop_pote, skiprows=4)
      null = 0. * prop_base
      M = np.where(prop_pote>0,prop_base,null)
      return get_value_err(M,closest,weights)

   H = []
   sfcwindspd,sfcwinddir = [],[]
   bltopwindspd,bltopwinddir = [],[]
   hbl,hbl_err = [],[]
   # hwcrit = []
   wstar = []
   rain = []
   dwcrit, dwcrit_err = [],[]
   zsfclcl,zsfclcl_err = [],[]
   zblcl,zblcl_err = [],[]
   for h in range(8,19):   # UTC hours
      H.append(h+UTCshift)
      s,_ = get_data(fol,h,'sfcwindspd',closest_index)
      sfcwindspd.append(s*3.6)
      d,_ = get_data(fol,h,'sfcwinddir',closest_index)
      sfcwinddir.append(d)
      s,_ = get_data(fol,h,'bltopwindspd',closest_index)
      bltopwindspd.append(s*3.6)
      d,_ = get_data(fol,h,'bltopwinddir',closest_index)
      bltopwinddir.append(d)
      hg,e = get_data(fol,h,'hbl',closest_index)
      hbl.append(hg)
      hbl_err.append(abs(hg-e)/2)
      # hwcrit.append(get_data(fol,h,'hwcrit',patch))
      d,e = get_data(fol,h,'dwcrit',closest_index)
      dwcrit.append(d+ground)
      dwcrit_err.append(abs(d-e)/2)
      r,_ = get_data(fol,h,'rain1',closest_index)
      rain.append(r)
      w,_ = get_data(fol,h,'wstar',closest_index)
      wstar.append(s)
      z,e = get_data_mask(fol,h,'zsfclcl',closest_index)
      zsfclcl.append(z)
      zsfclcl_err.append(abs(z-e)/2)
      z,e = get_data_mask(fol,h,'zblcl',closest_index)
      zblcl.append(z)
      zblcl_err.append(abs(z-e)/2)

   sfcU,sfcV = [],[]
   for S,D in zip(sfcwindspd,sfcwinddir):
      sfcU.append( -np.sin(np.radians(D)) )
      sfcV.append( -np.cos(np.radians(D)) )
   bltopU,bltopV = [],[]
   for S,D in zip(sfcwindspd,sfcwinddir):
      bltopU.append( -np.sin(np.radians(D)) )
      bltopV.append( -np.cos(np.radians(D)) )

   thermal_color = (0.90196078,1., 0.50196078)
   thermal_color1 = (0.96862745, 0.50980392, 0.23921569)
   terrain_color = (0.78235294, 0.37058824, 0.11568627)


   rect = patches.Rectangle((0,0),24,ground,facecolor=terrain_color,zorder=90)
   COLOR_back = 'white'
   COLOR = 'black'
   mpl.rcParams['text.color'] = COLOR
   mpl.rcParams['axes.labelcolor'] = COLOR
   mpl.rcParams['axes.facecolor'] = COLOR_back
   mpl.rcParams['savefig.facecolor'] = COLOR_back
   mpl.rcParams['xtick.color'] = COLOR
   mpl.rcParams['ytick.color'] = COLOR
   mpl.rcParams['axes.edgecolor'] = COLOR
   fig, ax = plt.subplots()
   ax.text(8,ground-200,f'GND:{int(ground)}m',zorder=100)
   sfc_info = ground + 30
   cb = ax.quiver(H,[sfc_info for _ in H],
                  sfcU, sfcV, sfcwindspd,
                  linewidth=1, scale=22,
                  norm=colors.Normalize(vmin=0,vmax=56),
                  headaxislength=3,
                  headlength=3.5,
                  headwidth=3,
                  edgecolor='k',
                  cmap = WindSpeed,
                  pivot='middle',zorder=99)
   for h,v in zip(H,sfcwindspd):
      ax.text(h-0.3,sfc_info+40,f'{v:.1f}',zorder=100,bbox=dict(edgecolor='none',facecolor='white', alpha=0.6))
   wind_info = np.where(hbl>sfc_info+150,hbl,-1e9)
   cb = ax.quiver(H,wind_info, bltopU,bltopV, bltopwindspd,
                  linewidth=1, scale=22,
                  norm=colors.Normalize(vmin=0,vmax=56),
                  headaxislength=3,
                  headlength=3.5,
                  headwidth=3,
                  edgecolor='k',
                  cmap = WindSpeed,
                  pivot='middle',zorder=99)
   for h,v,wi in zip(H,bltopwindspd,wind_info):
      ax.text(h-0.3,wi+40,f'{v:.1f}',zorder=100,bbox=dict(edgecolor='none',facecolor='white', alpha=0.6))
   cb = fig.colorbar(cb, orientation='horizontal')
   cb.set_label('Wind (km/h)')
   error_kw = {'width':2,'capsize':4.0, 'alpha':0.3}
   ax.bar(H,hbl,yerr=hbl_err,width=0.9,color=thermal_color,zorder=0,
                    error_kw=error_kw)
   col1 = np.array([255,191,128])/255
   col2 = np.array([204,41,0])/255
   wstar = np.array(wstar)
   wstar_norm = (wstar-np.min(wstar))/(np.max(wstar)-np.min(wstar))
   w_colors = [col2*c/col1 for c in wstar_norm]
   ax.bar(H,dwcrit,color=thermal_color1,yerr=dwcrit_err,width=0.7,zorder=1,
                   error_kw=error_kw)
   ax.bar(H,90,bottom=zsfclcl,width=1.05,color='gray',zorder=1,
                    error_kw=error_kw)
   ax.bar(H,90,bottom=zblcl,width=1.05,color='k',zorder=1,
                    error_kw=error_kw)
   rain = np.array(rain)
   rain = np.where(rain>=0.75,1,0)
   ax.bar(H,ground+90*rain,width=1.05,color='C0',zorder=10)
   ax.add_patch(rect)
   ax.set_ylim([ground-250,max([2500,1.2*max(hbl)])])
   ax.set_xlabel('Time')
   ax.set_ylabel('Height above sea level (m)')
   if len(title)>0:
      ax.set_title(title)
   fig.tight_layout()
   fig.savefig(fname)

# if __name__ == '__main__':
#    # Embalse Monda
#    P0 = -3.662435,40.790458   # Lon, Lat

#    ## Segovia
#    ## P0 = -4.140895,40.939294   # Lon, Lat


#    grids = '../RASPlots/grids/d2/SC2'
#    lats = np.load(f'{grids}/lats.npy')
#    lons = np.load(f'{grids}/lons.npy')
#    lon = np.random.uniform(np.min(lons),np.max(lons))
#    lat = np.random.uniform(np.min(lats),np.max(lats))
#    P0 = lon,lat

#    # # Arcones
#    # # P0 = -3.700872,41.088520   # Lon, Lat
#    # P0 = -3.709228,41.097472   # Lon, Lat

#    # # # Pedro Bernardo
#    # # P0 = -4.889601,40.220667

#    # # # Piedrahita
#    # P0 = -5.33,40.46

#    # # Palomaret
#    # P0 = -0.61, 38.4
#    P0 = -0.676081,38.486679

#    # # Maigmo
#    # P0 = -0.631212,38.501661

#    data_fol = f'{HOME}/Documents/RASP/DATA'
#    hoy = dt.datetime.now().date() # + dt.timedelta(days=1)
#    grids =   f'{HOME}/CODES/RASPlots/grids'
#    terrain = f'{HOME}/CODES/RASPlots/terrain'
#    get_meteogram(P0,hoy,data_fol,grids,terrain,'test.png')
