from core.user import run


if __name__ == '__main__':
    # run api
    run(api_host="0.0.0.0", api_port=8999, debug=True)