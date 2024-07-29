# PNP Slip Pdf Reader

This will enable parsing of data from a pnp pdf slip so that the data can be useful.
The data will be able to be exported to be used in other tools such as [Actual](https://github.com/actualbudget/actual-server) so that costs can be tracked and optimisations can occur

## Usage
In config.json specify the location of the folder that you wish store all the data in.
Folders will be created in this directory upon app start

The app will communicate via cli.
Use '**h**' to get commands in cli

## CSV Notes
The csv format is:
id, date, payee, amount, notes

Date format is: dd.mm.yy

## TODO
- Gui for user interaction
