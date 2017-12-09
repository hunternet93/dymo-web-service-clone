# Dymo Web Service Clone
This is a work-in-progress open-source reimplementation of Dymo's web service for label printing.

### Requirements
* Linux (support for other OSes would be trivial, but also unneccessary)
* Python 3.5 or greater
* [cairosvg](http://cairosvg.org/documentation/)

### Usage
Dymo Web Service Clone is still being developed and isn't quite ready-to-use. You can give it a try though, just install the above requirements and then run with:

    python3 dymo-web-service-clone.py

Currently, it advertises a dummy printer and waits for print jobs. When a print job is received, the label data is extracted and then applied to the included `Test Tag.svg` file. Text in brackets `{like this}` are replaced with the appropriate values from the received label data. Next, the generated label is printed on the system default printer.

Eventually I'll replace all the hard-coded stuff with a proper config file, and write some real documentation.
