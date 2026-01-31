import dataclasses

from visual_regression_tracker import types
from visual_regression_tracker.visualRegressionTracker import _http_request

from .config import _from_dict


@dataclasses.dataclass
class ClientConfig:
    project: str
    email: str
    password: str
    apiUrl: str = "http://localhost:4200"


class Client:
    def __init__(self, config: ClientConfig):
        """
        Creates a new Client

        :param config: The configuration to use.
        """
        self.config = config
        # retrieve token
        response = _http_request(
            f"{self.config.apiUrl}/users/login",
            "post",
            data={
                "email": self.config.email,
                "password": self.config.password,
            },
            headers={},
        )
        self.headers = {"Authorization": f"Bearer {response['token']}"}
        # retrieve project id
        self.project = self.get_project(self.config.project)

    def get_projects(self) -> list[types.Project]:
        response = _http_request(
            f"{self.config.apiUrl}/projects",
            "get",
            data={},
            headers=self.headers,
        )
        projects = [_from_dict(item, types.Project) for item in response]
        return projects

    def get_project(self, name: str) -> types.Project:
        projects = self.get_projects()
        for project in projects:
            if project.name == name:
                return project
        raise ValueError(f'Project with name "{name}" not found.')

    def get_builds(self) -> list[types.Build]:
        response = _http_request(
            f"{self.config.apiUrl}/builds?projectId={self.project.id}&take=1000&skip=0",
            "get",
            data={},
            headers=self.headers,
        )
        builds = [_from_dict(item, types.Build) for item in response["data"]]
        return builds

    def get_build(
        self, id: str | None = None, ciBuildId: str | None = None
    ) -> types.Build:
        if (id is None) == (ciBuildId is None):
            raise ValueError("Either 'id' or 'ciBuildId' must be provided.")
        builds = self.get_builds()
        for build in builds:
            if (
                id is not None
                and build.id == id
                or ciBuildId is not None
                and build.ciBuildId == ciBuildId
            ):
                return build
        if id is not None:
            raise ValueError(f'Build with id "{id}" not found.')
        else:
            raise ValueError(f'Build with ciBuildId "{ciBuildId}" not found.')
