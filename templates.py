# The quadruple escapes in the CSS are there for a reason! Not a good reason, but a reason...
# (to escape them from the two rounds of Python str.format)

html_wrap_template = '''
<html>
    <head>
        <title>Dymo Web Service Clone</title>
        <meta charset="utf-8" /> 
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css?family=Lato:400,700" rel="stylesheet"> 
        <style type="text/css">
            html {{{{
                margin: 0;
                width: 100%;
                background-color: #ccc;
                font-family: 'Lato', sans-serif;
                font-size: 125%;
            }}}}

            body {{{{
                margin: 2em auto;
                padding: 1em;
                width: 75%;
                min-width: 50em;
                background-color: white;
                border: 1px solid #aaa;
                border-radius: 2em;
            }}}}

            .error {{{{
                font-family: monospace;
                border: 1px solid #aaa;
                background-color: #333;
                color: #eee;
            }}}}
        </style>
    </head>
    <body>
        {}
    </body>
</html>
'''

status_template = html_wrap_template.format('''
<h1>Dymo Web Service Clone, at your service.</h1>
<p>This page will eventually have some status info and stuff, probably.</p>
''').format() # Uuuuuuugh. Anyone have a better idea how to handle this?

error_404_template = html_wrap_template.format('''
<h1>404</h1>
<p>Nothing to see here, move along, move along...</p>
''').format()

exception_traceback_template = html_wrap_template.format('''
<h1>Uh oh.</h1>
<p>Something bad happened!</p>
<hr>
<h3>Error Details</h3>
<p class="error">{}</p>
''')

exception_template = html_wrap_template.format('''
<h1>Uh oh.</h1>
<p>Something bad happened!</p>
''').format()

printer_info_template = '''
<LabelWriterPrinter>
    <Name>{name}</Name>
    <ModelName>{modelname}</ModelName>
    <IsConnected>{isconnected}</IsConnected>
    <IsLocal>{islocal}</IsLocal>
    <IsTwinTurbo>{istwinturbo}</IsTwinTurbo>
</LabelWriterPrinter>
'''
