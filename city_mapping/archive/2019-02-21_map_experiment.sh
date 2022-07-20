#!/usr/bin/env bash

# Creating a 'Canute-style map' file from a given location string.
# Left side of each page is a key, right side is a grid of letters a--i,
# representing the streets in the key. Map progresses Eastwards with 
# each page (if there are multiple pages, and in absence of a better 
# file format for the handling of 2D spacial info on the Canute).

# Basic rounding function. Args: number, decimal places.
round() {
  printf "%.${2}f" "${1}"
}

# First take the user's string and get long. and lat. from Google.

# Then create the bounding box: N=(Lat.+(0.001*4)); S=(Lat.-(0.001*5));
# E=(Lon.+(0.001*10)); W=(Lon.-(0.001*10)).
# This is currently biased towards East of Greenwich, North of Equator.

# Download all the named highways for that region from Open Street Map.

# The download all the nodes for that region from Open Street Map.
# It would be smarter, faster and neater to get all the nodes needed 
# from the ways, above, and only request those, but one thing at a time.


# Now for an experiment, before writing the thing proper;
# Project all the nodes onto half the Canute's display area (20x9).

# OSM uses SWNE, but we are using shredded wheat, for sanity's sake.
# Note also we have made the lon. numbers positive, as a cheat.
# Note that this location is in Bedmins., West of Greenw., so inverted.
bounds=( "51.44355" "2.59192" "51.44251" "2.59442" )

numnodes=$( jq ".elements | length" nodes.json )

echo "Number of nodes:" $numnodes


# Create blank BRF file to write to.
rm page.brf
i=0
while [ $i -lt 9 ]; do
	echo "                                        " >> page.brf
let i=i+1
done

j=0
while [ $j -lt $numnodes ]; do

	# Includes nasty neg. to pos conversion.
	lat=$( jq ".elements[$j].lat" nodes.json | sed -e 's/"//g' | sed -e 's/\-//g' )
	lon=$( jq ".elements[$j].lon" nodes.json | sed -e 's/"//g' | sed -e 's/\-//g' )

	line=$( round $( echo "( ${lat} - ${bounds[2]} ) * 10000" | bc | sed -e 's/\-//g' ) 0 )
	cell=$( round $( echo "( ${lon} - ${bounds[3]} ) * 10000" | bc | sed -e 's/\-//g' ) 0 )
	
	# I'm too lazy to work out why I need to add one...
	let line=line+1
	let cell=cell+1

	# Draw an 'a' in the map for the node.
	sed -i "${line}s/./a/${cell}" page.brf

	cat page.brf
	echo "----------------------------------------"

	let j=j+1 

done

