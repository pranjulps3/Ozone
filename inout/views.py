
from .forms import *
from django.http import HttpResponse, JsonResponse		
from django.shortcuts import render, redirect
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required#, csrf.csrf_protect
from inout.models import Profile
from contests.models import Contest, Problem
import random, socks, time
from django.core.mail import send_mail
from django.core import serializers
import os, json
from subprocess import *

from .global_vars import *




def clogin(request):
	if request.user.is_authenticated():
		if(request.user.is_active):
			return redirect("/home/")
		else:
			return redirect("/activate/")
	else:
		return auth_views.login(request, "inout/login.html")

def register(request):
	form = RegistrationForm()
	if request.user.is_authenticated():
		return redirect('/home/')
	elif request.method == 'POST':
		form = RegistrationForm(request.POST)
		if form.is_valid():
			u = User.objects.create_user(
				username = form.cleaned_data['username'],
				password = form.cleaned_data['password1'],
				is_active = False,
				first_name = form.cleaned_data['fname'],
				last_name = form.cleaned_data['lname'],
			)
			u.save()
			code = ""
			for i in range(6):
				code += chr(random.randrange(48, 122))
			p = Profile.objects.get(user=u)
			p.birth = form.cleaned_data['dob']
			p.activation_code = code
			print(code)
			p.rating = 1500
			p.save()

#			send_mail("Activation Code", "This is your activation Code: %s"%code, '<sender mail address>', [list of all the recipients])
			##Email the user
			usr = form.cleaned_data['username']
			form = ActivateForm(initial={})
			return render(request, 'inout/activate.html', {'usr':usr, 'form':form})
		else:
			return render(request, 'inout/register.html', {'form':form})
	else:
		return render(request, 'inout/register.html', {'form':form})
	

def activate(request):
	form = None
	try:
		if(request.method == "POST"):
			form = ActivateForm(request.POST)
			if(not request.user.is_active):
				if form.is_valid():
					cd = User.objects.get(username=request.POST.get('usr')).profile.activation_code
					print(cd)
					if(form.cleaned_data['act_code'] == cd):
						u = User.objects.get(username=request.POST.get('usr'))
						u.is_active = True
						u.activation_code = ""
						u.save()
#						st = "tmp/%s"%(request.POST.get('usr'))
#						os.mkdir(st)
						return redirect('/')
				return render(request, 'inout/activate.html', {'form':form})
			else:
				return redirect('/')
		else:
			return redirect('/')
	except:
		return redirect('/')
	
	
@login_required(login_url="/")
def index(request):
	return render(request, "inout/home.html")

@login_required(login_url='/')
def give_contests(request):
	try:
		c = Contest.objects.filter(allowed=0)
		if(len(c)==0):
			return JsonResponse({'status':'failure'}, status=200)
		contest_requests = serializers.serialize("json", c)
		return HttpResponse(contest_requests, content_type='application/json')

	except Exception as e:
		print(str(e))
		return JsonResponse({'status':'failure'}, status=404)
	

@login_required(login_url="/")
def allow(request):
	try:
		if(request.method == 'GET'):
			pp = int(request.GET.get('ag'))
			print pp
			c = Contest.objects.get(pk=request.GET.get('pk'))
			if(pp == 1):
				c.allowed = 1
				c.save()
				return JsonResponse({'done':'true'}, status=200)
			else:
				usr = c.admin
				usr.profile.tobecon = False
				usr.save()
				c.delete()
				return JsonResponse({'done':'true'}, status=200)
	except Exception as e:
		return JsonResponse({'done':'false'}, status=400)
	
	
@login_required(login_url='/')
def profile(request):
	return render(request, "inout/profile.html")


def is_alright(string, lang):
	string = string.lower()
	
	if('python' in lang):
		if("system(" in string or "os.popen" in string):
			return False
		else:
			return True
	elif lang == 'java':
		if(".getruntime(" in string or "processbuilder(" in string):
			return False
		else:
			return True
	elif "subprocess" in string:
		return False
	return True

@login_required(login_url='/')
def code_edit(request):
	form = CodeForm(initial={})
	if request.method == 'POST':
		form = CodeForm(request.POST)
		
		lang = request.POST.get('language')
		if not is_alright(str(request.POST.get('code')), lang):
			return HttpResponse("Invalid Code")
		code_path = os.path.join(os.getcwd(), "tmp/%s/code%s"%(request.user.username, extensions[lang]))
		input_file = os.path.join(os.getcwd(), "tmp/%s/inp.txt"%(request.user.username))
		with open(code_path, "w") as file:
			file.write(request.POST.get('code'))
		with open(input_file, "w") as file:
			file.write(request.POST.get('inpt'))
		if('python' in lang):
			run_cmd = "timeout 5s "+(cmd[lang][1]%(code_path, input_file))
			try:
				ps = check_output(run_cmd, shell=True, stderr=STDOUT)
				return HttpResponse(ps)
			except CalledProcessError as e:
				if("status 124" not in str(e)):
					retdata = "<pre>%s</pre>"%("<br>".join(e.output.split("\n")))
					return HttpResponse(retdata)
				elif("status 1" in str(e)):
					return HttpResponse("Time Exceeded: 5.0s")
				else:
					return HttpResponse("Server Error")
		else:
			outpt = "a.out" if lang != "java" else '';
			output_path = os.path.join(os.getcwd(), "tmp/%s/%s"%(request.user.username, outpt))
			compile_cmd = cmd[lang][0]%(code_path, output_path) if lang !='java' else "javac tmp/%s/code.java"%(request.user.username)
			print("Compiled")
			try:
				ps = check_output(compile_cmd, shell=True, stderr=STDOUT)
				run_cmd = "timeout 5s "+((cmd[lang][1]%(output_path, input_file)) if lang!='java' else "java -cp %s < %s"%(os.path.join(os.getcwd(),"tmp/%s Main"%request.user.username), input_file)) 
				ps = check_output(run_cmd, shell=True, stderr=STDOUT)
				return HttpResponse(ps)
			except CalledProcessError as e:
				retdata = "<pre>%s</pre>"%("<br>".join(e.output.split("\n")))
				return HttpResponse(retdata)

	else: return render(request, 'inout/code-edit.html', {'form':form})




