#!/bin/bash

echo "Ready your receipt. Make sure to leave some space on top and keep the date visible. Press 'Enter' when ready."

read

screencapture -s ~/reciept/new_receipt.png
open ~/reciept/new_receipt.png

~/reciept/reciept.py

osascript -e 'tell application "Preview" to close front window'

rm ~/reciept/new_receipt.png