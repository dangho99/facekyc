import numpy as np
from flask import Blueprint, make_response, request, jsonify, render_template

from core.model import Core
from core.monitor import Monitor
from keeper.environments import SystemEnv

user = Blueprint('user', __name__)


@user.route('pattern', methods=['POST'])
def api_register_pattern():
    data = request.get_json()
    features = data.get("features")
    metadata = data.get('metadata')
    userid = metadata.get('userid')

    if (not user_id) or (not features):
        return make_response(jsonify({
            "data": {},
            "message": "Invalid format, userid & features can not be empty",
            "message_code": 400
        }), 400)

    matched_score = Core.verify(user_id=user_id, features=features)
    matched_score = np.mean(matched_score)

    if matched_score != -1:
        is_success = bool(matched_score < SystemEnv.matching_threshold)
        Monitor.capture(
            user_id=user_id,
            is_success=is_success,
            event_type="verify_pattern",
            predicted="Owner" if is_success else "Imposter",
            score=matched_score,
            data=features
        )

    result = Core.register(user_id=user_id, features=features)

    if not result:
        return make_response(jsonify({
            "data": {},
            "message": "Database is busy",
            "message_code": 10003
        }), 401)

    Monitor.capture(
        user_id=user_id,
        is_success=result,
        event_type="register_pattern",
        data=features
    )

    return render_template(
        "api_register_pattern_response.json.jinja",
        user_id=user_id,
        matched_score=np.mean(matched_score),
        dense_score=Core.dense_score(user_id),
        complete_score=Core.complete_score(user_id),
        message="Success",
        message_code=200,
        **Monitor.user_info(user_id)
    )


@user.route('pattern', methods=['DELETE'])
def api_reset_pattern():
    data = request.get_json()
    user_id = data.get("user_id")

    if not user_id:
        return make_response(jsonify({
            "data": {},
            "message": "Invalid format, user_id can not be empty",
            "message_code": 400
        }), 400)

    from database.user import User
    _user = User.query.filter_by(user_id=user_id).first()

    if not _user:
        return make_response(jsonify({
            "data": {},
            "message": "User is invalid",
            "message_code": 10001
        }), 401)

    result = Core.reset(user_id=user_id)

    if not result:
        return make_response(jsonify({
            "data": {},
            "message": "Database is busy",
            "message_code": 10003
        }), 401)

    Monitor.capture(
        user_id=user_id,
        is_success=result,
        event_type="reset_pattern",
        data={}
    )

    return render_template(
        "api_reset_pattern_response.json.jinja",
        message="Success",
        message_code=200
    )


@user.route('pattern', methods=['PUT'])
def api_verify_pattern():
    data = request.get_json()
    user_id = data.get("user_id")
    features = data.get("data")

    if (not user_id) or (not features):
        return make_response(jsonify({
            "data": {},
            "message": "Invalid format, user_id & data can not be empty",
            "message_code": 400
        }), 400)

    from database.user import User
    _user = User.query.filter_by(user_id=user_id).first()

    if not _user:
        return make_response(jsonify({
            "data": {},
            "message": "User is invalid",
            "message_code": 10001
        }), 401)

    matched_score = Core.verify(user_id=user_id, features=features)
    matched_score = np.mean(matched_score)

    is_success = bool(matched_score < SystemEnv.matching_threshold)

    if matched_score != -1:
        Monitor.capture(
            user_id=user_id,
            is_success=is_success,
            event_type="verify_pattern",
            predicted="Owner" if is_success else "Imposter",
            score=matched_score,
            data=features
        )

    if is_success:
        return render_template(
            "api_verify_pattern_response.json.jinja",
            matched_score=matched_score,
            message="Pattern is valid",
            message_code=10007
        )

    return render_template(
        "api_verify_pattern_response.json.jinja",
        matched_score=matched_score,
        message="Pattern is invalid",
        message_code=10006
    )
