from django.shortcuts import render

from .forms import SingleGETRequestForm


def single_get(request):
    form = SingleGETRequestForm()
    if request.method == 'POST':
        form = SingleGETRequestForm(request.POST)
        if form.is_valid():
            pass