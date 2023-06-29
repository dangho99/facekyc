// importing OpenCv library
const cv = require('opencv4nodejs');
const path = require('path')
const express = require("express");
const session = require("express-session");
const cookieParser = require("cookie-parser");

const request = require('request');
const https = require('https');
const fs = require('fs');

const app = express();

// Initialization
app.use(express.json({limit: '50mb'}));
app.use(cookieParser());
app.use(session({
	secret: "kotora",
	saveUninitialized: true,
	resave: true
}));

// Render templates
app.engine('html', require('ejs').renderFile);

// Import file
app.use(express.static(__dirname + '/'));

// Define const
const { CAMERA, MODEL_API, MODEL_API_WORKER, TIMEOUT_API, 
    STORE_IMAGE, NUM_IMAGE, BACKEND_API, LAST_VERIFY} = require('./constants');

// Creating get request simple route
app.get('/camera', (req, res)=>{
    if (req.query.cam_id) {
        req.session.cam_id = req.query.cam_id;
        cam_id = req.session.cam_id;
        res.render(__dirname + '/templates/camera.html', {'gate_id': cam_id});
    }
    else {
        res.render(__dirname + '/templates/404.html');
    }
});

app.get('/', (req, res)=>{
    res.render(__dirname + '/templates/404.html');
});

app.get('/photo', (req, res)=>{
    res.render(__dirname + '/templates/upload.html');
});

app.get("/photo/:user_id", (req, res) => {
    request({
        requestCert: false,
        rejectUnauthorized: false,
        url: BACKEND_API,
        method: 'GET',
        json: {
            user_id: req.params.user_id,
            zcfg_requester_address_email: 'admin@kotora.com.vn',
            zcfg_requester_id_passport: 'secretpassport',
            last_verify: LAST_VERIFY
        }
    }, function(error, response, body){
        // console.log(body);
        if (!body.zcfg_requester_address_email) {
            res.render(__dirname + '/templates/404.html');
        }
        else {
            res.render(__dirname + '/templates/photo.html', body);
        }
    });
})

const dir = path.resolve(path.join(__dirname, 'uploads'));
if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir);
}

app.post("/api/photo", (req, res) => {
    request({
        requestCert: false,
        rejectUnauthorized: false,
        url: BACKEND_API,
        method: 'POST',
        json: {...req.body, existed: true}
    }, function(error, response, body){
        console.log(body);
        res.json(body);
    });
})

app.delete("/api/photo", (req, res) => {
    request({
        requestCert: false,
        rejectUnauthorized: false,
        url: BACKEND_API,
        method: 'DELETE',
        json: req.body
    }, function(error, response, body){
        console.log(body);
        res.json(body);
    });
})

var count = 0;
function isNumeric(n){
    n = Number(n);
    return (typeof n == "number" && !isNaN(n));
}

app.post("/api/predict", (req, res) => {
    gate_id = req.body.gate_id;

    // Resize image
    let buffer = Buffer.from(req.body.images[0], 'base64'); 
    let frame = cv.imdecode(buffer);

    if (STORE_IMAGE && isNumeric(gate_id)){
        let image_path = path.join(dir, "G"+gate_id+"_"+count+'.jpg');
        cv.imwrite(image_path, frame);
        count += 1;
        if (count >= NUM_IMAGE) {
            count = 0;
        }
    }

    if (gate_id == 1 || gate_id == 3) {
        var model_api = MODEL_API
    }
    else if (gate_id == 2 || gate_id == 4) {
        var model_api = MODEL_API_WORKER
    }
    else {
        var model_api = null;
        console.log("Invalid gate.");
    }
    if (model_api != null) {
        // notify me when client connection is lost
        // req.on('close', function(){
            // console.log('Client closed the connection');
        // });

        req.setTimeout(TIMEOUT_API);

        request({
            requestCert: false,
            rejectUnauthorized: false,
            url: model_api,
            method: 'PUT',
            json: {
                images: [cv.imencode('.jpg', frame).toString('base64')],
                cam_config: {
                    'zone': [{
                        'xmin': CAMERA.zone.xmin, 'ymin': CAMERA.zone.ymin,
                        'xmax': CAMERA.zone.xmax, 'ymax': CAMERA.zone.ymax,
                        'gate': gate_id
                    }],
                    'face_minsize': CAMERA.face_minsize,
                    'intruder_score': CAMERA.intruder_score,
                    'matched_score': CAMERA.matched_score
                },
            }
        }, function(error, response, body){
            let current_time = new Date().toLocaleString('en-US', { hourCycle: 'h23'})
            if (error == null) {
                console.log("Time:", current_time, "Gate:", gate_id, "Prediction:", body.response);
                res.json(body.response);
            }
            else {
                res.json([]);
            }
        });
    }
    else {
        res.json([]);
    }
})

const server = https.createServer({
    key: fs.readFileSync('certs/key.pem'), // where's me key?
    cert: fs.readFileSync('certs/cert.pem'), // where's me cert?
    requestCert: false,
    rejectUnauthorized: false,
}, app);

server.listen(8443, function () {
    console.log("app listening on port 8443!");
});
