# Release Notes

## Version 0.2.3 Release Notes - August 31, 2023
### Application discovery
* Expanded unzip capabilties to include .tar, gztar, bztar, and tgz files
* To optimize the running of CLOC in a Windows environment, utilize the subst function to create a temporary drive, which avoids the long path issue while runnin CLOC. 
* In windows environment, use subst to create a temporty drive to shorten the file name length while running CLOC 
* Expand cleanup to support regular expression in the file and folder cleanup lists 
* Enhanced discovery report
    * adjusted lines of code output to render as KLoc, or MLoc
    * Corrected Technolgy count missmatch
    * Corrected SQL count missmatch 
  
### Analysis
* Corrected HL-WORK folder not always being created issue
* Create application if it not exists in Highlight
* Corrected - skip analysis if already marked as done

### Reporting
* Corrected - report not always running issue 
* Corrected general formatting issues
* Added Green Impact Slide 

<u>Note: Report templates are curently not include in the extend package, please contact NKA</u>


## Version 0.2.2 Release Notes - June 7, 2023
* Interactive installation - Improvements
* Create application in Highlight
* Source Code Discovery Formatting
* Bug Fixes

## Version 0.2.1 Release Notes - April 25, 2023
* Interactive installation
* Bug Fixes

## Version 0.2.0 Release Notes
* First release in March 2023

## Version 1.0.5-beta Release Notes - May 30, 2024
* Improvments in installation
* Updated Templates
* Bug Fixes
