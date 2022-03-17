from . import auth
from flask import render_template
from .forms import RegistrationForm, LoginForm


@auth.route("/register")
def register():
    form = RegistrationForm()
    return render_template("register.html", form=form)

@auth.route("/login")
def login():
    form =LoginForm()
    return render_template("login.html", form=form)

@auth.route("/logout")
def logout():
    return "Logging out" #This is temporary ofc
