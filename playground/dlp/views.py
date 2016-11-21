import os, zipfile, json
from operator import itemgetter

from django.http import HttpResponse

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.messages import error, info
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

from django.core import mail

from .forms import UserForm
from django.contrib.auth.models import User
from .models import User, InviteCode, Modules, UserProfile, ModulesStatus, MessageBoard, Teams, MessageViews
from .models import ResetPassword, UserLog

from .helpers import generator



def index(request):
    if request.user.is_authenticated():
        return redirect("/home/")

    else:
        return render(request,"login.html")


def register(request, invite="0000"):

    # POST REQUEST
    if request.method == "POST":

        current_invite = InviteCode.objects.filter(invite_code=request.POST['invite'])[0]

        if current_invite and current_invite.active:
            new_user = User.objects.create_user(request.POST['username'],current_invite.email,request.POST['password'])
            new_profile = UserProfile(user=new_user,
                                      invite_code=request.POST['invite'],
                                      team=current_invite.leader)

            team = Teams(team=current_invite.leader,
                         member=new_user)

            if current_invite.staff:
                new_user.is_staff = True

            new_profile.save()
            new_user.save()
            team.save()

            current_invite.active = False
            current_invite.save()

            info(request,"You have been registered, please login")
            return redirect("/login/")
        else:
            info(request,"There was an error with your request")
            return redirect("/")

    # GET REQUEST
    else:

        if request.user.is_authenticated():
            return redirect("/home/")

        else:
            invite = InviteCode.objects.filter(invite_code=invite)
            if invite:
                return render(request, "register.html", {'invite': invite[0]})
            else:
                info(request, "There was an error with your request.")
                return redirect("/")



def userlogin(request):
    if request.method == "POST":
        user = authenticate(username=request.POST['username'],
                            password=request.POST['password'])
        if user and user.is_active:

            login(request, user)
            UserLog(user=request.user,action="login",ip= request.META['REMOTE_ADDR']).save()

            info(request, "Welcome back")
            return redirect("/home/")

        else:
            error(request, "There was an error with your username/password")
            return redirect("/login/")

    else:
        form = UserForm()
        return render(request, "login.html", {'LoginForm': form})


@csrf_exempt
@login_required
def content_mgmt(request):

    if request.method == "POST":

        if request.POST["action"] == "delete":
            Modules.objects.filter(storage=request.POST["item"]).delete()
            info(request, "Module Deleted")
            return redirect("/home/")

        elif request.POST["action"] == "publish":
            mod = Modules.objects.get(storage=request.POST["item"])
            if mod.published:
                mod.published = False
                info(request, "Module Unpublished")
            else:
                mod.published = True
                info(request, "Module Published")
            mod.save()
            return redirect("/home/")

        elif request.POST["action"] == "upload":

            if request.FILES["module"]:
                # TODO: clean up path vars
                uploaded_file = request.FILES["module"]
                module_dir = "modules"
                ext = uploaded_file.name.split(".")
                storage = generator.id_generator(size=16)
                upload_dir = os.path.join(settings.MEDIA_ROOT,module_dir,storage,uploaded_file.name)

                fs = FileSystemStorage()
                fs.save(upload_dir, uploaded_file)
                if ext[1:len(ext)][0] == "zip" and os.path.isfile(upload_dir):
                    zip_ref = zipfile.ZipFile(upload_dir,"r")
                    zip_ref.extractall(os.path.join(settings.MEDIA_ROOT,module_dir,storage,"store"))
                    zip_ref.close()


                Modules(name=ext[0],
                        owner=request.user.username,
                        storage=storage,
                        module=uploaded_file.name).save()

                info(request, "Module Uploaded")
                return redirect("/module/detail/"+storage)

    else:
        return redirect("/home/")


@login_required
def home(request):

    modules = Modules.objects.all()
    personal_stats = ModulesStatus.objects.filter(user=request.user.id)
    return render(request, "home.html", {"modules": modules,
                                         "pstats":personal_stats,})


@login_required
def manage(request):

    if request.method == "POST":

        if request.POST.get('staff'):
            staff = True

        else:
            staff = False


        # TODO: move invite code stuff from models
        invite = InviteCode().create_code(leader=request.user,
                                          email=request.POST['email'],
                                          staff=staff)

        # send invite email.
        message = """
            # email/invite not working yet
            Good Day,
            You've been invited to use the Daimler Learning Platform

            http://localhost:8000/register/%s

            Cheers,
            The DLP Team
            """ % invite

        info(request, message)
        return redirect("/manage")

    total_invites = InviteCode.objects.all()
    pending_invites = total_invites.filter(active=True)
    team_all_invites = total_invites.filter(leader=request.user)
    team_pending_invites = total_invites.filter(active=True, leader=request.user)

    # superusers can see all teams.
    current_team = UserProfile.objects.filter(team=request.user)

    modules = Modules.objects.filter(published=True)

    stats = []
    for member in current_team:
        for mod in modules:
            a = ModulesStatus.objects.filter(user=member.user,module=mod).order_by("-dtg")[:1]

    return render(request, "manage.html", {"total_invites":total_invites,
                                           "pending_invites":pending_invites,
                                           "team_pending_invites":team_pending_invites,
                                           "team_all_invites":team_all_invites,
                                           "current_team":current_team,})


