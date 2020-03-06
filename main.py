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


def generate_html(results, display_components):
    html_content = ''
    list_of_tables = []
    html_content += '<p><b>Overzicht bijgewerkt op {datetime}</b></p>'.format(
        datetime=datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    html_content += '<ac:layout><ac:layout-section ac:type="two_equal"><ac:layout-cell>'
    column_content = ''
    left_column = ''
    right_column = ''
    for environment in results:
        bgcolor = ''
        if any('No Version' in version for version in [results[environment]['Massaal'][0],
                                                       results[environment]['Comhub'][0],
                                                       results[environment]['Kantoor'][0]
                                                       ]):
            bgcolor = 'background-color:red;'

        number_of_columns = 3
        table_content = '<table style="width: 90%; {}"><colgroup>'.format(bgcolor)
        table_content += '<col style="width: {};"/>'.format(20)
        table_content += '<col style="width: {};"/>'.format(30)
        table_content += '<col style="width: {};"/>'.format(50)
        table_content += '</colgroup>'

        # header
        table_content += '<tr><td bgcolor="#ADD8E6" colspan="{}"><h2 style="text-align: center;">{}</h2></td></tr>'.format(
            number_of_columns, environment)

        # Display components per environment
        envdata = results[environment]
        for component in display_components:
            data = envdata[component]
            table_content += f'''<tr><td bgcolor="#D3D3D3"><a href="{data[3]}" target="_blank"><img src="https://pooscisl56.ont.belastingdienst.nl/jenkins/static/665c6ecd/images/16x16/clock.png"/></a>&nbsp{component}</td><td>{data[0]}<br/><font style="rgb(133,134,154)"><sub><i>{data[2]}</i></sub></font></td><td>{data[1]}</td></tr>'''
        table_content += "</table>"
        list_of_tables.append(table_content)

    for t in range(len(list_of_tables)):
        if t % 2 == 0:
            left_column += list_of_tables[t]
        else:
            right_column += list_of_tables[t]

    column_content += left_column \
                      + "</ac:layout-cell><ac:layout-cell>" \
                      + right_column \
                      + "</ac:layout-cell></ac:layout-section></ac:layout>"
    html_content += column_content
    return html_content


if __name__ == '__main__':
    cmdline_parser = argparse.ArgumentParser()
    cmdline_parser.add_argument("-v", "--verbose", action="store_true")
    cmdline_parser.add_argument("-u", "--user")
    cmdline_parser.add_argument("-p", "--password")
    cmdline_args = cmdline_parser.parse_args()
    with open('config.json', 'r') as f:
        content = json.load(f)

    c = CollectData(content['jenkins']['host'],
                    content['bitbucket']['host'],
                    content['jira']['project-key'],
                    cmdline_args.user,
                    cmdline_args.password)

    results = c.get_version_info_per_street(content)
    htmlresult = generate_html(results, content['components'])

    if cmdline_args.verbose:
        dump_html(htmlresult)
    else:
        p = Publisher(cmdline_args.user, cmdline_args.password, content['confluence']['space'],
                      content['confluence']['host'])
        parent = content['confluence']['parent']
        pagename = content['confluence']['pagename']
        p.publish(parent, pagename, htmlresult)
