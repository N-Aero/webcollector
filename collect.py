import json
import re
from datetime import datetime

import requests
import urllib3
from requests.auth import HTTPBasicAuth

# Disable proxy settings
session = requests.Session()
session.trust_env = False

# Disable SSL warnings
urllib3.disable_warnings()


class CollectData:
    def __init__(self, jenkins_host, bitbucket_host, username, password):
        self.jenkins_host = jenkins_host
        self.bitbucket_host = bitbucket_host
        self.username = username
        self.password = password

    def get_content(self, url):
        if not self.username or not self.password:
            raise SyntaxError("User or Password not set")

        try:
            response = session.get(url, auth=HTTPBasicAuth(self.username, self.password), verify=False,
                                   headers={'Cache-Control': 'no-cache',
                                            'Pragma': 'no-cache',
                                            'Expires': 'Thu, 01 Jan 1970 00:00:00 GMT'})
        except:
            return None

        if response.status_code != 200:
            return None

        return response

    @staticmethod
    def create_jira_key_macro(jira_key):
        return '''
        <p><ac:structured-macro ac:name="jira">
            <ac:parameter ac:name="columns">key,summary</ac:parameter>
            <ac:parameter ac:name="key">{key}</ac:parameter>
        </ac:structured-macro></p>'''.format(key=jira_key)

    def extract_issue_key(self, text_containing_issue_key):
        url = ''
        if text_containing_issue_key is not None:
            re_match = re.search(r'(OSA)-?(\d{4})', text_containing_issue_key)
            if re_match:
                match = re_match.group(1) + '-' + re_match.group(2)
                url = self.create_jira_key_macro(match)
        return url

    def get_bitbucket_tag_info(self, repository, tag_generic_part, version):
        if version == 'No Version' or version is None:
            return '-'
        else:
            tag = tag_generic_part + version
        try:
            tag_url = self.bitbucket_host + '{}/tags/{}'.format(repository, tag)
            content = self.get_content(tag_url)
            if content is None:
                return '-'

            json_content = json.loads(content.text)
            commit_url = self.bitbucket_host + '{}/commits/{}'.format(repository, tag, json_content['latestCommit'])
            commit_content = self.get_content(commit_url)
            json_commit = json.loads(commit_content.text)
            epoch = json_commit['authorTimestamp']
            date = datetime.fromtimestamp(epoch / 1000.0).strftime("%d/%m/%Y %H:%M:%S")
        except KeyError as err:
            raise AssertionError(
                'Could not find information in repo: {repo} for tag: {tag}\nError: {error}'.format(repo=repository,
                                                                                                   tag=tag,
                                                                                                   error=err))
        except json.decoder.JSONDecodeError:
            date = 'date not found'
        return date

    def get_releaseinfo(self, environment, street, component_config):
        version_info = component_config["version"]
        if "version-info" in version_info:
            version, link_versioninfo = self.get_version_from_version_text(
                version_info["version-info"].format(street, environment))
        else:
            raise NotImplementedError("only version text currently implemented")

        issue = self.extract_issue_key(version)
        deploytime = self.get_bitbucket_tag_info(component_config["repo_key"], component_config["scm_version_prefix"],
                                                 version)
        jenkins_link = self.jenkins_host + component_config["jenkins_job"]

        return link_versioninfo, issue, deploytime, jenkins_link

    def get_version_info_per_street(self, config):
        data = {}
        content = config['environments']
        for environment in content:
            for street in content[environment]:
                server_title = str(environment).capitalize() + ' ' + str(street)
                environment_key = str(environment) + '_' + str(street)
                data[server_title] = {}

                # iterate over each component
                for component in config['components']:
                    component_name = component['name']
                    if "unavailable" not in component or environment_key not in component["unavailable"]:
                        data[server_title][component_name] = list(self.get_releaseinfo(environment, street, component))
        return data

    def get_version_from_version_text(self, url):
        version_txt = self.get_content(url)
        if version_txt is None:
            version_txt = 'Not Found'
        else:
            version_txt = version_txt.text
        try:
            version = re.findall(r'>(\d{4}.*)<', version_txt)[0]
        except IndexError:
            version = 'No Version'
        link_html = '<a href="{url}" target="_blank">{version}</a>'.format(url=url, version=version)
        return version, link_html
