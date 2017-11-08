#    Front
#  rtsp://eyezon:M@n39ha77an@10.1.1.206:554/videoMain
#  rtsp://eyezon:M@n39ha77an@10.1.1.206:554/videoSub
#    Back
#  rtsp://admin:M@n07ha77an@10.1.1.116:88/videoMain
#  rtsp://admin:M@n07ha77an@10.1.1.116:88/videoSub
#    Garage
#  rtsp://eyezon:M@n07ha77an@10.1.1.3:554/videoMain
#  rtsp://eyezon:M@n07ha77an@10.1.1.3:554/videoSub
import os
import cv2
import time
import argparse
import multiprocessing
import numpy as np
import tensorflow as tf

from utils.app_utils import FPS, WebcamVideoStream
from multiprocessing import Queue, Pool
from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as vis_util

CWD_PATH = os.getcwd()

# Path to frozen detection graph. This is the actual model that is used for the object detection.
MODEL_NAME = 'ssd_mobilenet_v1_coco_11_06_2017'
PATH_TO_CKPT = os.path.join(CWD_PATH, 'object_detection', MODEL_NAME, 'frozen_inference_graph.pb')

# List of the strings that is used to add correct label for each box.
PATH_TO_LABELS = os.path.join(CWD_PATH, 'object_detection', 'data', 'mscoco_label_map.pbtxt')

NUM_CLASSES = 90

# Loading label map
label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES,
                                                            use_display_name=True)
category_index = label_map_util.create_category_index(categories)


def detect_objects(image_np, sess, detection_graph):
    # Expand dimensions since the model expects images to have shape: [1, None, None, 3]
    image_np_expanded = np.expand_dims(image_np, axis=0)
    image_tensor = detection_graph.get_tensor_by_name('image_tensor:0')

    # Each box represents a part of the image where a particular object was detected.
    boxes = detection_graph.get_tensor_by_name('detection_boxes:0')

    # Each score represent how level of confidence for each of the objects.
    # Score is shown on the result image, together with the class label.
    scores = detection_graph.get_tensor_by_name('detection_scores:0')
    classes = detection_graph.get_tensor_by_name('detection_classes:0')
    num_detections = detection_graph.get_tensor_by_name('num_detections:0')

    # Actual detection.
    (boxes, scores, classes, num_detections) = sess.run(
        [boxes, scores, classes, num_detections],
        feed_dict={image_tensor: image_np_expanded})

    # Visualization of the results of a detection.
    vis_util.visualize_boxes_and_labels_on_image_array(
        image_np,
        np.squeeze(boxes),
        np.squeeze(classes).astype(np.int32),
        np.squeeze(scores),
        category_index,
        use_normalized_coordinates=True,
        line_thickness=8)
    return image_np



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-src', '--source', dest='video_source', type=int,
                        default=0, help='Device index of the camera.')
    parser.add_argument('-wd', '--width', dest='width', type=int,
                        default=480, help='Width of the frames in the video stream.')
    parser.add_argument('-ht', '--height', dest='height', type=int,
                        default=360, help='Height of the frames in the video stream.')
    parser.add_argument('-num-w', '--num-workers', dest='num_workers', type=int,
                        default=1, help='Number of workers.')
    parser.add_argument('-q-size', '--queue-size', dest='queue_size', type=int,
                        default=1, help='Size of the queue.')
    args = parser.parse_args()


    video_capture = cv2.VideoCapture("rtsp://eyezon:M@n39ha77an@10.1.1.206:554/videoMain")

    detection_graph = tf.Graph()
    with detection_graph.as_default():
        od_graph_def = tf.GraphDef()
        with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
            serialized_graph = fid.read()
            od_graph_def.ParseFromString(serialized_graph)
            tf.import_graph_def(od_graph_def, name='')


        config = tf.ConfigProto()
        config.gpu_options.allow_growth = True
        config.gpu_options.per_process_gpu_memory_fraction = 0.7
        sess = tf.Session(graph=detection_graph,config=config)


    while True:  # fps._numFrames < 120
        try :
            retValue, frame = video_capture.read()

            if frame is not None and retValue:

                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                if frame_rgb is not None:
                    frame_objects = detect_objects(frame_rgb, sess, detection_graph)

                    if frame_objects is not None:
                        output_rgb = cv2.cvtColor(frame_objects, cv2.COLOR_RGB2BGR)
                        if output_rgb is not None:
                            cv2.imshow('Video', output_rgb)

            else :
                print(retValue)
                if video_capture.isOpened() :
                    print("Abierto")
                    video_capture.release()
                    video_capture = cv2.VideoCapture("rtsp://eyezon:M@n39ha77an@10.1.1.206:554/videoMain")
                else :
                    print("Cerrado")
                

        except Exception as exp:   
            print(exp)


        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


    sess.close()
    video_capture.release()
    cv2.destroyAllWindows()
