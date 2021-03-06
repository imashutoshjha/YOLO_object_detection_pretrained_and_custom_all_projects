import numpy as np
import cv2
#first point
frame=0
file_video_stream=cv2.VideoCapture('images/car_vdo.mp4') #0 index for webcam,for external camera index 1,2,3
while (file_video_stream.isOpened()):
    ret,current_frame=file_video_stream.read()
    img_to_detect=current_frame

    img_height=img_to_detect.shape[0]
    img_width=img_to_detect.shape[1]

    img_blob=cv2.dnn.blobFromImage(img_to_detect,1/255,(416,416),swapRB=True,crop=False)
    #accepted sizes are 320Ã—320,416Ã—416,608Ã—608. More size means more accuracy but less speed
    class_labels = ["number_plate"]
#
    class_colors = ["0,255,0"]#list of 5 colors in form of RGB for all the classes
    class_colors = [np.array(every_color.split(",")).astype("int") for every_color in class_colors]
    class_colors = np.array(class_colors)
    class_colors = np.tile(class_colors,(1,1))
    # print(class_colors)

    #model creation from the weights and cfg
    yolo_model = cv2.dnn.readNetFromDarknet('model/cov_yolov4(1).cfg','model/yolov4_final.weights')

    yolo_layers = yolo_model.getLayerNames()
    #print(len(yolo_layers)) #254 layers
    for yolo_layer  in yolo_model.getUnconnectedOutLayers():
        print(yolo_layers[yolo_layer[0]-1])
    yolo_output_layer = [yolo_layers[yolo_layer[0] - 1] for yolo_layer in yolo_model.getUnconnectedOutLayers()]
    # print(f"yolo output layer is : {yolo_output_layer}")
    yolo_model.setInput(img_blob)
    obj_detection_layers = yolo_model.forward(yolo_output_layer) #output for the image from the three output end
    #the YOLOv3 have 3 output layer which returns in dimension 13*13*3,26*26*3 and 51*52*3
    print(obj_detection_layers[0].shape) #i.e (507,85) or (13*13*3,85)
    print(obj_detection_layers[1].shape) #i.e (2028,85) or (26*26*3,85)
    print(obj_detection_layers[2].shape) #i.e (8112,85) or (52*52*3,85)
    class_ids_list = []
    boxes_list = []
    confidences_list = []

    for object_detection_layer in obj_detection_layers:
        for object_detection in object_detection_layer:
            all_scores=object_detection[5:]  #ALL CLASSES CONFIDENCE because from o to 4 is box cordinates(tx,ty,tw,th) and p0=object is present or not?
            predicted_class_id=np.argmax(all_scores) #calculates index of maximum confidence/probabilities class
            prediction_confidence=all_scores[predicted_class_id] #finds confidence of predicted class

            if prediction_confidence>0.50:
                bounding_box = object_detection[0:4] * np.array([img_width, img_height, img_width, img_height])
                (box_center_x_pt, box_center_y_pt, box_width, box_height) = bounding_box.astype("int")
                start_x_pt = int(box_center_x_pt - (box_width / 2)) #Doubt
                start_y_pt = int(box_center_y_pt - (box_height / 2)) #Doubt
                #Storing lists of class id,confidence and boundary details so that we can apply Non-Max suppresion to detect one best boundary for each object
                class_ids_list.append(predicted_class_id)
                confidences_list.append(float(prediction_confidence))
                boxes_list.append([start_x_pt, start_y_pt, int(box_width), int(box_height)])

                #applying NMS:- 0.5=Non-maxima suppresion,0.4=max-suppresion threshold
    max_value_ids = cv2.dnn.NMSBoxes(boxes_list, confidences_list, 0.5, 0.4)
    print(max_value_ids) #eg.[[3],[21],[14],[12],[28],[23],[5]]
    i=0
    for max_valueid in max_value_ids:
        max_class_id = max_valueid[0]  #index of that unique and only boundary box for each object that is most fitted bounday box from the boxes list.
        box = boxes_list[max_class_id]
        start_x_pt = box[0]
        start_y_pt = box[1]
        box_width = box[2]
        box_height = box[3]

        #get the predicted class id and label
        predicted_class_id = class_ids_list[max_class_id]
        predicted_class_label = class_labels[predicted_class_id]
        prediction_confidence = confidences_list[max_class_id]

        end_x_pt = start_x_pt + box_width
        end_y_pt = start_y_pt + box_height

        #To get the crop of that detected image
        crop_img=current_frame[start_y_pt:end_y_pt,start_x_pt:end_x_pt]
        if(crop_img.size!=0):
            cv2.imwrite("crops/object"+str(frame)+"_"+str(i)+".jpg",crop_img)
            i=i+1

            #to extract the number from the image
            from PIL import Image
            from pytesseract import image_to_string
            text = image_to_string(crop_img,lang="eng",config ='--psm 6')
            print("The car number plate is : "+str(text))

        box_color = class_colors[predicted_class_id]
        #print(box_color)

        box_color = [int(c) for c in box_color]

        predicted_class_label = "{}: {:.2f}%".format(predicted_class_label, prediction_confidence * 100)

        print("predicted object {}".format(predicted_class_label))

        cv2.rectangle(img_to_detect, (start_x_pt, start_y_pt), (end_x_pt, end_y_pt), box_color, 2) #2=thickness and this function is to make the rectangle

        cv2.putText(img_to_detect,str(text), (start_x_pt, start_y_pt-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, box_color, 1) #doubt start_y_pt-5 and this function is to put text on image

    frame=frame+1
    cv2.imshow("Detection Output", img_to_detect)
    if cv2.waitKey(1) &0xff==ord('q'):  #second point
        break
file_video_stream.release()
cv2.destroyAllWindows()
