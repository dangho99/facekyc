from core.user import run
from keeper.environments import SystemEnv


if __name__ == '__main__':
    # run api
    run(api_host=SystemEnv.host, api_port=9980, debug=True)