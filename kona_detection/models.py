from django.db import models

class Videos(models.Model):
    
    title = models.CharField(max_length=255)
    video_file = models.FileField(upload_to='videos/')

    def __str__(self):
        return self.title
    

class Pdfs(models.Model):
    
    pdf_id = models.CharField(max_length=255)
    pdf_title = models.CharField(max_length=255)
    pdf_file = models.FileField(upload_to='pdfs/')

    def __str__(self):
        return self.pdf_title
