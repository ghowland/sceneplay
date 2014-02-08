#!/bin/bash

ffmpeg -y -f image2 -r 10 -i output/output_%06d.png -i data/music.wav -c:a aac -strict experimental -c:v libx264 output/out.m4v

open output/out.m4v 

