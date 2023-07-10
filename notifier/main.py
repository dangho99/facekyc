from util.database import connect_db,  close_db
from util.handler import get_datetime, get_timestamp
from loguru import logger
import requests
import time
import os


def notifier():
    timeout = float(os.getenv('TIMEOUT', '5'))
    notify_interval = float(os.getenv('INTERVAL', '86400'))
    endpoints = os.getenv('ENDPOINT', 'https://localhost:8999,http://localhost:27017,http://localhost:1234')
    api_token = os.getenv('API_TOKEN', '6022923090:AAE0fJvV52NjWlgdITuQL13H_oGgtJ5RcGA')
    chat_id = os.getenv('CHAT_ID', '-926409367')
    headers = {'Content-Type': 'application/xml'} # set what your server accepts

    db_conn = connect_db()
    while True:
        collection = db_conn['verify_logs']
        current_time = get_timestamp()
        end_time = get_datetime(current_time)
        start_time = get_datetime(current_time - notify_interval)
        verify_logs = collection.find({"datetime":{'$gte':start_time, '$lte':end_time}}, {"_id": 0})
        verify_logs = list(verify_logs)
        verify_logs = sorted(verify_logs, key=lambda d: d['datetime'])
        count_users = set([log.get('user_id') for log in verify_logs])

        if len(count_users):
            body = "From {} to {}.\n".format(start_time, end_time)
            body = body + "Number of verified users: {}\n".format(len(count_users))
            body = body + "Latest verified users: {} at {}\n\n".format(
                verify_logs[-1].get('zcfg_requester_address_email'), verify_logs[-1].get('datetime')
            )
        else:
            body = "From {} to {}.\n".format(start_time, end_time)
            body = body + "Number of verified users: 0\n\n"

        conn_status = "Connection:\n"
        for endpoint in endpoints.split(','):
            try:
                r = requests.get(endpoint, timeout=timeout, verify=False)
                conn_status = conn_status + "Port {} on {} is Healthy\n".format(endpoint.split(':')[-1], endpoint.split(':')[-2].replace('/',''))
            except (requests.ConnectionError, requests.Timeout) as e:
                logger.info("Error: {}".format(e))
                conn_status = conn_status + "Port {} on {} is Unhealthy\n".format(endpoint.split(':')[-1], endpoint.split(':')[-2].replace('/',''))

        body = body + conn_status
        api_url = f'https://api.telegram.org/bot{api_token}/sendMessage?text={body}&chat_id={chat_id}&parse_mode=Markdown'
        r = requests.post(api_url, headers=headers)
        logger.info(r.content)

        time.sleep(notify_interval)


if __name__ == "__main__":
    notifier()
