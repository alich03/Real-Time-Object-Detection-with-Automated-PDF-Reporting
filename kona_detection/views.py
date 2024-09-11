from django.shortcuts import render,redirect
from .models import Videos,Pdfs

import cv2
import matplotlib.pyplot as plt
import numpy as np
from ultralytics import YOLO
from datetime import datetime, timedelta
import os
# from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import pandas as pd

from django.core.files import File

from .forms import SignupForm, LoginForm
from .firestore_models import UserModel
from django.views import View
from firebase_admin import auth,firestore
from firebase_admin.exceptions import FirebaseError
from firebase_admin import storage

db = firestore.client()

import pyrebase
 
#credentials of firebase
config = {
  'apiKey': "AIzaSyDLmk7cvD6W2X0h2Wdhl2eKtM1KJpsCjxc",
  'authDomain': "safemov-a6bff.firebaseapp.com",
  'projectId': "safemov-a6bff",
  'storageBucket': "safemov-a6bff.appspot.com",
  'messagingSenderId': "468617986620",
  'appId': "1:468617986620:web:9d3e26d2864f0a66fdb939",
  'databaseURL': 'https://safemov-a6bff-default-rtdb.firebaseio.com'
}

# Initialising database,auth and firebase for further use 
firebase=pyrebase.initialize_app(config)
authe = firebase.auth()
database=firebase.database()
#db model
user_model = UserModel()
#yolo mdoel
mymodel=YOLO("kona_detection/models_specs/kona_model.pt")
#data in safemove to coresponding the claases in yolo
hs_code_duty_rates=pd.read_csv('kona_detection/models_specs/classes_hs_codes.csv',dtype={'hs_code': 'str'})
#classes in yolo
kona_classes = ['person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck','boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench','bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra','giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee','skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove','skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup','fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange','broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch','potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse','remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink','refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier','toothbrush']




