import argparse
import json
from datetime import datetime
from collect import CollectData
from publish import Publisher


def dump_html(h):
    html = """
    <html>
    <head>
        <link type="text/css" rel="stylesheet" href="css/styles.css" media="all">
    </head>
    <body>
        <div class=".wiki-content">
        {htmlcontent}
    </body>
    </html>
    """.format(htmlcontent=h)

    with open('test.html', 'w') as file:
        file.write(html)



class Config:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        with open('config.json', 'r') as f:
            self.content = json.load(f)


if __name__ == '__main__':
    cmdline_parser = argparse.ArgumentParser()
    cmdline_parser.add_argument("-v", "--verbose", action="store_true")
    cmdline_parser.add_argument("-u", "--user")
    cmdline_parser.add_argument("-p", "--password")
    cmdline_args = cmdline_parser.parse_args()

    config = Config(cmdline_args.user, cmdline_args.password)

    c = CollectData(config)

    results = c.get_version_info_per_street(config)

    p = Publisher(config)
    htmlresult = p.generate_html()

    if cmdline_args.verbose:
        dump_html(htmlresult)
    else:
        p.publish(htmlresult)
