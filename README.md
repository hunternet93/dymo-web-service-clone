# Dymo Web Service Clone
This is an open-source reimplementation of Dymo's web service for label printing.

### Requirements
* Linux (support for other OSes would be trivial, but also unneccessary)
* Python 3.5 or greater
* [cairosvg](http://cairosvg.org/documentation/)

### Usage
After installing the above requirements, edit the included `dymo-web-service-clone.ini` file as needed. Labels will be printed using the specified SVG file as a template.

When a print job is received its fields will be applied to the template, replacing text in brackes with the corresponding field from the print job. For example, `{Name}` would be replaced from the Name field of an incoming job. When the `debug` option in the config is enabled, all label data fields will be shown in the console, useful for determining which fields are available.

After editing the config file, simply run:

    python3 dymo-web-service-clone.py <location of config file>

Since the server uses a self-signed certificate, you must accept the certificate. Open [https://127.0.0.1:41951/](https://127.0.0.1:41951/) in your browser and allow the insecure connection. Once you see the status page, it's ready to go.

The server will wait for incoming print jobs and print them to the specified printer, or the system default if none are specified.
