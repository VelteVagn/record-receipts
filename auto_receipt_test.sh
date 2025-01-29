#!/bin/bash

successes=0
unforeseen_fails=0
empty_df=0
wrong_price=0
wrong_amount=0
zero_price=0
unavailable_price=0
unavailable_amount=0         # line 10
readonly DPI=150
                                    
# in nano seconds:
time_sum=0
success_time_sum=0
fastest_time=-1
fastest_success=-1

for receipt in ./receipt_pdfs/20??-??-??T??_??_??.pdf
do                                                              # line 20
 echo "Testing receipt: $receipt"
 output=$(./receipt_test.py "$receipt" "$DPI")
 result=$?
 iteration_time=$(echo "$output" | jq -r '.time')
 size=$(ls -1 receipt_pdfs | wc -l)
 if [ $result -eq 0 ]; then
  echo "Success!"
  ((successes++))
  success_time_sum=$((success_time_sum+iteration_time))                          # line 30
  if [[ "$iteration_time" < "$fastest_success" ||  "$fastest_success" -eq -1 ]]; then
   fastest_success=$iteration_time
  fi
 elif [ $result -eq 1 ]; then
  echo "Unforeseen error..."
  ((unforeseen_fails++))
 elif [ $result -eq 2 ]; then
  echo "Probably single purchase (empty data frame)"
  ((empty_df++))
 elif [ $result -eq 3 ]; then                             # line 40
  ((wrong_price++))
 elif [ $result -eq 4 ]; then
  ((wrong_amount++))
 elif [ $result -eq 5 ]; then
  ((zero_price++))
 elif [ $result -eq 6 ]; then
  ((unavailable_price++))
 elif [ $result -eq 7 ]; then
  ((unavailable_amount++))
 fi                                                            # line 50
 time_sum=$((time_sum+iteration_time))
 if [[ "$iteration_time" < "$fastest_time" ||  "$fastest_time" -eq -1 ]]; then
  fastest_time=$iteration_time
 fi
done

fails=$((empty_df+wrong_price+wrong_amount+zero_price+unavailable_price+unavailable_amount+unforeseen_fails))
average_time=$(( time_sum/size ))
if [[ "$successes" > 1 ]]; then
 average_success_time=$(( success_time_sum / successes ))        # line 60
else
 average_success_time="undefined"
fi

readonly RATIO=$(echo "scale=2; $successes / $size" | bc)

# convert nano seconds to seconds
readonly BILL=1000000000
stats=(time_sum average_time fastest_time fastest_success success_time_sum average_success_time)

for stat in "${stats[@]}"
do
 eval "$stat=\$(echo \"scale=2; \$$stat / $BILL\" | bc)"
done

echo
echo "TEST RESULTS:"
echo "Iterations:         $size"
echo "Total successes:          $successes"
echo "Total fails:              $fails"
echo "DPI:                      $DPI"
echo "Success rate:             $RATIO"                         # line 70
echo
echo "empty data frame:         $empty_df"
echo "wrong total price:        $wrong_price"
echo "wrong total amount:       $wrong_amount"
echo "total price is 0:         $zero_price"
echo "receipt price not found:  $unavailable_price"
echo "receipt amount not found: $unavailable_amount"
echo "-----------------------------------------------------"
echo "TIME RESULTS:"
#echo "Fastest run:            $fastest_time seconds"              # line 80
echo "Total time:             $time_sum seconds"
echo "Average time:           $average_time seconds"
echo
echo "Fastest run  (success): $fastest_success seconds"
echo "Total time   (success): $success_time_sum seconds"
echo "Average time (success): $average_success_time seconds"







