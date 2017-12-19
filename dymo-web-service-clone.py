import templates

import logging
import traceback
import configparser

import http.server
import urllib
import ssl

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

import os
import sys
import tempfile
import subprocess
from cairosvg import svg2png

class DymoWebServiceClone:
    def __init__(self):
        if len(sys.argv) > 1:
            location = sys.argv[1]
            if not os.stat(location):
                print('Cannot open config file {}'.format(location))
                quit()

        else:
            for location in ('dymo-web-service-clone.ini', '/etc/dymo-web-service-clone.ini',
                             '~/.config/dymo-web-service.clone.ini'):
                if os.stat(location): break
        
            if not location:
                print("Cannot find config file. Please specify the file's location or place it in a supported location.")
                quit()
        
        self.config = configparser.ConfigParser()
        self.config.read(location)
        
        self.dpi = self.config.getint('DymoWebServiceClone', 'dpi')
        self.printer = self.config.get('DymoWebServiceClone', 'printer', fallback = None)
        self.debug = self.config.getboolean('DymoWebServiceClone', 'debug', fallback = False)

        if self.debug: logging.basicConfig(level = logging.DEBUG)
        else: logging.basicConfig(level = logging.INFO)
        
        self.labels = []
        for section in self.config.sections():
            if section.startswith('Label'):
                self.labels.append({
                    'svgfile': self.config.get(section, 'svgfile'),
                    'hasfield': self.config.get(section, 'hasfield', fallback = None)
                })
        
        if len(self.labels) == 0:
            print('Config file must contain at least one [Label] section')
            quit()
        
        self.print_counter = 1

    def replace_render_print_svg(self, data):
        svgfile = None
        
        for label in self.labels:
            if label.get('hasfield'):
                if label['hasfield'] in data:
                    svgfile = label['svgfile']
                    break
            else:
                svgfile = label['svgfile']
        
        if not svgfile:
            logger.error('No label conditions match data, aborting print job.')
            return
    
        tree = ET.parse(svgfile)
        root = tree.getroot()
        
        # Finds all tspan elements, formats them with label data. The weird selector is due to how ETree handles namespaces or something. 
        for tspan in root.iter('{http://www.w3.org/2000/svg}tspan'):
            if tspan.text:
                try:
                    tspan.text = tspan.text.format(**data)
                except KeyError as e:
                    logging.warn('Label data does not contain property "{}"'.format(e.args[0]))
        
        outfilename = os.path.join(tempfile.gettempdir(), 'dymo-web-service-generated-{}.png'.format(self.print_counter))
        
        svg2png(
            bytestring = ET.tostring(root, encoding = 'utf8', method = 'xml'),
            dpi = self.dpi,
            write_to = outfilename
        )
        
        logging.debug('Rendered SVG to PNG tempfile')

        if self.printer: printsettings = ('-P', self.printer)
        else: printsettings = tuple()
        
        # TODO uncomment
#        subprocess.run(
#            ('lpr', '-r', '-T', 'Dymo Web Service Clone #{}'.format(self.print_counter),
#            '-q', outfilename) + printsettings
#        )
        
        self.print_counter += 1
        
        logging.debug('Printed rendered label')

    def get_printer_info_xml(self):
        # Currently uses placeholder data. Real printer data could be pulled from CUPS if needed.
        return '<Printers>{}</Printers>'.format(
            templates.printer_info_template.format(
                name = 'Dymo Web Service Clone',
                modelname = 'Dymo Web Service Clone',
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
            tb = traceback.format_exc()
            logging.error(tb)
            if dymo.debug:
                self.respond_with_data(templates.exception_traceback_template.format(tb.replace('\n', '<br>')), code = 500)
            else:
                self.respond_with_data(templates.exception_template, code = 500)                
    
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
            tb = traceback.format_exc()
            logging.error(tb)
            if dymo.debug:
                self.respond_with_data(templates.exception_traceback_template.format(tb.replace('\n', '<br>')), code = 500)
            else:
                self.respond_with_data(templates.exception_template, code = 500)              
                
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
            
            logging.debug('Label data: {}'.format(labeldata))

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
