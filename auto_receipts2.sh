#!/bin/bash

successes=0
fails=0

echo -n "Password:"
read -s PASSWORD
echo

##################################################################

# python outputs: 

# 0 = success; all purchases registered
# 1 = fail; unforseen error
# 2 = success; unregistered purchases saved as a dataframe somehow
# 3 = fail; unable to read the receipt

##################################################################

for receipt in ./receipt_pdfs/20??-??-??T??_??_??.pdf
do
 echo
 echo "Registering: $receipt"
 ./receipt2.py "$receipt" "$PASSWORD"
 result=$?
 if [ $result -eq 0 ]; then
  echo "Successfully registered $receipt. Deleting file."
  ((successes++))
  #delete file
 elif [ $result -eq 1 ]; then
  echo "Failed to register $receipt."
  ((fails++))
 elif [ $result -eq 2 ]; then
  echo "Partly registered $receipt."
  ((fails++))
  name=$(echo $receipt | cut -c 16-34)
  mkdir "$name"
  mv .temp_csv/* "$name/"
  mv "$receipt" "$name/"
  mv "$name" ./CSV_receipt/
 elif [ $result -eq 3 ]; then
  echo "Failed to register $receipt."
  ((fails++))
 else
  echo "Exiting script..."
  exit 1
 fi
 exit 1
done

echo 
echo "Successfully registered: $successes receipt(s)"
echo "Failed to register:      $fails receipt(s)"
