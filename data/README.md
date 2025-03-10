## archive:
Contains CSVs ending with _reg, _mod, _edit and _incorrect:
### reg
This is a CSV containing the registered groceries from the receipt. Together with its _mod file, it should contain the whole receipt. Meant to be used as reference when editing the _mod file.
### mod
This is a CSV containing the remaining groceries on the receipt, i.e., the groceries that have not been registered yet for whatever reason. Edit this file so that everything corresponds to the original receipt pdf (use the corresponding _reg file as reference). After editing, rename it to _edit so that it gets registered in the future.
### edit
This is a manually edited CSV containing groceries that have not been registered yet. When log_csv.py is run, the files ending in _edit will be registered. On success, all corresponding CSVs and PDFs will be deleted. 
### incorrect
CSVs that have the wrong price or amount registered. Compare it with the original PDF, edit and rename the file so that it ends with _edit, similar to what is described under _mod. 

## receipt_pdfs:
Contains PDFs of grocery receipts. This is where all input receipts should be stored for them to be registered when running read_receipt.py. 

## temp:
Contains temporarily stored files. Will be emptied automatically when running the script.

## sample_receipts:
Contains examples of receipts. Copy the contents over to ./receipt_pdfs to test the script:
```bash
$ cd data
$ cp sample_receipts/* receipt_pdfs
```