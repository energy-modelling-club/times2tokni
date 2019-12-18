# excel2json

## Description
The excel2json.py converts the data from the data4json.xlsx file into a json file that can be pushed to tokni's github repository.

## Requirements
- python 3.6
- pandas

## General information
- All files must be in the same folder next to each other
- With each execution potential old json files in the folder will be over-written
- If you use an excel file with a different structure or naming convention compared to the original data4json.xlsx, make sure to change the filter.csv accordingly
- All periods in the excel file will be used, but you have the possiblity to exclude years within the exel2json.py


## Output
The script creates
1. stackedBar.json
2. line.json

The line.json consists only of the 'CO2 budget' indicator. The remaining indicators are in the stackedBar.json. If needed, this can be changed in the excel2json.py directly.