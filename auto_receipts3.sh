#!/bin/bash

successes=0
fails=0
iterations=0
saved_csvs=0

echo -n "Password:"
read -s PASSWORD
echo

for receipt in ./data/receipt_pdfs/20??-??-??T??_??_??.pdf
do
 ./src/repetition_check.py "$receipt" "$PASSWORD"
 new_receipt=$?
 if [ $new_receipt -eq 1 ]; then
  echo "Unexpected error."
  exit 1
 elif [ $new_receipt -eq 2 ]; then
  continue
 elif [ $new_receipt -eq 3 ]; then
  echo "Error: Unable to connect to psql server. Possibly wrong password. Try again."
  exit 1
 fi
 echo
 echo "Reading: $receipt"
 ./src/read_receipt.py "$receipt"
 result=$?
 if [ $result -eq 0 ]; then
  echo "Successfully read: $receipt. Beginning registration."
  csv="./data/temp${receipt:19:20}.csv"
  ./src/log_csv.py "$csv" "$PASSWORD"
  log_result=$?
  if [ $log_result -eq 0 ]; then
   echo "Success!"
   ((successes++))
   rm "$csv"
   rm "$receipt"
  elif [ $log_result -eq 1 ]; then
   echo "Unexpected error: unable to log CSV"
   ((fails++))
  elif [ $log_result -eq 2 ]; then
   echo "Saved CSVs for manual editing."
   ((saved_csvs++))
  elif [ $log_result -eq 3 ]; then
   echo "Error: Unable to connect to psql server. Possibly wrong password. Try again."
   exit 1
  fi
 elif [ $result -eq 1 ]; then
  echo "Unexpected error: receipt unable to be read."
  ((fails++))
 elif [ $result -eq 2 ]; then
  echo "Error: read empty receipt. Double checking receipt, and possibly adjusting script, could be warranted."
  ((fails++))
 fi
 ((iterations++))
done

for edit in ./data/archive/20??-??-??T??_??_??_edit.csv
do
 echo
 echo registering "$edit"
 ./src/log_csv.py "$edit" "$PASSWORD"
 result=$?
 if [ $result -eq 0 ]; then
  reg="${edit::34}_reg.csv"
  mod="${edit::34}_mod.csv"
  pdf="./data/receipt_pdfs/${edit:15:19}.pdf"
  rm "$edit"
  rm "$reg"
  if [ test -f "$mod" ]; then
   rm "$mod"
  fi
  if [ test -f "$pdf" ]; then
   rm "$pdf"
  fi
 fi 
done

echo
echo "Successfully registered: $successes receipt(s)"
echo "Failed to register:      $fails receipt(s)"
echo
if [ $saved_csvs -gt 0 ]; then
 echo "Saved $saved_csvs receipts as CSV to be reviewed"
fi

#clear temporary directory to keep things tidy
rm ./data/temp/*