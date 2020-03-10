from datetime import datetime

import requests
import urllib3
from requests.auth import HTTPBasicAuth

# Disable proxy settings
session = requests.Session()
session.trust_env = False

# Disable SSL warnings
urllib3.disable_warnings()


class Publisher:
    def __init__(self, config):
        self.config = config
        self.username = config.username
        self.password = config.password
        self.space = config.content['confluence']['space']
        self.confluence_host = config.content['confluence']['host']

    def get_content(self, url):
        if not self.username or not self.password:
            raise SyntaxError("User or Password not set")

        response = session.get(url, auth=HTTPBasicAuth(self.username, self.password), verify=False,
                               headers={'Cache-Control': 'no-cache',
                                        'Pragma': 'no-cache',
                                        'Expires': 'Thu, 01 Jan 1970 00:00:00 GMT'})
        return response

    def post_content(self, url, data):
        if not self.username or not self.password:
            raise SyntaxError("User or Password not set")

        response = session.post(url, json=data, auth=HTTPBasicAuth(self.username, self.password), verify=False,
                                headers={'Cache-Control': 'no-cache',
                                         'Pragma': 'no-cache',
                                         'Expires': 'Thu, 01 Jan 1970 00:00:00 GMT'})
        return response

    def put_content(self, url, data):
        if not self.username or not self.password:
            raise SyntaxError("User or Password not set")

        response = session.put(url, json=data, auth=HTTPBasicAuth(self.username, self.password), verify=False,
                               headers={'Cache-Control': 'no-cache',
                                        'Pragma': 'no-cache',
                                        'Expires': 'Thu, 01 Jan 1970 00:00:00 GMT'})
        if response.status_code != 200:
            raise ConnectionError(response.text)

        return response

    def publish(self, content):
        title = self.config.content['confluence']['page_name']

        parent_title = self.config.content['jira']['parent_page'].replace(' ', '%20')
        url = f"{self.confluence_host}/confluence/rest/api/content?spaceKey={self.space}&title={parent_title}"

        response = self.get_content(url)
        result = response.json()['results'][0]

        parent_id = result['id']
        url_children = "{confluence_host}/confluence/rest/api/{id}/child/page".format(
            confluence_host=self.confluence_host, id=parent_id)

        response = self.get_content(url_children)
        results = response.json()['results']
        found = None
        for result in results:
            if title in result['title']:
                found = result['id']
                break
        if found:
            print("Already exists: " + found)

            get_page_url = "{}/confluence/rest/api/content/{}".format(self.confluence_host, found)
            update_page_url = get_page_url + "?expand=body.storage"

            r = self.get_content(get_page_url)
            version = r.json()['version']['number']
            version += 1

            page = {
                "type": "page",
                "title": title,
                "version": {"number": version},
                "body": {
                    "storage": {
                        "value": content,
                        "representation": "storage"
                    }
                }
            }
            r = self.put_content(update_page_url, page)

        else:
            new_page_url = "{}/confluence/rest/api/content".format(self.confluence_host)
            page = {
                "type": "page",
                "title": title,
                "ancestors": [{"id": parent_id}],
                "space": {"key": self.space},
                "body": {
                    "storage": {
                        "value": content,
                        "representation": "storage"
                    }
                }
            }
            r = self.post_content(new_page_url, page)

        print(r.status_code)

    def generate_html(self, results):
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
            for component in self.config.content['components']:
                data = envdata[component]
                table_content += f'''<tr><td bgcolor="#D3D3D3"><a href="{data[3]}" target="_blank"><img src="{self.config.content['jenkins']['host']}/jenkins/static/665c6ecd/images/16x16/clock.png"/></a>&nbsp{component}</td><td>{data[0]}<br/><font style="rgb(133,134,154)"><sub><i>{data[2]}</i></sub></font></td><td>{data[1]}</td></tr>'''
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