def run_model_video(request):

    if request.method == 'POST':
        name = request.POST.get('name')
        origin = request.POST.get('origin')
        destination = request.POST.get('destination')
        video_file = request.FILES.get('video_file')
        if video_file:
            video_object = Videos.objects.create(title=name, video_file=video_file)
            video_url = video_object.video_file.url
            video_file_ = video_object.video_file
            video_url=os.path.join('media',video_url)
            if video_url.startswith('/'):
                video_url = video_url[1:]
            cap = cv2.VideoCapture(video_url)  

            frame_count=0
            objects_list = []
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                result=mymodel.predict(frame)
                cc_data=np.array(result[0].boxes.data)
                if len(cc_data) != 0:
                            xywh=np.array(result[0].boxes.xywh).astype("int32")
                            xyxy=np.array(result[0].boxes.xyxy).astype("int32")
                            for (x1, y1, _, _), (_, _, w, h), (_,_,_,_,conf,clas) in zip(xyxy, xywh,cc_data):
                                                cv2.rectangle(frame,(x1,y1),(x1+w,y1+h),(255,0,255),2)
                                                class_name=kona_classes[int(clas)]
                                                confidence=np.round(conf*100,1)
                                                text = f"{class_name}-{confidence}%"
                                                cv2.putText(frame, text, (x1,y1-10), cv2.FONT_HERSHEY_SIMPLEX,0.45,(0, 0, 255), 2)

                                                hs_code_data = hs_code_duty_rates.iloc[int(clas)]
                                                label = hs_code_data.label
                                                hs_code = hs_code_data.hs_code
                                                duty_rate = hs_code_data.duty_rate

                                                detected_obj={'name':label,'price':hs_code,'description':duty_rate}
                                                product_found = any(product['name'] == class_name for product in objects_list)

                                                if not product_found:
                                                            objects_list.append(detected_obj)
                                                else:
                                                    for index, product in enumerate(objects_list):
                                                        if product['name'] == label:
                                                            # and confidence > product['price']:
                                                            objects_list[index] = detected_obj
                cv2.imshow("live camera for kona", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            cap.release()
            cv2.destroyAllWindows()

            current_datetime=datetime.now()
            pdf_id = int(datetime.now().timestamp() * 1000) 
            if len(objects_list) != 0:
                output_pdf_file = f'{pdf_id}.pdf'
                create_product_pdf(objects_list, output_pdf_file,name,origin,destination,pdf_id)

                if output_pdf_file:
                   with open(output_pdf_file, 'rb') as file:
                        mypdf_file = File(file)
                    # Create an instance of Pdfs model and save it
                        # pdf_instance = Pdfs.objects.create(pdf_id=pdf_id, pdf_title=output_pdf_file, pdf_file=mypdf_file)
                        uid=request.session['id']
                        pdf_url = upload_pdf(uid,mypdf_file,pdf_id)
                        save_pdf_metadata(uid, current_datetime, destination, pdf_id, name, origin, pdf_url)


                return redirect("/")
    return render(request,'run_on_video.html')



class SignupView(View):
    def get(self, request):
        form = SignupForm()
        return render(request, 'signup.html', {'form': form})

    def post(self, request):
        form = SignupForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user_model.create_user(email, username, password)
            return redirect('login')
        return render(request, 'signup.html', {'form': form})




class LoginView(View):
    def get(self, request):
        form = LoginForm()
        return render(request, 'login.html', {'form': form})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            try:
                user=authe.sign_in_with_email_and_password(email,password)
                if user:
                        user_ref = db.collection('users').document(user['localId'])
                        user_doc = user_ref.get()
                        if user_doc.exists:
                            user_data = user_doc.to_dict()
                            username = user_data.get('username', 'Unknown')
                            session_id=user['idToken']
                            request.session['id']=str(user['localId'])
                            request.session['uid']=str(session_id)
                            request.session['username']=str(username)
                            request.session.save()
                        return redirect("/")
            
            except FirebaseError as e:
                form.add_error(None, f'Firebase error: {str(e)}')
            except Exception as e:  # Catching other possible errors
                form.add_error(None, f'General error: {str(e)}')


        return render(request, 'login.html', {'form': form})


    
class LogoutView(View):
    def get(self, request):
        if 'uid' in request.session:
            del request.session['uid']
        return redirect('/')



def create_product_pdf(products, output_file,name,origin,destination,pdf_id):
    # Create a PDF canvas
    c = canvas.Canvas(output_file, pagesize=letter)

    # Set the font and font size
    c.setFont("Helvetica", 12)

    # Set the starting y-coordinate for writing text
    y_position = 620
    logo_path="static\logo\white-logo.png"
    logo = ImageReader(logo_path)
    c.drawImage(logo, 250, y_position, width=160, height=120)
    y_position -= 20
    #wrte address
    # c.drawString(450, y_position, "Address:")
    #id ,tim date
    c.drawString(70, y_position, f"PDF ID: {pdf_id}")
    y_position -= 15
    c.setFont("Helvetica", 11)
    c.drawString(70, y_position, f"Name: {name}")
    y_position -= 15
    # c.drawString(400, y_position, "Benglore")
    c.drawString(70, y_position, f"Origin Address: {origin}")
    y_position -= 15
    # c.drawString(400, y_position, "Punjab,India")
    c.drawString(70, y_position, f"Destination Address: {destination}")
    
    # Write the header
    y_position -= 30
    # c.drawString(250, y_position, "Detected Object List")
    c.setFont("Helvetica", 12)
    y_position -= 20 
    c.drawString(70, y_position, "-----------------------------------------------------------------------------------------------------------------------")
    y_position -= 10 
    # c.drawString(30, y_position, f"Sr#")
    c.drawString(70, y_position, f"Label ")
    c.drawString(270, y_position, f"HS Code ")
    c.drawString(470, y_position, f"Duty rate ")
    y_position -= 10  # Move to the next line
    c.drawString(70, y_position, "-----------------------------------------------------------------------------------------------------------------------")
    y_position -= 20 
    c.setFont("Helvetica", 11)
    # Write each product's information
    for index, product in enumerate(products, start=1):
        if y_position <= 50:
            c.showPage()  # Start a new page
            c.setFont("Helvetica", 10)  # Reset font
            y_position = 730  # Reset y-coordinate
            # Write the header on the new page
            y_position -= 10 
            # c.drawString(0, y_position, f"Sr#")
            c.drawString(70, y_position, f"Label ")
            c.drawString(270, y_position, f"HS Code ")
            c.drawString(470, y_position, f"Duty rate ")
            y_position -= 10  # Move to the next line
            c.drawString(70, y_position, "-----------------------------------------------------------------------------------------------------------------------")
            y_position -= 20 

        # c.drawString(30, y_position, f"{index}.")
        c.drawString(70, y_position, f"{product['name']}")
        c.drawString(270, y_position, f"{product['price']}")
        c.drawString(470, y_position, f"{product['description']}")
        y_position -= 25  # Move to the next product

    # Save the PDF file
    c.save()




def upload_pdf(user_id, pdf_file,id):
    # Generate a unique ID for the PDF
    # id = int(datetime.now().timestamp() * 1000)  # Unix time in milliseconds
    bucket_name  = "safemov-a6bff.appspot.com"
    # Upload PDF to Cloud Storage
    bucket = storage.bucket(bucket_name)
    blob = bucket.blob(f'users/{user_id}/pdf/{id}.pdf')
    blob.upload_from_file(pdf_file, content_type='application/pdf')

    expiration = timedelta(days=1)
    # Get the download URL for the uploaded PDF
    pdf_url = blob.generate_signed_url(expiration=expiration, method='GET')

    return pdf_url


def save_pdf_metadata(user_id, created_at, destination_address, id, name, origin_address, pdf_url):
    db = firestore.client()
    doc_ref = db.collection('users').document(user_id).collection('pdf').document(str(id))
    doc_ref.set({
        "created_at": created_at,
        "destinationAddress": destination_address,
        "id": id,
        "name": name,
        "originAddress": origin_address,
        "pdf_url": pdf_url,
        "user_id": user_id
    })