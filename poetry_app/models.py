from django.db import models
from django.forms import ModelForm

class poetry_db(models.Model):
    title = models.CharField(max_length=50)
    author = models.CharField(max_length=50)
    content = models.TextField()
    def __str__(self):
        return self.title
class collections_db(models.Model):
    collection_name=models.CharField(max_length=50)
    collection_id=models.IntegerField()
    date_created=models.DateTimeField()
    def __str__(self):
       return self.collection_name

class poetry_collection(models.Model):
    poetry_id=models.ForeignKey(poetry_db,on_delete=models.CASCADE)
    collection_id=models.ForeignKey(collections_db,on_delete=models.CASCADE)
 
    def __str__(self):
        return f"{self.poetry_id.title} - {self.collection_id.collection_name}"
