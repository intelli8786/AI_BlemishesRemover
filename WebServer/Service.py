'''
이 모듈은 다음과 같은 기능을 제공합니다.
 - Streamlit 기반의 이미지 편집 웹서버를 구동합니다.
 - 세 가지 AI 이미지 복원 기능을 RestAPI 방식으로 호출합니다.
  - Inpainting : 이미지에서 특정 영역을 지우고, 지운 자리에 자연스러운 이미지를 추론해서 합성하는 기능을 제공합니다.
  - Super Resolution : 추론을 통한 자연스러운 업샘플링 기능을 제공합니다.
  - Deblur : 추론을 통해 자연스럽게 모션블러를 제거합니다.
 - 잘라내기, 배율을 통해 원하는 부분을 축소, 확대할 수 있습니다.
 - "원본", "뒤로", "앞으로" 히스토리 도구 : 세가지 히스토리 기능을 통해 과거 작업을 잃어버리지 않도록 편의 기능을 제공합니다.
 - "그리기 도구" : Free Draw, Rect 기능으로 원하는 영역을 선택할 수 있는 기능을 제공합니다.

작성자 김지성
최종 수정일 2021-12-16
'''

import sys, os
import requests
import time

import numpy as np
import cv2
import PIL.Image as Image

import streamlit as st
from streamlit_drawable_canvas import st_canvas

sys.path.append(os.path.join(os.getcwd(), 'Utils'))
ImageEncoder = __import__("ImageEncoder")
st.set_page_config(layout="wide")


def RefreshCanvas():
    st.session_state["canvas_id"] = time.time()
    st.session_state["mask"] = None

if st.session_state.get("canvas_id") is None:
    st.session_state["canvas_id"] = time.time()

if st.session_state.get("magnification") is None:
    st.session_state["magnification"] = 1

if st.session_state.get("history") is None:
    st.session_state["history"] = []

if st.session_state.get("history_idx") is None:
    st.session_state["history_idx"] = 0

