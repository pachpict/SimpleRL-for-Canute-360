#!/usr/bin/env bash

# Creating a 'Canute-style map' file from a given location string.

# Basic rounding function. Args: number, decimal places.
round() {
	printf "%.${2}f" "${1}"
}

# Bresenham's line drawing algorithm. Thanks to:
# https://rosettacode.org/wiki/Bitmap/Bresenham%27s_line_algorithm#bash
function line {
	x0=$1
	y0=$2
	x1=$3
	y1=$4
#	z=$5

	if (( x0 > x1 ))
	then
		(( dx = x0 - x1 ))
		(( sx = -1 ))
	else
		(( dx = x1 - x0 ))
		(( sx = 1 ))
	fi
 
	if (( y0 > y1 ))
	then
		(( dy = y0 - y1 ))
		(( sy = -1 ))
	else
		(( dy = y1 - y0 ))
		(( sy = 1 ))
	fi
 
	if (( dx > dy ))
	then
		(( err = dx ))
	else
		(( err = -dy ))
	fi
	(( err /= 2 ))
	(( e2 = 0 ))
 
	while :
	do
		newline=$y0
		newcell=$x0
		if (( newline < 1 )); then
			let newline=1
		fi
		if (( newline > $maplines )); then
			let newline=$maplines
		fi
		if (( newcell < 1 )); then
			let newcell=1
		fi
		if (( newcell > $mapcells )); then
			let newcell=$mapcells
		fi

	
		# A lot of the following is hang-over from word-search and should be cut
		if ( grep -Fq "${newline},${newcell},${highwayname}" /dev/shm/highway-locations.csv )
		then
			# This highway is already drawn here.
			let nonsense=True
		else
			if ( grep -Fq "${newline},${newcell}" /dev/shm/highway-locations.csv )
			then
				# Another highway is already drawn here so back-paint the previous cell as an intersection.
				if (( ${oldline} != -1 && ${oldcell} != -1 ))
				then
					sed -i "${oldline}s/${z}/ /${oldcell}" /dev/shm/map.brf
					sed -i "${oldline}s/${z}/ /$((oldcell+1))" /dev/shm/map.brf
				fi
			else
				# Drawing on this cell for the first time
				if (( ${oldline} == -1 && ${oldcell} == -1 ))
				then
					# This must be start of the highway.
					sed -i "${newline}s/./ /${newcell}" /dev/shm/map.brf
					sed -i "${newline}s/./ /$((newcell+1))" /dev/shm/map.brf
					echo "${newline}","${newcell}","${highwayname}" >> /dev/shm/highway-locations.csv
					echo "${newline}","$((newcell+1))","${highwayname}" >> /dev/shm/highway-locations.csv
				else
					# Otherwise paint whitespace.
					z=$( echo ${highwaymarks:${hwmi}:1} )
					hwmi=$((hwmi+1))
					if (( ${hwmi} == ${hwml} ))
					then
						hwmi=0
					fi
					sed -i "${newline}s/./ /${newcell}" /dev/shm/map.brf
					sed -i "${newline}s/./ /$((newcell+1))" /dev/shm/map.brf
					echo "${newline},${newcell},${highwayname}" >> /dev/shm/highway-locations.csv
					echo "${newline}","$((newcell+1))","${highwayname}" >> /dev/shm/highway-locations.csv
				fi
				oldline=${newline}
				oldcell=${newcell}
			fi
		fi

		(( x0 == x1 && y0 == y1 )) && return
		(( e2 = err ))
		if (( e2 > -dx ))
		then
			(( err -= dy ))
			((  x0 += sx ))
		fi
		if (( e2 < dy ))
		then
			(( err += dx ))
			((  y0 += sy ))
		fi
	done
}

# Creating the blank map.
# Two cell margin needed for cut-off..?
rm map.brf highway-locations.csv /dev/shm/highway-locations.csv /dev/shm/map.brf
mapcells=400
maplines=120
filelines=0
date=$(date '+%Y%m%d-%H%M%S');
while [ ${filelines} -lt ${maplines} ]; do
	printf "%-${mapcells}s\n" "=" | sed 's/ /=/g' >> /dev/shm/map.brf
	let filelines=filelines+1
done
touch /dev/shm/highway-locations.csv

