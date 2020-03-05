import requests
import urllib3
from requests.auth import HTTPBasicAuth

# Disable proxy settings
session = requests.Session()
session.trust_env = False

# Disable SSL warnings
urllib3.disable_warnings()


class Publisher:
    def __init__(self, username, password, space, host):
        self.username = username
        self.password = password
        self.space = space
        self.confluence_host = host

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

    def publish(self, parent_page, title, content):
        parent_title = parent_page.replace(' ', '%20')
        url = "{confluence_host}/confluence/rest/api/content?spaceKey={space}&title={title}".format(
            confluence_host=self.confluence_host, space=self.space, content=content)

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
