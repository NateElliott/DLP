from django.db import models
from django.contrib.auth.models import User

from .helpers import generator

# Create your models here.

class UserProfile(models.Model):
    user = models.OneToOneField(User,
                                on_delete=models.CASCADE,
                                primary_key=True)
    invite_code = models.TextField(max_length=24,blank=False)
    location_city = models.TextField(max_length=255, blank=True)
    location_state = models.TextField(max_length=255, blank=True)
    location_country = models.TextField(max_length=255, blank=True)
    team = models.CharField(max_length=255)


class SiteData(models.Model):
    name = models.CharField(max_length=255)
    invite_limit = models.IntegerField()

    def __str__(self):
        return self.name


class InviteCode(models.Model):
    invite_code = models.CharField(max_length=128,unique=True)
    staff = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    leader = models.CharField(max_length=128)
    email = models.CharField(max_length=128)
    sent = models.DateTimeField(auto_now_add=True)


    # TODO: move this to the views
    def create_code(self,leader,email,staff):
        self.invite_code = generator.id_generator(size=16)
        self.staff = staff
        self.email = email
        self.leader = leader
        self.save()
        return self.invite_code

    def __str__(self):
        return self.invite_code


class Modules(models.Model):
    name = models.CharField(max_length=255,blank=True)
    description = models.CharField(max_length=255, blank=True)
    module = models.FileField(upload_to='modules/')
    owner = models.CharField(max_length=255)
    upload_dtg = models.DateTimeField(auto_now_add=True)
    published = models.BooleanField(default=False)
    storage = models.CharField(max_length=32)


    def __str__(self):
        return self.name


class ModulesStatus(models.Model):
    module = models.ForeignKey(Modules, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=255)
    dtg = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.status

class Teams(models.Model):
    team = models.CharField(max_length=255)
    member = models.ForeignKey(User, on_delete=models.CASCADE)
    is_leader = models.BooleanField(default=False)


class MessageBoard(models.Model):
    title = models.TextField(max_length=255)
    posted_dtg = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    body = models.TextField()
    team = models.TextField(max_length=255)
    parent = models.TextField(max_length=32)

    def __str__(self):
        return self.title

class MessageViews(models.Model):
    message = models.ForeignKey(MessageBoard, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    data = models.TextField(max_length=255)
