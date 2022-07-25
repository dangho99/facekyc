import json
from . import ClassProperty


class SystemEnv:
    __instance: dict = None

    @staticmethod
    def get_instance():
        if not SystemEnv.__instance:
            return SystemEnv()

        return SystemEnv.__instance

    def __init__(self) -> None:
        if SystemEnv.__instance:
            raise Exception("This class cannot initialize")
        else:
            SystemEnv.__instance = self

            with open("./env.json") as f:
                env_vars = json.load(f)

            self.__host: str = env_vars["host"]
            self.__matched_score: str = env_vars["matched_score"]
            self.__distance_metric: str = env_vars["distance_metric"]
            self.__serving_url: str = env_vars["serving_url"]
            self.__serving_ip: str = env_vars["serving_ip"]
            self.__serving_port: int = env_vars["serving_port"]
            self.__model_version: int = env_vars["model_version"]

    @ClassProperty
    def host(cls):
        return cls.get_instance().__host

    @ClassProperty
    def matched_score(cls):
        return cls.get_instance().__matched_score

    @ClassProperty
    def distance_metric(cls):
        return cls.get_instance().__distance_metric

    @ClassProperty
    def model_version(cls):
        return cls.get_instance().__model_version

    @ClassProperty
    def serving_url(cls):
        return cls.get_instance().__serving_url.format(
            server_ip=cls.get_instance().__serving_ip,
            server_port=cls.get_instance().__serving_port,
            model_version=cls.get_instance().__model_version
        )
