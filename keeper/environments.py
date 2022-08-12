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
            self.__broker_host: str = env_vars["broker_host"]
            self.__k: int = env_vars["k"]
            self.__n_dims: int = env_vars["n_dims"]
            self.__matched_score: float = env_vars["matched_score"]
            self.__duplicate_score: float = env_vars["duplicate_score"]
            self.__serving_host: str = env_vars["serving_host"]

    @ClassProperty
    def host(cls):
        return cls.get_instance().__host

    @ClassProperty
    def broker_host(cls):
        return cls.get_instance().__broker_host

    @ClassProperty
    def k(cls):
        return cls.get_instance().__k

    @ClassProperty
    def n_dims(cls):
        return cls.get_instance().__n_dims

    @ClassProperty
    def matched_score(cls):
        return cls.get_instance().__matched_score

    @ClassProperty
    def duplicate_score(cls):
        return cls.get_instance().__duplicate_score

    @ClassProperty
    def serving_host(cls):
        return cls.get_instance().__serving_host
