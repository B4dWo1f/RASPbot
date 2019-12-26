#!/bin/bash

rm test.png

SC='sc4+3'
hour='1200'
prop='hglider'
prop_vec='sfcwind'

sed -e "s/XXhourXX/$hour/" w2_"$SC"_vec_scal_template.svg | sed -e "s/XXpropXX/$prop/" | sed -e "s/XXprop_vecXX/$prop_vec/" > foo.svg

inkscape -b "#ffffff" -e test.png foo.svg

eog test.png
