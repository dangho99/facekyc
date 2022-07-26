import json
import os
from tqdm import tqdm

from core import server
from core.model import NeighborSearch
from PIL import ImageDraw, Image, ImageFont
from util import dataio

class Predictor:
    def __init__(self, model_dir=None):
        self.model = NeighborSearch.load(model_dir)

    def predict(self, data):
        """
        data = [{
            "features": [ [], [] ],
            "locations": [ [], [] ],
            "image": ""},
            ...
        ]
        """
        # set color and font
        colors = ["red", "blue", "green"]
        font = ImageFont.truetype("Carlito-Regular.ttf", size=18)

        for d in tqdm(data, desc="Predict"):
            preds = self.model.predict(d['features'])
            """
            preds = [
                {"userid": "", "score": 0.},
                ...
            ]
            """
            if not len(preds):
                continue

            pil_image = Image.fromarray(dataio.convert_bytes_to_numpy_array(d['image']))
            draw = ImageDraw.Draw(pil_image)
            i = 0
            for (top, right, bottom, left), pred in zip(d['locations'], preds):
                if not pred["userid"]:
                    continue
                # text label
                name = ' '.join([pred["userid"], str(pred['score'])])
                # draw a box
                box_color = colors[i % len(colors)]
                draw.rectangle(((left, top), (right, bottom)), outline=box_color)
                # draw a label
                text_width, text_height = draw.textsize(name)
                draw.rectangle(((left, bottom - text_height - 10), (right, bottom)), fill=box_color, outline=box_color)
                draw.text((left + 6, bottom - text_height - 5), name, fill=(255, 255, 255, 255), font=font)
                i += 1
            
            # remove draw
            del draw
            # show image
            pil_image.show()
        
        return 


if __name__ == '__main__':
    model = Predictor(model_dir="./checkpoint/model")
    server.run(model)