# Set map scale.
# Have a Mercator projection problem here, different 
# ratios needed for different lats
# London ratio: 3.5:2
scalex=17500
scaley=10000

# Location bounding box.
# OSM uses SWNE, but we are using shredded wheat, for sanity's sake.
nb=51.4606970
eb=-2.5821023 
sb=51.4484943
wb=-2.6039797

# Download all the named highways for that region from Open Street Map.
# Create wider catchment for nodes for those that go off edge of display.
# Comment out whenever poss when testing due to OSM server limitations.
#curl -g "https://overpass-api.de/api/interpreter?data=[out:json];way['building']['name']($sb,$wb,$nb,$eb);out%20geom;" > buildings.json
curl -g "https://overpass-api.de/api/interpreter?data=[out:json];way[highway~'^(motorway|trunk|primary|secondary|tertiary|unclassified|(motorway|trunk|primary|secondary)_link)$']['name']($sb,$wb,$nb,$eb);out%20geom;" > highways.json
#curl -g "https://overpass-api.de/api/interpreter?data=[out:json];way['highway']['name']($sb,$wb,$nb,$eb);out%20geom;" > highways.json

# Loop through the highways
rm highway-locations.csv
j=0
numhighways=$( jq '.elements | length' highways.json )
if (( $numhighways > 9999 )); then
	let numhighways=9999
fi

while [ $j -lt $numhighways ]; do

	highway=$( jq ".elements[${j}]" highways.json)

	highwayname=$( echo ${highway} | jq ".tags.name" | sed 's/"//g')
	highwaymark=$( echo ${highwayname:0:1} | tr '[:upper:]' '[:lower:]')
	highwaymarks=$( echo "${highwayname} " | tr '[:upper:]' '[:lower:]' | sed 's/ street/ st/g'| sed 's/ lane/ ln/g' | sed 's/ avenue/ av/g' | sed 's/ road/ rd/g' | sed 's/ square/ sq/g' | sed 's/ /_/g')
	hwml=$( echo ${#highwaymarks} )
	hwmi=0
	let oldline=-1
	let oldcell=-1

	echo "${j}/${numhighways}" ${highwayname}

	numgeoms=$( echo ${highway} | jq ".geometry | length" )
	k=0
	while [ $k -lt $numgeoms ]; do

		geomlat=$( echo ${highway} | jq ".geometry[${k}] | .lat" )
		geomlon=$( echo ${highway} | jq ".geometry[${k}] | .lon" )

		# This is lazy stuff. It will probably fold any
		# map that falls on the equator or meridian over
		# on itself.
		if (( $( round $geomlat 0 ) > 0 )); then # North of the equator
			curline=$( round $( echo "( ${nb} - ${geomlat} ) * ${scaley}" | bc ) 0 )
		else # South of the equator
			curline=$( round $( echo "( ${geomlat} - ${sb} ) * ${scalex}" | bc ) 0 )
		fi
		if (( $( round $geomlon 0 ) > 0 )); then # East of Greenwich Meridian.
			curcell=$( round $( echo "( ${eb} - ${geomlon} ) * ${scaley}" | bc ) 0 )
		else # West of Greenwich Meridian.
			curcell=$( round $( echo "( ${geomlon} - ${wb} ) * ${scalex}" | bc ) 0 )
		fi

		# So, idea is, give a one-cell margin around the
		# edge so lines can be plotted to these edge
		# geoms. Then cut the edge cells off. Is hacky.
		if (( $curline < 1 )); then
			let curline=1
		fi
		if (( $curline > $maplines )); then
			let curline=$maplines
		fi
		if (( $curcell < 1 )); then
			let curcell=1
		fi
		if (( $curcell > $mapcells )); then
			let curcell=$mapcells
		fi

		# Draw a line between geoms.
		if (( $k > 0 )); then
			line $prevcell $prevline $curcell $curline 
		fi
		# Save the old values so we can plot a line
		prevline=$curline
		prevcell=$curcell

		let k=k+1
	done

	let j=j+1
done

cp /dev/shm/map.brf ./map.brf
cp /dev/shm/highway-locations.csv ./highway-locations.csv
rm /dev/shm/highway-locations.csv /dev/shm/map.brf

echo ${date} >> archive/maps.brf
cat map.brf >> archive/maps.brf
#cat map.brf

exit

