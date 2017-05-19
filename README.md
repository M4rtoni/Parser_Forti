# Parser_Forti

This programme is tool to convert a Fortinet configuration file in JSON and/or XSLS file.

## Install

Clone the project:
```bash
git clone https://github.com/M4rtoni/Parser_Forti.git
cd Parser_Forti
```
Install the project:
```bash
pip install -r requirements.txt
sudo python setup.py install
```
## Test
```bash
$ python parser_forti.py --files test.conf --json --xlsx
        Reading : done
        Header : done
        Parsing : done
/usr/lib/python2.7/site-packages/openpyxl/workbook/child.py:98: UserWarning: Title is more than 31 characters. Some applications may not be able to read the file
  warnings.warn("Title is more than 31 characters. Some applications may not be able to read the file")
        Format XLS : done
        Format JSON : done
```
Openpyxl can't create a sheet with more than 31 characters, so `firewall profile-protocol-options` (33) don't pass !

XLSX file return an error when you open it, `Microsoft Excel` can fix it but you have to change links with the new names. `firewall profile-protocol-options` become `firewall profile-protocol-optio`, save and that's it !

## Run

Let's go !
```bash
python parser_forti.py --xlsx 
```

Take 5 optionnals arguments :
  - `files` (--files) change wildcard to find configuration files (default : `*.conf`)
  - `directory` (--dir) change path to find files (default current folder)
  - `JSON` (--json) save result in an JSON file (`file_name.json`)
    - This file contains a multiples level of dictionaries of data extract from a configuration file,
    - Data are store in lists (even it's only one element)
  - `XLSX` (--xlsx) save result in an XSLX file (`file_name.xlsx`)
    - This file have main sheet (`Acceuil`), that has a empty and non empty sheet list,
    - Every non empty sheet show informations extract from a main part of a configuration file,
  - `help` (-h/--help) output usage information

## Incoming

  - Bug fix for sheet names longer than 31 characters
  - creating optionnal argument for selecting keys (you can change it manualy in `forti_paarser.py line 677`)

# Licence

BSD 3-clause "New" or "Revised" License
