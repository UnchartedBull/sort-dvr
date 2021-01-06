import cv2
import numpy as np
import pytesseract
import logging
import time
import re

from fuzzy_match import match_modelname, load_modelnames

SEARCH_DISTANCE = 120


def dilate(image):
    kernel = np.ones((4, 4), np.uint8)
    return cv2.dilate(image, kernel, iterations=1)


def erode(image):
    kernel = np.ones((3, 3), np.uint8)
    return cv2.erode(image, kernel, iterations=1)


def apply_mask(image):
    lower_bound = np.array([0, 0, 0], dtype="uint16")
    upper_bound = np.array([215, 215, 215], dtype="uint16")
    return cv2.inRange(image, lower_bound, upper_bound)


def resize_image(image):
    return cv2.getRectSubPix(image, (375, 80), (344, 60))


def ocr(image):
    start_time = time.time()
    custom_oem_psm_config = r"--oem 1 --psm 4"
    detected_text = pytesseract.image_to_data(image,
                                              output_type="data.frame",
                                              config=custom_oem_psm_config)
    detected_text = detected_text[detected_text.conf != -1]
    text = None
    confidence = None

    try:
        text = detected_text.groupby("page_num")["text"].agg(" ".join)[1]
        confidence = round(
            detected_text.groupby("page_num")["conf"].mean()[1], 2)
    except:
        text = ""
        confidence = 0

    # logging.debug('OCR detected %s (%s%% confidence) in %ss', text, str(confidence), str(round(time.time() - start_time, 2)))

    return (text, confidence, image)


def extract_name_from_still(image):
    dilated = dilate(image)
    eroded = erode(dilated)
    masked = apply_mask(eroded)
    return ocr(masked)


def get_model_from_filename(filename):
    result = re.search("\[(.*)\]", filename)
    if not result:
        return None
    else:
        return result.group(1)


def get_modelname(recording, start_frame, end_frame):
    frame_to_search = start_frame

    ocr_text = None
    ocr_confidence = 0
    masked_image = None
    matched_model = None
    match_similarity = 0

    load_modelnames()

    while frame_to_search + SEARCH_DISTANCE - 1 < end_frame:
        recording.set(cv2.CAP_PROP_POS_FRAMES, frame_to_search)
        _, frame = recording.read()
        frame = resize_image(frame)

        (text, confidence, image) = extract_name_from_still(frame)
        (match, similarity) = match_modelname(text)

        if similarity > match_similarity and confidence > ocr_confidence - 10:
            logging.debug(
                "Better match: %s (%s%% confidence, %s%% similarity)",
                match,
                str(confidence),
                str(similarity),
            )
            ocr_text = text
            ocr_confidence = confidence
            masked_image = image
            matched_model = match
            match_similarity = similarity

        frame_to_search += SEARCH_DISTANCE

    if ocr_confidence < 75 or match_similarity < 75:
        raise Exception("unsure result")

    return (ocr_text, ocr_confidence, matched_model, match_similarity,
            masked_image)


def write_mask(filename, mask_image):
    cv2.imwrite(filename, mask_image)
    logging.debug("Saved model name image mask at %s", filename)
