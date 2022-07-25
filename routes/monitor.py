from flask import Blueprint, make_response, request, jsonify
import json
import os


monitor = Blueprint('monitor', __name__)


@monitor.route('trend', methods=['GET'])
def api_register_pattern():
    data = request.get_json()

    return make_response(None, 200)


@monitor.route('histogram', methods=['GET'])
def api_reset_pattern():
    data = request.get_json()

    return make_response(None, 200)


@monitor.route('pie', methods=['GET'])
def api_verify_pattern():
    data = request.get_json()

    return make_response(None, 200)
