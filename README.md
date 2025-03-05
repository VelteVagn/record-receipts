# Receipt Recorder
This is a programme with the purpose of reading receipts and logging the results in a psql table. Product purchases will be divided into amount, total price and category. 

## Table of Contents
- [Installation](#installation)
- [Usage](#usage)
- [License](#license)
- [Notes](#notes)

## Installation
If you haven't already, install [PostgreSQL](https://www.postgresql.org/download/) and [Conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html).

Clone and navigate to the repository:
```bash
$ git clone https://github.com/...........
$ cd reciept
```

Create and activate Conda environment:
```bash
$ conda env create -f environment.yml
$ conda activate base
```

Change name of .env.example to .env:
```bash
$ cp .env.example .env
```

Open PostgreSQL:
```bash
$ psql -U postgres -d
```
NOTE: if you have edited the contents of .env, make sure the user matches DB_USER, i.e., if DB_USER=username, then write 
```bash
$ psql -U username -d
```
in the terminal instead. 

Create the database:
```sql
$ CREATE DATABASE receipts;
```
Again, make sure the database name matches the name in .env.
Lastly, initialise the tables:

```bash
$ psql -U postgres -d receipts -f env/init.sql
```

## Usage
Put the receipts that are to be scanned and logged into the directory data/receipt_pdfs. For testing purposes, copy the sample receipts to data/receipt_pdfs:
```bash
$ cp data/sample_receipts/* data/receipt_pdfs/
```

Make record_receipts.sh executable:
```bash
$ chmod +x record_receipts.sh
```

Execute record_receipts.sh to begin registering the receipts in data/receipt_pdfs and follow the instructions:
```bash
$ ./record_receipts.sh
```

If parts of the receipt was saved, CSVs will be saved in data/archive. Manually edit the file ending in _mod.csv, and rename it by changing _mod.csv to _edit.csv. Next time record_receipts.sh is run, the edits will be registered, and the corresponding CSVs and PDF will be deleted.  

## License
This project is licensed under the [GNU General Public License](COPYING).

## Notes
Here are some final notes regarding choices made, background, etc.

### Willy:s
Willy:s is a Swedish grocery store, owned by Axfood. Meanwhile the project is written specifically for digital receipts from Willy:s, it shouldn't pose too much of a challenge to tailor it for other stores instead. 

### Pytesseract
The use of pytesseract to read the receipt might look weird, but for whatever reason, the Willy:s receipts are formatted weirdly, so I could not find a better way to read the receipts. On the bright side, the use of OCR should make it possible to use the script on physical receipts as well as digital ones. 

### Purpose
The purpose of the project was mostly out of curiosity. I do not know if this could have any bigger purpose than that, but personally I have long wanted to know more specifically where the money goes when going to the grocery store. Maybe it could be possible to collect data to train an AI, but personally I wouldn't trust an AI to do my grocery shopping.

### Bash
Part of the motivation behind doing this project was to get more proficient in bash, so that I can install Linux for personal use. Of course, that means that this programme cannot easily be ported to Windows. However, most is python anyway, so it probably wouldn't be too big of a hassle if someone felt the need to change that.
