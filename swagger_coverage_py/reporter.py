import os
import platform
import re
import shutil
from pathlib import Path

import requests

from swagger_coverage_py.docs_writers.api_doc_writer import write_api_doc_to_file


class CoverageReporter:
    def __init__(self, api_name: str, host: str):
        self.host = host
        self.swagger_doc_file = f"swagger-doc-{api_name}.json"
        self.output_dir = self.__get_output_dir()
        self.ignore_requests = []
        self.swagger_coverage_config = f"swagger-coverage-config-{api_name}.json"

    def __get_output_dir(self):
        output_dir = "swagger-coverage-output"
        subdir = re.match(r"(^\w*)://(.*)", self.host).group(2)
        return f"{output_dir}/{subdir}"

    def setup(
        self, path_to_swagger_json: str, auth: object = None, cookies: dict = None
    ):
        """Setup all required attributes to generate report

        :param path_to_swagger_json: The relative URL path to the swagger.json (example: "/docs/api")
        :param auth: Authentication object acceptable by "requests" library
        :param cookies: Cookies dictionary. (Usage example: set this to bypass Okta auth locally)

        """
        link_to_swagger_json = f"{self.host}{path_to_swagger_json}"

        response = requests.get(link_to_swagger_json, auth=auth, cookies=cookies)
        assert response.ok, (
            f"Swagger doc is not pulled. See details: "
            f"{response.status_code} {response.request.url}"
            f"{response.content}\n{response.content}"
        )
        swagger_json_data = response.json()

        write_api_doc_to_file(self.swagger_doc_file, swagger_json_data)

    def generate_report(self, venv_path="venv"):
        inner_location = "swagger-coverage/swagger_coverage_py/swagger-coverage-commandline/bin/swagger-coverage-commandline"

        cmd_ = f"src/{inner_location}"
        cmd_venv = f"{venv_path}/src/{inner_location}"

        if Path(cmd_).exists():
            cmd_path = cmd_
        elif Path(cmd_venv).exists():
            cmd_path = cmd_venv
        else:
            raise Exception(
                f"No commandline tools is found in following locations:\n{cmd_}\n{cmd_venv}.\n"
                f"Make sure your venv_path parameter matches to your "
                f"virtual environment directory name.\n"
            )

        config = self.swagger_coverage_config
        if config:
            command = f"{cmd_path} -s {self.swagger_doc_file} -i {self.output_dir} -c {config}"
        else:
            command = f"{cmd_path} -s {self.swagger_doc_file} -i {self.output_dir}"

        command = (
            command if platform.system() != "Windows" else command.replace("/", "\\")
        )

        os.system(command)

    def cleanup_input_files(self):
        shutil.rmtree(self.output_dir, ignore_errors=True)
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
