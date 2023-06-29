module.exports = Object.freeze({
    MODEL_API: 'https://127.0.0.1:8501/api/user/pattern',
    MODEL_API_WORKER: 'https://127.0.0.1:8500/api/user/pattern',
    TIMEOUT_API: 3000,

    BACKEND_API: 'https://192.168.0.4:8999/api/user/pattern',
    LAST_VERIFY: 86400,

    STORE_IMAGE: true,
    NUM_IMAGE: 20,

    CAMERA: {
        'zone': {'xmin': 0, 'ymin': 0, 'xmax': 720, 'ymax': 1280},
        'face_minsize': 80,
        'intruder_score': 1.0,
        'matched_score': 0.7,
    }
});
