module.exports = Object.freeze({

    CAM_CHECKIN: {
        'model_api': 'https://10.20.3.189:8501/api/user/pattern',
        'url': 'rtsp://admin:kotora2023@10.20.3.187:554/ch01/0',
        'zone': [
            {'xmin': 25, 'ymin': 80, 'xmax': 425, 'ymax': 700, 'gate': 1},
            {'xmin': 500, 'ymin': 80, 'xmax': 900, 'ymax': 700, 'gate': 2},
            {'xmin': 975, 'ymin': 80, 'xmax': 1250, 'ymax': 700, 'gate': 3}
        ],
        'face_minsize': 70,
        'intruder_score': 0.8,
        'matched_score': 0.70,
        'output_fps': 0.65
    },

    CAM_CHECKOUT: {
        'model_api': 'https://10.20.3.189:8500/api/user/pattern',
        'url': 'rtsp://admin:kotora2023@10.20.3.186:554/ch01/0',
        'zone': [
            {'xmin': 525, 'ymin': 100, 'xmax': 850, 'ymax': 650, 'gate': 3}
        ],
        'face_minsize': 50,
        'intruder_score': 0.8,
        'matched_score': 0.70,
        'output_fps': 0.65
    },

    INPUT_WIDTH: 1920,
    INPUT_HEIGHT: 1080,
    INPUT_FPS: 25,

    OUTPUT_WIDTH: 1280,
    OUTPUT_HEIGHT: 720,
});
