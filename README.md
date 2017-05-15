# Forti_Parser

This programme is tool to convert a Fortinet configuration file in JSON and/or XSLS file.

## Install

Clone the project:
```bash
git clone https://github.com/M4rtoni/Parser_Forti.git
cd Forti_parser
```
Install the project:
```bash
pip install -r requirements.txt
sudo python setup.py install
```

## Run

Let's go !
```bash
python parser_forti.py --xlsx 
```

Take 5 optionnals arguments :
  - `files` (--files) change wildcard to find configuration files (default : `*.conf`)
  - `directory` (--dir) change path to find files (default current folder)
  - `JSON` (--json) save result in an JSON file (`file_name.json`)
  - `XLSX` (--xlsx) save result in an XSLX file (`file_name.xlsx`)
  - `help` (-h/--help) output usage information
