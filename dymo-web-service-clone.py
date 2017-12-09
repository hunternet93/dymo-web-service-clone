import templates

import logging
import traceback

import http.server
import urllib
import ssl

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

import os
import tempfile
import subprocess
from cairosvg import svg2png

logging.basicConfig(level = logging.DEBUG)

# TODO get all settings from command line or conf file
class DymoWebServiceClone:
    def __init__(self):
        self.svgfilename = 'Test Tag.svg'

        self.print_counter = 1

    def replace_render_print_svg(self, data):
        tree = ET.parse(self.svgfilename)
        root = tree.getroot()
        
        # Finds all tspan elements, formats them with label data. The weird selector is due to how ETree handles namespaces or something. 
        for tspan in root.iter('{http://www.w3.org/2000/svg}tspan'):
            if tspan.text:
                try:
                    tspan.text = tspan.text.format(**data)
                except KeyError as e:
                    logging.warn('Label data does not contain property "{}"'.format(e.args[0]))
        
        outfilename = os.path.join(tempfile.gettempdir(), 'dymo-web-service-generated.png')
        
        svg2png(
            bytestring = ET.tostring(root, encoding = 'utf8', method = 'xml'),
            dpi = 300, # TODO pull this from printer info or user settings
            write_to = outfilename
        )
        
        logging.debug('Rendered SVG to PNG tempfile')

        # TODO print to printer specified in options instead of to default
        # TODO add -r option to auto-remove temp file after printing

        subprocess.run(
            ('lpr', '-T', 'Dymo Web Service Clone #{}'.format(self.print_counter), '-q', outfilename)
        )
        
        self.print_counter += 1
        
        logging.debug('Printed rendered label')

    def get_printer_info_xml(self):
        # TODO make this use real data instead of placeholder
        return '<Printers>{}</Printers>'.format(
            templates.printer_info_template.format(
                name = 'Test',
                modelname = 'Model T???',
                isconnected = 'True',
                islocal = 'True',
                istwinturbo = 'False'
            )
        )

dymo = DymoWebServiceClone()

class DymoRequestHandler(http.server.BaseHTTPRequestHandler):
    def respond_with_data(self, data, content_type = 'text/html', code = 200):
        self.send_response(code)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Charset', 'utf-8')
        self.send_header('Content-Type', content_type)
        self.send_header('Cache-Control', 'max-age=0')
        self.end_headers()
        
        if type(data) == str:
            self.wfile.write(data.encode('utf-8'))
        else:
            self.wfile.write(data)
        
    def do_GET(self):
        try:
            self.do_GET_wrapped()
        except:
            # TODO only do this in debug mode
            tb = traceback.format_exc()
            logging.error(tb)
            self.respond_with_data(templates.exception_template.format(tb.replace('\n', '<br>')), code = 500)            
    
    def do_GET_wrapped(self):
        logging.debug('GET {} from {}'.format(self.path, self.client_address[0]))

        if self.path == '/' or self.path == '/DYMO/DLS/Printing/Check':
            self.respond_with_data(templates.status_template)
        
        elif self.path == '/DYMO/DLS/Printing/StatusConnected':
            # TODO determine under what circumstances this should return 'false'
            self.respond_with_data('true', content_type = 'text/plain')
        
        elif self.path == '/DYMO/DLS/Printing/GetPrinters':
            self.respond_with_data(dymo.get_printer_info_xml(), content_type = 'text/xml')
        
        else:
            self.respond_with_data(templates.error_404_template, code = 404)

    def do_POST(self):
        try:
            self.do_POST_wrapped()
        except:
            # TODO only do this in debug mode
            tb = traceback.format_exc()
            logging.error(tb)
            self.respond_with_data(templates.exception_template.format(tb.replace('\n', '<br>')), code = 500)         
                
    def do_POST_wrapped(self):
        logging.debug('POST {} from {}'.format(self.path, self.client_address[0]))
        
        if self.path == '/DYMO/DLS/Printing/PrintLabel':
            logging.info('New print job from {}'.format(self.headers.get('Referer') or '<unknown>'))

            length = int(self.headers['Content-Length'])
            postdata = urllib.parse.parse_qs(self.rfile.read(length).decode('utf-8'))
            
            tree = ET.fromstring(postdata['labelSetXml'][0])
            
            labeldata = {}
            for od in tree.iter('ObjectData'):
                labeldata[od.attrib['Name']] = od.text
            
            logging.debug('Label data:', labeldata)

            dymo.replace_render_print_svg(labeldata)

            self.respond_with_data('')

        else:
            self.respond_with_data(templates.error_404_template, code = 404)

if __name__ == '__main__':
    for port in range(41951, 41961):
        try:
            httpd = http.server.HTTPServer(('127.0.0.1', port), DymoRequestHandler)
        except OSError:
            continue
        else:
            break
    
    logging.info('Serving on port {}'.format(port))
    
    # TODO something about this causes wget to throw errors when accessing. Works OK in Firefox, so not fixing for now.
    httpd.socket = ssl.wrap_socket(httpd.socket, certfile = 'chain.pem', keyfile = 'key.key', server_side = True)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('Bye!')
