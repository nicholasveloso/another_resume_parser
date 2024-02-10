# Resume Parser

1. Resume Parser Lambda worker file consists a **`ParseResume`** class that can extract structured data from resumes.
2.  It has functions to check if the resume is from LinkedIn, generate basic parsing results, and save parsed data to a DynamoDB database.
3. The class also includes methods to interact with Amazon S3 and DynamoDB services. It can read a file from S3, compute a hash of the file content, and generate a file name. 
4. The class can then parse the resume file using either **`GeneralResumeParser`** or **`LinkedinResumeParser`**, depending on whether the resume is a general CV or a LinkedIn resume. The parsed data is then stored in the DynamoDB database.
5. The **`process_request`** method is the main function that processes the resume file. It reads the file from S3, checks if the resume is a LinkedIn resume or a general CV, generates basic parsing results, and stores the parsed data in the DynamoDB database. 
6. If the parsing is successful, the method returns **`"success"`**, along with some keys related to the parsed data. If parsing fails, the method returns **`"Resume pdf is not properly formatted"`**.

Going deep our resume parser is not a single parser rather, an integration of 3 different parser.

1. Basic Parser
2. LinkedIn Parser
3. General Parser

### Process:

1. first the Resume are uploaded to S3, when uploaded resume parser lambda is invoked.
2. This lambda first call the Basic Resume Parser function to get the Basic Details like name, email, phone no etc
3. Then lambda checks whether the uploaded file is a LinkedIn resume or not. if it is a LinkedIn resume then it call the LinkedIn Parser function.
4. If the uploaded resume is not LinkedIn resume then it calls General Resume Parser.
5. At end the extracted data are stored in **Parsed_cv_data_v3** DB.

### Basic Parser:

This parser contains a class named  **`BasicParser`** which contains several methods to extract basic information such as name, email, and phone number from a given PDF file.

Here is a description of each method in the class:

1. **`filter_func`**: A helper method used to filter non-ASCII characters from a given string.
2. **`_remove_non_ascii`**: A method used to remove non-ASCII characters from a given string.
3. **`extract_lines_pdfplumber`**: A method that uses the **`pdfplumber`** library to extract lines from a given PDF file.
4. **`extract_basic`**: A method that extracts name, email, and phone number from the converted PDF file. It uses various regular expressions to match patterns and identify the relevant information.
5. **`remove_digits`**: A method that removes digits from a given string.
6. **`extract_name`**: A method that extracts the name from the converted PDF file. It checks various parameters in the first few lines of the document to search for names using regular expressions.
7. **`extract_info`**: A method that structures the final response object and encapsulates function calls to all modularized functions.
8. **`check_num`**: A method that finds phone numbers in a line of text. It checks if the phone number is present in a line of text using regular expressions or if conditions.
9. **`extract_phno`**: A method that finds the phone number in the converted PDF file. It replaces all special characters with spaces and calls a function to check and find the phone number in a specific line.
10. **`extract_email`**: A method that finds the email in the converted PDF file. It checks if the email is present in the converted PDF file using regular expressions.
11. **`extract_extra_email`**: A method that finds extra email IDs in the converted PDF file. It checks for extra email IDs using regular expressions and ignores the primary email found earlier.
12. **`extract_extra_phone`**: A method that finds extra phone numbers in the converted PDF file. It checks for extra phone numbers using regular expressions and ignores the primary phone number found earlier.
13. **`generate_result`**: The main method of the class that converts the PDF file to a string and extracts name, emails, and phone numbers. It separates sections, extracts lines, and finds name, emails, and phone numbers from the converted PDF file using multiple functions.

### General Parser:

This Parser is the most used Parser among the 3 Parser.

General Parse used to parse all other CV except if it isn’t a LinkedIn CV.

General Parser contains 4 levels of extraction like
  1. parse1

1. parse2
2. parse3
3. parse4 

the whole process start at general parser class

which call the P1 parser.

P1 Parser:

1. it converts Pdf to words using Pdf plumber.
2. here each word contain meta data.
3. then the words are grouped to form a line by using the properties of word.
4. these are returned to General Parser class

P2 Parser:

1. the output from P1 parser is the input for P2
2. here the line are analysed and converted to headers.
3. then the parser check for columns in the resume. if columns exists then it splits the lines to saperate columns.
4. then all these lines are merged to form para and then segregated to form sections.
5. the output of the P2 does not contain any meta data.

P3 Parser:

1. the output of the P2 is input for P3
2. so here first we match the divided sections or lines with the possible headers in the constants file. constant files contains all possible headers in resumes.
3. here we individually extract experience, projects, education, about, achievements etc.
4. but all this data is raw data they must be tuned.

P4 Parser:

1. the output from P3 is input for P4 parser
2. here all the headers like experience, education , projects etc are tuned.
3. means here we are extracting dates,marks , location etc from the raw data.

### Limitations:

1. our resume parser is not able to extract data when there are more than 2 columns in a resume.
2. this Resume Parser is not able to parse data from table formatted cvs
3. Resume Parser is not able to read image files
4. most of the cases resume parser is not able to get names and skills.
5. some of the resumes are parsed till P3 perfectly but returning null at P4.
