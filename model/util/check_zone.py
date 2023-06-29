from shapely.geometry import Polygon


class IntrusionTask():
    def __init__(self, zone, threshold=0.5):
        super().__init__()
        self.zone = zone
        self.threshold = threshold
        self.polygons = {}
        self.load_areas()

    def load_areas(self):
        for box in self.zone:
            if not box:
                continue
            self.polygons[str(box['gate'])] = Polygon(
                [
                    (box['xmin'], box['ymin']),
                    (box['xmax'], box['ymin']),
                    (box['xmax'], box['ymax']),
                    (box['xmin'], box['ymax'])
                ]
            )

    def check_intrusion(self, face_box):
        xmin, ymin, xmax, ymax = face_box
        poly_face = Polygon([(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)])

        result = None
        for i, poly_box in self.polygons.items():
            poly_box: Polygon
            if not poly_box.intersects(poly_face):
                continue
            if poly_box.intersection(poly_face).area / poly_face.area >= self.threshold:
                result = i
                break

        return result
