import os, zipfile, json

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.messages import error, info
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

from .forms import UserForm, RegistrationForm, ModuleForm
from .models import User, InviteCode, Modules, UserProfile, ModulesStatus, MessageBoard, Teams, MessageViews
from .helpers import generator



def index(request):
    if request.user.is_authenticated():
        return redirect("/home/")

    else:
        form = UserForm()
        return render(request,"login.html",{'LoginForm':form})


def register(request, invite="0000"):
    if request.method == "POST":
        current_invite = InviteCode.objects.get(invite_code=request.POST['invite'])

        if current_invite.active:
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
            return redirect("/")
    else:
        if request.user.is_authenticated():
            return redirect("/home/")
        else:
            return render(request, "register.html",{'form': RegistrationForm(),'invite':invite})


def userlogin(request):
    if request.method == "POST":
        user = authenticate(username=request.POST['username'],
                            password=request.POST['password'])
        if user is not None:
            if user.is_active:
                login(request, user)
                info(request, "Welcome back")
                return redirect("/home/")

            else:
                info(request, "User is not active")
                return redirect("/login/")

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
        return redirect("/module/detail/" + request.POST["storage"])
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
                                        "description":project_data_full["metadata"]["description"],
                                        "size":project_data_full["metadata"]["totalSlides"],
                                        "load_file":project_data_full["metadata"]["launchFile"]}
                else:
                    project_data = {"title":current_module.name}
            else:
                project_data = {"title": current_module.name,
                                "description":current_module.description}

            return render(request, "module-detail.html",{"module":current_module,
                                                         "module_detail":project_data})
        else:
            info(request, "There was an error with your request")
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
def userlogout(request):

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