def main():
    # 만약 이미지를 업로드 했다면 원본 이미지를 업로드이미지로 설정, 아니라면 데모 이미지로 설정
    image_uploaded = st.sidebar.file_uploader("Image Upload:", type=["png", "jpg"])
    if image_uploaded:
        image_origin = Image.open(image_uploaded)
    else:
        image_origin = Image.open('WebServer/demo.jpg')
    image_origin = np.array(image_origin.convert('RGB'))

    # 새 이미지를 업로드 했다면 image_current를 업데이트
    flag_newImage = st.session_state.get("image_origin") is None or not np.array_equal(st.session_state["image_origin"], image_origin)
    if flag_newImage:
        # 새로 업로드
        st.session_state["image_origin"] = image_origin
        st.session_state["image_current"] = image_origin
        RefreshCanvas()

    st.sidebar.text("AI 복원")
    flag_inpainting = st.sidebar.button('Inpainting')
    flag_superResolution = st.sidebar.button('Super Resolution')
    flag_deblur = st.sidebar.button('Deblurring')

    st.sidebar.text("이미지 편집")
    edit_col1, edit_col2 = st.sidebar.columns(2)
    flag_crop = edit_col1.button('잘라내기')

    magnification = st.sidebar.slider("배율 ", 0.1, 5., 1.)
    if st.session_state["magnification"] != magnification:
        st.session_state["magnification"] = magnification
        RefreshCanvas()

    st.text("히스토리")
    history_col1, history_col2, history_col3 = st.sidebar.columns(3)
    flag_history_origin = history_col1.button("원본")
    flag_history_back = history_col2.button("뒤로")
    if len(st.session_state["history"])-1 > st.session_state["history_idx"]:
        flag_history_front = history_col3.button("앞으로")
    else:
        flag_history_front = False

    # 원본 이미지 출력
    st.sidebar.text(f"원본 이미지 {st.session_state['image_origin'].shape[:2]}")
    st.sidebar.image(st.session_state["image_origin"])

    st.sidebar.text(f"현재 이미지 {st.session_state['image_current'].shape[:2]}")
    st.sidebar.image(st.session_state["image_current"])

    if flag_inpainting:
        if st.session_state.get("mask") is not None:
            image_bytes = ImageEncoder.Encode(st.session_state["image_current"], ext='jpg', quality=90)
            mask_bytes = ImageEncoder.Encode(st.session_state["mask"], ext='png')
            response = requests.post('http://jiseong.iptime.org:8786/inference/', files={'image': image_bytes, 'mask': mask_bytes})
            st.session_state["image_current"] = ImageEncoder.Decode(response.content)

            RefreshCanvas()
        else:
            st.error("Inpainting을 위해 영역을 선택해주세요!")

    elif flag_superResolution:
        if st.session_state.get("mask") is None:
            st.session_state["mask"] = np.ones(st.session_state["image_current"].shape[:2], dtype=np.uint8)
        mask_front = st.session_state["mask"]
        mask_background = np.array(st.session_state["mask"]==0,dtype=np.uint8)

        image_bytes = ImageEncoder.Encode(st.session_state["image_current"], ext='jpg', quality=90)
        response = requests.post('http://jiseong.iptime.org:8890/super', files={'image': image_bytes, 'ratio': (None, 4)})
        result = ImageEncoder.Decode(response.content)

        image_quarter = cv2.resize(st.session_state["image_current"], dsize=(0,0), fx=4, fy=4)
        mask_front_quarter = cv2.resize(mask_front, dsize=(0,0), fx=4, fy=4, interpolation=cv2.INTER_NEAREST)
        mask_background_quarter = cv2.resize(mask_background, dsize=(0, 0), fx=4, fy=4, interpolation=cv2.INTER_NEAREST)

        image_front = cv2.bitwise_and(result, result, mask=mask_front_quarter)
        image_background = cv2.bitwise_and(image_quarter, image_quarter, mask=mask_background_quarter)

        st.session_state["image_current"] = image_front+image_background
        RefreshCanvas()

    elif flag_deblur:
        if st.session_state.get("mask") is None:
            st.session_state["mask"] = np.ones(st.session_state["image_current"].shape[:2], dtype=np.uint8)
        mask_front = st.session_state["mask"]
        mask_background = np.array(st.session_state["mask"]==0,dtype=np.uint8)

        image_bytes = ImageEncoder.Encode(st.session_state["image_current"], ext='jpg', quality=90)
        response = requests.post('http://jiseong.iptime.org:8891/deblur', files={'image': image_bytes})  # TODO: change into server addr
        result = ImageEncoder.Decode(response.content)

        image_front = cv2.bitwise_and(result, result, mask=mask_front)
        image_background = cv2.bitwise_and(st.session_state["image_current"],st.session_state["image_current"],mask=mask_background)

        st.session_state["image_current"] = image_front+image_background
        RefreshCanvas()

    elif flag_crop:
        y, x = np.nonzero(st.session_state["mask"])
        x1, y1, x2, y2 = np.min(x), np.min(y), np.max(x), np.max(y)
        st.session_state["image_current"] = st.session_state["image_current"][y1:y2, x1:x2]
        RefreshCanvas()

    elif flag_history_back:
        if st.session_state["history_idx"] > 0:
            st.session_state["history_idx"] -= 1
        st.session_state["image_current"] = st.session_state["history"][st.session_state["history_idx"]]
        RefreshCanvas()

    elif flag_history_front:
        if len(st.session_state["history"]) > st.session_state["history_idx"]:
            st.session_state["history_idx"] += 1
        st.session_state["image_current"] = st.session_state["history"][st.session_state["history_idx"]]
        RefreshCanvas()

    elif flag_history_origin:
        st.session_state["image_current"] = st.session_state["image_origin"]
        st.session_state["history_idx"] = 0

    if flag_newImage:
        st.session_state["history"] = [st.session_state["image_current"]]
        st.session_state["history_idx"] = 0

    if any([flag_inpainting, flag_superResolution, flag_deblur, flag_crop]):
        st.session_state["history"].append(st.session_state["image_current"])
        st.session_state["history_idx"] = len(st.session_state["history"]) - 1

    # 그리기 도구
    drawing_mode = st.selectbox("그리기 도구:", ["Free Draw", "Rect", "Inpainting 영역 추천"])
    if drawing_mode == "Free Draw":
        tool = "freedraw"
        stroke_width = st.slider("Stroke width: ", 1, 50, 35)

    elif drawing_mode == "Rect":
        tool = "rect"
        stroke_width = 1

    elif drawing_mode == "Inpainting 영역 추천":
        tool = "freedraw"
        stroke_width = 1

    # 캔버스에 보여줄 이미지 * 배율
    image_view = cv2.resize(st.session_state["image_current"], dsize=(0, 0), fx=magnification, fy=magnification)

    # 캔버스 (이미지 업데이트를 위해 가장 마지막에 위치)
    h,w = image_view.shape[:2]
    drawing_objects = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",  # Fixed fill color with some opacity
        stroke_width=stroke_width,  # drawing 두께
        background_color="#eee",  # 캔버스 바탕 색
        background_image=Image.fromarray(image_view),
        update_streamlit=True,
        height=h,
        width=w,
        drawing_mode=tool,
        key=str(st.session_state["canvas_id"])
    )

    # 마스크 생성
    flag_draw = drawing_objects.json_data is not None and drawing_objects.json_data["objects"]  # draw 내용 유무
    if flag_draw:
        mask = np.zeros((h, w), np.uint8)
        for ob in drawing_objects.json_data["objects"]:
            if ob['type'] == 'rect':
                x1, y1, x2, y2 = ob['left'], ob['top'], ob['left'] + ob['width'], ob['top'] + ob['height']
                mask = cv2.rectangle(mask, (x1, y1), (x2, y2), (1), cv2.FILLED)
            if ob['type'] == 'path':
                for dot in ob['path']:
                    if dot[0] != 'Q':
                        continue
                    x1, y1, x2, y2 = map(int, dot[1:])
                    mask = cv2.line(mask, (x1, y1), (x2, y2), (1), stroke_width)

        h,w = st.session_state["image_current"].shape[:2]
        st.session_state["mask"] = cv2.resize(mask, dsize=(w,h))

    # 이미지 다운로드
    st.download_button(label="Image Download", data=ImageEncoder.Encode(st.session_state["image_current"]), file_name="image.jpg")
    
    # 별점
    score = st.radio("이 앱을 평가해주세요!",('5점', '4점', '3점', '2점', '1점'))
    image_star = Image.open('WebServer/star.png')
    cols = st.columns(20)
    for idx in range(int(score[0])):
        cols[idx].image(image_star)
    
    if st.button("평가하기"):
        # TODO: 별점, 어떤 inference인지 DB에 저장
        pass

if __name__ == "__main__":
    main()