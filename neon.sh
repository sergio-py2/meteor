#!bash

RA=2.5
RB=7.0
RC=12.0

convert space_ship_raw.png \
	\( -clone 0 -channel RGBA -blur 0x0.5 -modulate 100,100 \) \
	\( -clone 0 -channel RGBA -blur 0x1.5 -modulate 100,100 \) \
	\( -clone 0 -channel RGBA -blur 0x$RA -modulate 100,100 \) \
	\( -clone 0 -channel RGBA -blur 0x$RA -modulate 100,100 \) \
	\( -clone 0 -channel RGBA -blur 0x$RA -modulate 100,100 \) \
	\( -clone 0 -channel RGBA -blur 0x$RA -modulate 100,100 \) \
	\( -clone 0 -channel RGBA -blur 0x$RB -modulate 100,100 \) \
	\( -clone 0 -channel RGBA -blur 0x$RB -modulate 100,100 \) \
	\( -clone 0 -channel RGBA -blur 0x$RB -modulate 100,100 \) \
	\( -clone 0 -channel RGBA -blur 0x$RB -modulate 100,100 \) \
	\( -clone 0 -channel RGBA -blur 0x$RB -modulate 100,100 \) \
	\( -clone 0 -channel RGBA -blur 0x$RC -modulate 100,100 \) \
	\( -clone 0 -channel RGBA -blur 0x$RC -modulate 100,100 \) \
	  -delete 0 -reverse -background none -flatten -resize 50% space_ship_neon.png