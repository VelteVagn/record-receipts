#!/bin/bash

successes=0
fails=0
iterations=0

echo -n "Password:"
read -s PASSWORD
echo

for receipt in ./receipt_pdfs/20??-??-??T??_??_??.pdf
do
 echo
 echo "Reading: $receipt"
 ./read_receipt.py "$receipt"
 result=$?
 if [ $result -eq 0 ]; then
  echo "Successfully read: $receipt. Beginning registration."
  csv="./csv${receipt:14:20}.csv"
  ./log_csv.py "$csv" "$PASSWORD"
  log_result=$?
  if [ $log_result -eq 0 ]; then
   echo "Success!"
   # DELETE CSV AND PDF!!!
  elif [ $log_result -eq 1 ]; then
   echo "Unexpected error: unable to log CSV"
  elif [ $log_result -eq 2 ]; then
   echo "Saved CSVs for manual editing."
  elif [ $log_result -eq 3 ]; then
   echo "Error: Unable to connect to psql server. Possibly wrong password. Try again."
   exit 1
  fi
 elif [ $result -eq 1 ]; then
  echo "Unexpected error: receipt unable to be read."
 elif [ $result -eq 2 ]; then
  echo "Error: read empty receipt. Double checking receipt, and possibly adjusting script, could be warranted."
 fi
done

#clear directory to keep things tidy
rm csv/*.csv