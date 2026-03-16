#!/usr/local/autopkg/python
#
# Copyright 2022 James Nairn
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Post message to Microsoft Teams based on result from autopkg"""

# Heavily based on
# https://github.com/autopkg/asemak-recipes/blob/master/PostProcessors/TeamsPost.py
# Tweaked by jwrn3 for jamf-upload output and updated to py3

# Teams alternative to the post processor provided by Ben Reilly (@notverypc)
#
# Based on Graham Pugh's slacker.py -
# https://github.com/grahampugh/recipes/blob/master/PostProcessors/slacker.py
# and
# @thehill idea on macadmin slack -
# https://macadmins.slack.com/archives/CBF6D0B97/p1542379199001400
# Takes elements from
# https://gist.github.com/devStepsize/b1b795309a217d24566dcc0ad136f784
# and
# https://github.com/autopkg/nmcspadden-recipes/blob/master/PostProcessors/Yo.py


# pylint: disable=line-too-long
# pylint: disable=invalid-name

import requests  # pylint: disable=import-error

from autopkglib import Processor  # pylint: disable=import-error
from autopkglib import ProcessorError  # pylint: disable=import-error

__all__ = ["JamfPostTeams"]


class JamfPostTeams(Processor):  # pylint: disable=too-few-public-methods
    description = """Posts to Teams via webhook based on output of jamf-upload."""

    input_variables = {
        "jamfpackageuploader_summary_result": {
            "required": False,
            "description": ("jamf-upload result dictionary to parse."),
        },
        "webhook_url": {"required": False, "description": ("Teams webhook.")},
    }
    output_variables = {}

    __doc__ = description

    def main(self):
        """Construct message from autopkg results and post to Teams"""

        # get jamfpackageuploader_summary_result from environment
        jamfpackageuploader_summary_result = self.env.get(
            "jamfpackageuploader_summary_result"
        )

        # if it exists then package was uploaded and we have something to do
        if jamfpackageuploader_summary_result:

            # test to see if webhook_url is defined
            # webhook_url = self.env.get("webhook_url")
            # if webhook_url is None:
            #     self.output("webhook_url is not defined!")

            webhook_url = self.env.get("webhook_url")
            if webhook_url is None:
                raise ProcessorError("ERROR: webhook_url not set")

            # get other vars from autopkg
            name = self.env.get("NAME")
            groups = self.env.get("GROUP_NAME")
            policy = self.env.get("POLICY_NAME")
            jss_server = self.env.get("JSS_URL")

            # get vars from jamf_upload
            version = jamfpackageuploader_summary_result["data"]["version"]
            package = jamfpackageuploader_summary_result["data"]["pkg_name"]

            # build text data structure
            teams_text = f"Version: **{version}**  \
                            \nPackage: **{package}**  \
                            \nPolicy: **{policy}**  \
                            \nGroups: **{groups}**"

            # build object to post to Teams
            teams_data = {
                "text": teams_text,
                "textformat": "markdown",
                "title": f"{name} updated on {jss_server}",
            }

            # post to Teams
            response = requests.post(webhook_url, json=teams_data)
            if response.status_code != 200:
                raise ValueError(
                    f"Request to Teams returned an error {response.status_code}, the response is:\n{response.text}"
                )


if __name__ == "__main__":
    processor = JamfPostTeams()
    processor.execute_shell()
