#!/bin/bash

open "$1"
#echo "Calculated total price: $2"
echo "press 'enter' to continue"
read
osascript -e 'tell application "Preview" to close front window'

