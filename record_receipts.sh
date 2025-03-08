#!/bin/bash

shopt -s nullglob

successes=0
fails=0
saved_csvs=0
registered_edits=0
already_processed=0

./src/prompt_password.py
result=$?

if [ $result -eq 2 ]; then
 read -s -p "password:" DB_PASSWORD
 echo
 export DB_PASSWORD
fi

for receipt in ./data/receipt_pdfs/20??-??-??T??_??_??.pdf
do
 ./src/repetition_check.py "$receipt"
 new_receipt=$?
 if [ $new_receipt -eq 1 ]; then
  echo "Unexpected error."
  exit 1
 elif [ $new_receipt -eq 2 ]; then
  ((already_processed++))
  continue
 elif [ $new_receipt -eq 3 ]; then
  echo "Error: Unable to connect to psql server. Possibly wrong password. Try again."
  exit 1
 else
  if compgen -G "./data/archive${receipt:19:20}_*.csv" > /dev/null; then
   ((already_processed++))
   continue
  fi
 fi
 echo
 echo "Reading: $receipt"
 ./src/read_receipt.py "$receipt"
 result=$?
 if [ $result -eq 0 ]; then
  echo "Successfully read: $receipt. Beginning registration."
  csv="./data/temp${receipt:19:20}.csv"
  ./src/log_csv.py "$csv"
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
 elif [ $result -eq 3 ]; then
  echo "Cancelled by user."
  ((fails++))
 elif [ $result -eq 4 ]; then
  echo "Receipt not properly read. CSV saved in archive for editing."
  ((saved_csvs++))
  ((fails++))
 fi
done

for edit in ./data/archive/20??-??-??T??_??_??_edit.csv
do
 echo
 echo "registering $edit"
 ./src/log_csv.py "$edit"
 result=$?
 if [ $result -eq 0 ]; then
  reg="${edit::34}_reg.csv"
  mod="${edit::34}_mod.csv"
  incorrect="${edit::34}_incorrect.csv"
  pdf="./data/receipt_pdfs/${edit:15:19}.pdf"
  rm "$edit"
  if [ -f "$reg" ]; then
   rm "$reg"
  fi
  if [ -f "$mod" ]; then
   rm "$mod"
  fi
  if [ -f "$pdf" ]; then
   rm "$pdf"
  fi
  if [ -f "$incorrect" ]; then
   rm "$incorrect"
  fi
  ((registered_edits++))
  ((already_processed--))
 fi
done

echo
echo "Successfully registered: $successes receipt(s)"
echo "Failed to register:      $fails receipt(s)"
echo
if [ $saved_csvs -gt 0 ]; then
 echo "Saved $saved_csvs receipt(s) as CSV to be reviewed."
fi
if [ $registered_edits -gt 0 ]; then
 echo "Registered $registered_edits edit(s) from archive."
fi
if [ $already_processed -gt 0 ]; then
 echo "$already_processed PDFs have already been fully, or partially, processed."
fi
echo

#clear temporary directory to keep things tidy
rm -f ./data/temp/*