from firebase_admin import auth, firestore

db = firestore.client()

class UserModel:
    def create_user(self, email, username, password):
        # Create user with Firebase Authentication
        user = auth.create_user(
            email=email,
            password=password
        )
        # Save additional user data in Firestore
        self.save_user_data(user.uid, username, email)

    def save_user_data(self, uid, username, email):
        doc_ref = db.collection('users').document(uid)
        doc_ref.set({
            'username': username,
            'email': email,
            'id':uid,
        })

    def save_pdf(self, user_id,created_at, destinationAddress,id,name,originAddress,pdf_url):
        doc_ref = db.collection('users').document(user_id).collection('pdf').document(id)
        doc_ref.set({
            "created_at":created_at,
            "destinationAddress":destinationAddress,
            "id":id,
            "name":name,
            "originAddress":originAddress,
            "pdf_url":pdf_url,
            "user_id":user_id
        })
# acha yaar yeh pdf_url  kay liye pehlay ap ko pdf upload karni paray gi waha say jo us ka url get ho ga sara kuch automatic hay tension laynay ki zaroorat
# waha par say ap us url ko pick karna aur uper jo sara data hay aik sath passsss
    def get_user_by_email(self, email):
        user_record = auth.get_user_by_email(email)
        if user_record:
            return {
                'uid': user_record.uid,
                'email': user_record.email
            }
        return None
