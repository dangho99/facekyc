from flask import Blueprint, make_response, request, jsonify

feedback = Blueprint('feedback', __name__)


@feedback.route('', methods=['PUT'])
def api_send_fb():
    data = request.get_json()
    request_id = data.get("request_id")
    is_success = data.get("is_success")

    return make_response(jsonify({
        "data": {},
        "message": "",
        "message_code": 200
    }))
