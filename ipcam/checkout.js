// importing OpenCv library
const cv = require('opencv4nodejs');
const path = require('path')
const express = require('express');
const request = require('request');
// const {drawBlueRect} = require('./utils');

const app = express();
const server = require('http').Server(app);
const io = require('socket.io')(server, 
    {
    cors: {
        origin: "*",
        methods: ["GET", "POST"],
        transports: ['websocket', 'polling'],
        credentials: true
    },
    allowEIO3: true
});
var constants = require('./constants');

// We will now create a video capture object.
const wCap = new cv.VideoCapture(constants.CAM_CHECKOUT.url);

//Setting the height and width of object
wCap.set(cv.CAP_PROP_FRAME_WIDTH, constants.OUTPUT_WIDTH);
wCap.set(cv.CAP_PROP_FRAME_HEIGHT, constants.OUTPUT_HEIGHT);

// Import file
app.use(express.static(__dirname + '/'));

// Creating get request simple route
app.get('/', (req, res)=>{
    res.sendFile(path.join(__dirname, 'index.html'));
});

var infer_frame = '';

// Using setInterval to read the image every one second.
setInterval(async () => {

    // Reading image from video capture device
    var frame = wCap.read();

    if (frame.empty) {
        console.log('No frame captured!');
        try {
            wCap.reset();
            console.log('Reset camera success!')
        }
        catch (error) {
            console.log('Reset error:', error);
        }
        // throw new Error('No frame captured!');
    }
    else {
        // Resize
        frame = frame.resize(constants.OUTPUT_HEIGHT, constants.OUTPUT_WIDTH);
        infer_frame = frame;

        // Draw detection zone
        constants.CAM_CHECKOUT.zone.forEach((zone, i) => {
            frame.drawRectangle(new cv.Rect(
                zone.xmin, zone.ymin, zone.xmax - zone.xmin, zone.ymax - zone.ymin
            ), new cv.Vec3(0, 0, 255), 1, cv.LINE_8);
        });

        // Encoding the image with base64.
        let image = cv.imencode('.jpg', frame).toString('base64');
        io.emit('image', image);
    }
}, 1000 / constants.INPUT_FPS)

// Using setInterval to predict
setInterval(async () => {
    try {
        // cv.imwrite('data/' + Date.now() + '.jpg', infer_frame);
        request({
            rejectUnauthorized: false,
            url: constants.CAM_CHECKOUT.model_api,
            method: 'PUT',
            json: {
                images: [cv.imencode('.jpg', infer_frame).toString('base64')],
                cam_config: constants.CAM_CHECKOUT,
            }
          }, function(error, response, body){
            let current_time = new Date().toLocaleString('en-US', { hourCycle: 'h23'})
            if (error == null) {
                console.log("Time:", current_time, "Prediction:", body.response);
                io.emit('info', body.response);
            }
          });
    } catch (error) {
        console.log(error);
    }
}, 1000 / constants.CAM_CHECKOUT.output_fps)

server.listen(3000, function () {
    console.log("app listening on port 3000!");
});
