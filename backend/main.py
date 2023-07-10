from core.user import run
import os

if __name__ == '__main__':
    debug_mode = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
    trainable = os.getenv('TRAINABLE', 'False').lower() == 'true'
    train_interval = float(os.getenv("TRAIN_INTERVAL", "10.0"))
    api_port = int(os.getenv("API_PORT", "8999"))

    # run api
    run(
        api_host='0.0.0.0',
        api_port=api_port,
        debug_mode=debug_mode,
        train_interval=train_interval,
        trainable=trainable
    )
