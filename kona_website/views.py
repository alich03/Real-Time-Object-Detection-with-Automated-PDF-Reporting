from django.shortcuts import render
from django.shortcuts import render, redirect
import datetime
from kona_detection.models import Pdfs
from .decorators import login_required
from firebase_admin import firestore
from django.core.files import File

@login_required
def home(request):
    current_datetime=datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

    all_pdfs=Pdfs.objects.all()

    if request.session:
        uid=request.session['id']
        db = firestore.client()
        pdfs_ref = db.collection('users').document(uid).collection('pdf')
        user_pdfs = pdfs_ref.stream()
        pdf_list = []

        for pdf in user_pdfs:
            pdf_data = pdf.to_dict()
            pdf_list.append(pdf_data)

    
    return render(request, 'home.html',{'pdfs':all_pdfs,'pdf_list':pdf_list})