@login_required
def manageteam(request):
    current_team = UserProfile.objects.filter(team=request.user)
    return render(request, "manage.html", {"current_team":current_team})


def manageinvites(request):

    total_invites = InviteCode.objects.all()
    pending_invites = total_invites.filter(active=True)

    return render(request, "manage.html",{"total_invites":total_invites,
                                          "pending_invites":pending_invites,
                                          "page":"invites",
                                          "title":"Manage/Invites"})


def manageusers(request,user=None):

    if user:
        current_user = User.objects.filter(username=user)
        user_log = UserLog.objects.filter(user=current_user).order_by("-datetime")
        if current_user:
            return render(request, "manage.html", {"current_user": current_user[0],
                                                   "logs":user_log,
                                                   "page":"user",
                                                   "title":"Manage/User"})

        else:
            info(request,"There was an error with your request")
            return redirect("/manage/users/")
    else:

        sort_options = ["last_name","date_joined","last_login"]
        sort_type = "last_name"

        if request.GET.get("sort"):
            sort_by = request.GET.get("sort")

            if sort_by[0] == "-":
                sort_type = sort_by[1:len(sort_by)]
            else:
                sort_type = sort_by

            if sort_type in sort_options:
                sort_type = request.GET.get("sort")

        users = User.objects.all().order_by(sort_type)

        users_complete = []
        users_incomplete = []
        for user in users:
            if user.first_name and user.last_name:
                users_complete.append(user)
            else:
                users_incomplete.append(user)

        return render(request, "manage.html", {"users_complete": users_complete,
                                               "users_incomplete":users_incomplete,
                                               "page": "users",
                                               "sort": sort_type,
                                               "title": "Manage/Users"})


def managemodules(request):
    modules = Modules.objects.all()
    return render(request, "manage.html", {"modules": modules,
                                           "page": 'modules',
                                           "title": "Manage/Modules"})




@login_required
def module(request, storage=None):
    status = 0
    # TODO: this is a fucking mess
    if Modules.objects.filter(storage=storage):
        current_module = Modules.objects.get(storage=storage)
        if request.method == "POST" and int(request.POST["module_status"]) in range(0,101):
            if not ModulesStatus.objects.filter(user=request.user, module=current_module,status=100):
                ModulesStatus(user=request.user,
                              module=current_module,
                              status=request.POST["module_status"]).save()

        if not ModulesStatus.objects.filter(user=request.user,module=current_module):
            ModulesStatus(user=request.user,module=current_module,status=status).save()

        status = ModulesStatus.objects.filter(user=request.user, module=current_module).order_by("-dtg")[:1][0].status

        return render(request, "module.html", {"module": current_module,
                                               "status": status,})

    else:
        info(request, "There was an error with your request")
        return redirect("/home/")

@login_required
def module_detail(request, storage=None):

    if not request.user.is_superuser:
        info(request,"There was an error with your request")
        return redirect("/home/")


    if request.method == "POST":
        if Modules.objects.filter(storage=storage):
            current_module = Modules.objects.get(storage=storage)
            current_module.name = request.POST["title"]
            current_module.description = request.POST["description"]
            current_module.reviewed = True
            current_module.save()

        info(request,"Module updated")

        return redirect("/home/")

    else:
        if Modules.objects.filter(storage=storage):
            current_module = Modules.objects.get(storage=storage)
            project_data = []

            if not current_module.reviewed:

                project_file = os.path.join(settings.MEDIA_ROOT,"modules",storage,"store")+"\project.txt"
                if os.path.isfile(project_file):

                    with open(project_file) as project_file_text:
                        project_data_full = json.load(project_file_text)
                        project_data = {"title":project_data_full["metadata"]["title"],
                                        "description":project_data_full["metadata"]["description"],}

                    current_module.size = project_data_full["metadata"]["totalSlides"]
                    current_module.load_file = project_data_full["metadata"]["launchFile"]
                    current_module.save()

                else:
                    project_data = {"title":current_module.name}
                    current_module.size = 1
                    current_module.load_file = current_module.module
                    current_module.save()

            else:
                project_data = {"title": current_module.name,
                                "description":current_module.description}

            return render(request, "module-detail.html",{"module":current_module,
                                                         "module_detail":project_data})
        else:
            info(request, "There was an error with your requesttt")
            return redirect("/home/")


