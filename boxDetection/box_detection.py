import numpy as np
import cv2 as cv
import pyrealsense2 as rs
import ipautils as ipa
import piece


class Detection:

    def __init__(self):
        self.kernal = cv.getStructuringElement(cv.MORPH_ELLIPSE, (3, 3))

        self.lower_red_1 = np.array([0, 146, 20])
        self.upper_red_1 = np.array([7, 255, 255])

        self.lower_red_2 = np.array([163, 146, 20])
        self.upper_red_2 = np.array([189, 255, 255])

        self.lower_blue = np.array([100, 100, 20])
        self.upper_blue = np.array([125, 255, 255])

        self.lower_green = np.array([50, 100, 20])
        self.upper_green = np.array([77, 255, 255])

        self.lower_box = np.array([0, 80, 20])
        self.upper_box = np.array([31, 255, 255])

        self.pipe = rs.pipeline()
        self.config = rs.config()
        self.config.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 30)
        self.config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 30)
        self.pipe.start(self.config)

        self.colors = [(0, 0, 255), (255, 0, 0), (0, 255, 0)]

        for x in xrange(0, 10):
            self.pipe.wait_for_frames()

    def detect_box(self):
        frames = self.pipe.wait_for_frames()
        color_frames = frames.get_color_frame()

        depth_frame = frames.get_depth_frame()
        depth_data = np.asanyarray(depth_frame.get_data())[160:720, 280:1200]

        img = np.asanyarray(color_frames.get_data())
        correction = img[160:720, 280:1200]
        correction = cv.rotate(correction, cv.ROTATE_180)

        min_depth = np.amin(depth_data[np.nonzero(depth_data)])

        if min_depth < 820:
            print "Blocked"
            cv.imshow("Dect", correction)
            cv.waitKey(1)
            return None

        hsv = cv.cvtColor(correction, cv.COLOR_BGR2HSV)

        mask_box = cv.inRange(hsv, self.lower_box, self.upper_box)

        mask_box = cv.morphologyEx(mask_box, cv.MORPH_CLOSE, self.kernal)
        mask_box = cv.morphologyEx(mask_box, cv.MORPH_OPEN, self.kernal)

        contour_box, hie_box = cv.findContours(mask_box, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

        box_rect = None
        box_contour = None

        for (i, c) in enumerate(contour_box):
            box_box = cv.minAreaRect(c)
            area = cv.contourArea(c)
            if (area < 35000) or (area > 40000):
                continue

            box_points = cv.boxPoints(box_box)
            box_contour = np.array(box_points, dtype="int")
            cv.drawContours(correction, [box_contour], -1, (255, 0, 0), 2)
            rect = ipa.order_points(box_contour)
            box_rect = rect
            cv.circle(correction, (int(rect[0, 0]), int(rect[0, 1])), 5, (0, 0, 255), -1)
            break

        if box_rect is None:
            cv.imshow("Dect", correction)
            cv.waitKey(1)
            return None

        mask_1 = cv.inRange(hsv, self.lower_red_1, self.upper_red_1)
        mask_2 = cv.inRange(hsv, self.lower_red_2, self.upper_red_2)

        mask_red = cv.bitwise_or(mask_1, mask_2)
        mask_red = cv.morphologyEx(mask_red, cv.MORPH_CLOSE, self.kernal, iterations=3)
        mask_red = cv.morphologyEx(mask_red, cv.MORPH_OPEN, self.kernal, iterations=2)

        mask_blue = cv.inRange(hsv, self.lower_blue, self.upper_blue)
        mask_green = cv.inRange(hsv, self.lower_green, self.upper_green)

        contours_red, hie_r = cv.findContours(mask_red, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
        contours_blue, hie_b = cv.findContours(mask_blue, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
        contours_green, hie_g = cv.findContours(mask_green, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

        contours = [contours_red, contours_blue, contours_green]
        points = []
        for (i, color) in enumerate(contours):
            for (j, c) in enumerate(color):
                piece_rect = cv.minAreaRect(c)
                area = cv.contourArea(c)

                if (piece_rect[1][0] > 80) or (piece_rect[1][1] > 80):
                    continue

                if (area < 500) or (area > 3000):
                    continue

                piece_bp = cv.boxPoints(piece_rect)
                piece_bp = np.array(piece_bp, dtype="int")
                rect = ipa.order_points(piece_bp)

                if cv.pointPolygonTest(box_contour, tuple(rect[0]), False) == -1:
                    continue

                cv.drawContours(correction, [piece_bp], -1, (0, 255, 0), 2)

                if i == 0:
                    color = "R"
                elif i == 1:
                    color = "B"
                else:
                    color = "G"

                if area > 1500:
                    height = ipa.distance(rect[0], rect[3])
                    width = ipa.distance(rect[0], rect[1])

                    int_orientation = 0 if width > height else 1
                    orientation = "Horizontal" if int_orientation == 0 else "Vertical"
                    cv.putText(correction, orientation, (int(rect[3, 0]) + 10, int(rect[3, 1]) + 10),
                               cv.FONT_HERSHEY_SIMPLEX,
                               0.5, (255, 255, 255), 2)

                    points.append(piece.Piece(rect[0, 0], rect[0, 1], color, int_orientation))
                else:
                    points.append(piece.Piece(rect[0, 0], rect[0, 1], color))

                cv.circle(correction, (int(rect[0, 0]), int(rect[0, 1])), 5, self.colors[i], -1)
                cv.waitKey(1)
        try:
            points_count = len(points)
            if points_count > 4:
                cv.imshow("Dect", correction)
                cv.waitKey(1)
                return None

            points_organized = [None, None, None, None]

            if points_count != 0:
                for i in xrange(0, points_count):
                    point = points[i]
                    for j in xrange(0, 4):
                        p_distance = ipa.distance((point.x, point.y), box_rect[j])
                        point.distance.append(p_distance)

                    point.position = point.distance.index(min(point.distance))

                # Verificar mesma posicao

                collision = False
                for i in xrange(0, points_count):
                    point = points[i]
                    for j in xrange(0, points_count):
                        if i == j:
                            continue
                        if point.position == points[j].position:
                            collision = True
                            break

                if collision:
                    print "Collision!"
                    cv.imshow("Dect", correction)
                    cv.waitKey(1)
                    return None

                for i in xrange(0, 4):
                    for j in xrange(0, points_count):
                        if points[j].position == i:
                            points_organized[i] = points[j]
                            continue

            pieces = "{} {}".format(points_organized[0].color if points_organized[0] is not None else "X",
                                    points_organized[1].color if points_organized[1] is not None else "X")

            cv.putText(correction, pieces, (50, 50),
                       cv.FONT_HERSHEY_SIMPLEX,
                       0.5, (255, 255, 255), 2)

            pieces = "{} {}".format(points_organized[3].color if points_organized[3] is not None else "X",
                                    points_organized[2].color if points_organized[2] is not None else "X")

            cv.putText(correction, pieces, (50, 70),
                       cv.FONT_HERSHEY_SIMPLEX,
                       0.5, (255, 255, 255), 2)

            cv.imshow("Dect", correction)
            cv.waitKey(1)

            return [points_organized[0].color if points_organized[0] is not None else "X",
                    points_organized[1].color if points_organized[1] is not None else "X",
                    points_organized[3].color if points_organized[3] is not None else "X",
                    points_organized[2].color if points_organized[2] is not None else "X"]

        except ValueError:
            cv.imshow("Dect", correction)
            cv.waitKey(1)
            return None
        except TypeError as exc:
            cv.imshow("Dect", correction)
            cv.waitKey(1)
            return None
