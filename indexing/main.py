from core.user import run
import os


API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8999"))
DEBUG = os.getenv("DEBUG", "")
    

if __name__ == '__main__':
    debug = False
    if debug == "1":
        debug = True
    # run api
    run(api_host='0.0.0.0', api_port=API_PORT, debug=debug)