@login_required
def profile(request, username=None):

    if username and request.user.is_staff:
        if User.objects.filter(username=username):
            profile = User.objects.get(username=username)

            modules = Modules.objects.filter(published=True)

            module_status = []
            for mod in modules:
                if ModulesStatus.objects.filter(user=profile, module=mod):
                    module_status.append(ModulesStatus.objects.filter(user=profile, module=mod).order_by("-dtg")[:1][0])

            return render(request, "userprofile.html", {"profile": profile,
                                                        "module_status":module_status,
                                                        "modules":modules,})

        else:
            info(request, "There was an error with your request.")
            return redirect("/manage")



    if request.method == "POST":
        current_user = User.objects.get(username=request.user)
        current_user.email = request.POST['email']
        current_user.first_name = request.POST['firstname']
        current_user.last_name = request.POST['lastname']
        current_user.save()

        info(request, "Profile Updated")
        return redirect("/profile")

    else:
        current_user_profile = UserProfile.objects.get(user=request.user)
        return render(request, "profile.html",{"current_user_profile":current_user_profile,})

@login_required
def updatepassword(request):

    if request.method == "POST":
        user = User.objects.get(username=request.user.username)
        if request.POST["newpassword"] == request.POST["confirmpassword"] and user.check_password(request.POST["currentpassword"]):

            user.set_password(request.POST["confirmpassword"])
            user.save()
            info(request, "Account password has been updated")
            return redirect("/profile/")
        else:
            info(request, "There was an error with your request")
            return redirect("/profile/")

def forgotpassword(request):
    if request.method == "POST":

        user = User.objects.filter(email=request.POST["email"])[0]

        if user is not None and user.is_active:
            code = generator.id_generator(size=32)
            temp_pass = generator.id_generator(size=64)
            ResetPassword(code=code,user=user).save()
            user.set_password(temp_pass)
            user.save()

            info(request, "Please check your email ("+code+")")
            return redirect("/")

        else:
            info(request, "There is no record of that email in our system")
            return redirect("/")

    else:
        return render(request, "forgotpassword.html")


def resetpassword(request, reset="0000"):
    if request.method == "POST":

        re = ResetPassword.objects.filter(code=request.POST["code"])[0]

        if re is not None and re.active:
            if request.POST["newpassword"] == request.POST["confirmpassword"]:
                re.active = False
                re.user.set_password(request.POST["confirmpassword"])
                re.user.save()
                re.save()

            info(request, "Your password has been reset, please login")
            return redirect("/")
        else:
            info(request, "There was a problem with your request")
            return redirect("/")

    else:

        re = ResetPassword.objects.filter(code=reset)[0]

        if re is not None and re.active:
            return render(request, "resetpassword.html",{"reset":re})
        else:
            info(request, "There was a problem with your request")
            return redirect("/")




@login_required
def userlogout(request):

    UserLog(user=request.user, action="logout", ip=request.META['REMOTE_ADDR']).save()
    logout(request)
    return redirect("/home/")


@login_required
def message(request, message_id=None):

    myprofile = UserProfile.objects.get(user=request.user)
    board = MessageBoard.objects.filter(team=myprofile.team, parent=0).order_by("-id")
    board_views = MessageViews.objects.filter(user=request.user)

    if request.method == "POST":

        try:

            MessageBoard(body=request.POST["body"],
                         author=request.user,
                         parent=request.POST["parent"],
                         team=myprofile.team).save()

            info(request,"beta message")
            return redirect("/message/" + request.POST["parent"])
        except:
            MessageBoard(title=request.POST["title"],
                         body=request.POST["body"],
                         author=request.user,
                         parent=0,
                         team=myprofile.team).save()
            info(request, "Message Posted")
            return redirect("/message/")


    if message_id:
        try:
            payload = MessageBoard.objects.get(id=message_id)
            payload_reply = MessageBoard.objects.filter(parent=message_id)
            if not MessageViews.objects.filter(message=payload, user=request.user, data="view"):
                MessageViews(message=payload, user=request.user, data="view").save()
        except:
            info(request, "There was a problem with your request")
            return redirect("/message/")

    else:
        payload=None
        payload_reply=None

    return render(request, "message.html", {"board":board,
                                            "views":board_views,
                                            "payload":payload,
                                            "payload_reply":payload_reply})


