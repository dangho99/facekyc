module.exports = Object.freeze({

    CAM_CHECKIN: {
        'model_api': 'https://192.168.0.7:8501/api/user/pattern',  // IP cua AIBox tang 3
        'url': 'CamTruoc_T3.mp4',
        'zone': [
            {'xmin': 250, 'ymin': 100, 'xmax': 750, 'ymax': 500, 'gate': 1},
            {'xmin': 800, 'ymin': 100, 'xmax': 1100, 'ymax': 500, 'gate': 2}
        ],
        'face_minsize': 4,
        'frame_ratio': 0.5,
        'intruder_score': 0.6,
        'matched_score': 0.1,
        'output_fps': 0.65
    },

    CAM_CHECKOUT: {
        'model_api': 'https://192.168.0.7:8500/api/user/pattern',  // IP cua AIBox tang 3
        'url': 'CamSau_T3.mp4',
        'zone': [
            {'xmin': 275, 'ymin': 100, 'xmax': 475, 'ymax': 400, 'gate': 3}
        ],
        'face_minsize': 4,
        'frame_ratio': 0.65,
        'intruder_score': 0.7,
        'matched_score': 0.15,
        'output_fps': 0.65
    },

    INPUT_WIDTH: 1920,
    INPUT_HEIGHT: 1080,
    INPUT_FPS: 25,

    OUTPUT_WIDTH: 1280,
    OUTPUT_HEIGHT: 720
});
