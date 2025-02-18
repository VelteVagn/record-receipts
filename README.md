# Receipt logger

## Description
This is a personal project with the purpose of automating the process of registering grocery receipts on a detailed level. First and foremost out of curiousity, but also to see where the money goes to make smarter shopping decisions in the future.

### Use
As mentioned, the point is to register grocery receipts. It is specifically tailored to the digital receipts (in pdf-format) from the Swedish grocery store chain Willy:s (owned by Axfood). Thus running the program on receipts from other stores will likely not work without tweaking the code. The program will run through all receipts saved in the repository named receipt_pdfs. First it will convert the pdf to a png, and then extract the text using pytesseract. Then it structures the contents into a table with columns of name, amount and price, for every purchased product on the receipt. The table will then be saved as a csv. 

Now every product purchase will be registered in a psql table. For every product that has not been registered previously, the user will be prompted to choose a category that the product fits into. Thus in the beginning, the programme will be slow and prompt the user for input a lot. But as the psql table increases in size, the amount of times a new product must be registered decreases and so the programme will become more and more independent of the user.  

### Purpose
The purpose of the project is first and foremost out of curiousity and to teach myself more programming. Additionally, I wanted to try to utilise Bash and psql and become proficient in navigating the terminal and using git. When I have previously described this project to people, I've usually gotten an empty stare that I do believe means "Why?". And so I've concluded that people in general aren't that interested in this kind of detailed check of grocery expenses, but maybe I'll ask Willy:s if they're interested further down the line. Because why not? For people who love data, maybe they're interested in collecting data of themselves, and then train an AI to do their daily grocery shopping. 

### Challenges
During the project, various issues have surfaced. The biggest issues have been directly connected to the digital receipts on the Willy:s homepage. Firstly, the receipts are saved as pdfs, but the text refuses to be extracted. Copy/pasting the text, or alternatively extracting it with python, yields seemingly gibberish results. So I opted with first converting them to pngs, and then using pytesseract to extract the text with image recognision. This in turn, led to the problem of the receipt text being flawed at times, e.g., inserting spaces where no spaces are present, completely ignoring some lines, etc. I managed to avoid some of the problems by setting the parameter config="--psm 6" in pytesseract.image_to_string, thereby forcing the text to be extracted line by line. This didn't remove all issues, so I've tried to root out some common mistakes by coding in some exceptions.

Secondly, the receipts from Willy:s get somewhat "corrupted" over time. That is receipts that are older than ~2 weeks change name and converts all Swedish letters (Ää, Öö, Åå) into question marks. This adds a lot more work, especially since I've used the time stamp in the original file names to extract time and date. 

This is also my very first project that I intend to publish on GitHub. So I'm doing my very best to create structured code readable by anyone, not just me, but more importantly, structuring the directories properly, creating my first README.md, making sure all necessary files are present meanwhile unnecessary files are removed, and so on. So if this project contains stupid stuff, or lacks very smart stuff, any guidance is welcome.

  
