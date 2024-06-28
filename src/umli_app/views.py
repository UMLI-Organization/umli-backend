from typing import Dict, IO
from collections import deque


import pika
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpRequest
from django.core.files.uploadedfile import UploadedFile
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db import transaction

from umli_app.message_broker.producer import send_uploaded_file_message, create_message_data
from .models import UmlModel, UmlFile
from .forms import SignUpForm, AddUmlModelForm, AddUmlFileForm, AddUmlFileFormset
from umli_app.utils.forms_utils import get_form_index, create_handler_for_copying_forms, create_copies_of_forms_from_formset, apply_to_request_post_elements, FormCopiesConfig

def home(request: HttpRequest) -> HttpResponse:

    if request.method == "POST":
        return login_user(request)
    else:
        uml_models = UmlModel.objects.prefetch_related("metadata", "source_files").all()
        return render(request, "home.html", {"uml_models": uml_models})


def login_user(request: HttpRequest) -> HttpResponse:
    username = request.POST.get("username")
    password = request.POST.get("password")
    user = authenticate(request, username=username, password=password)

    if user is not None:
        login(request, user)
        messages.success(request, f"Welcome {username}")
        return redirect("home")
    else:
        messages.warning(request, "Invalid credentials")
        return redirect("home")


def logout_user(request: HttpRequest) -> HttpResponse:
    logout(request)
    messages.success(request, "You have been logged out")
    return redirect("home")


def register_user(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()

            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password1")
            user = authenticate(request, username=username, password=password)
            login(request, user)

            messages.success(request, "You have successfully registered")
            return redirect("home")
    else:
        form = SignUpForm()

    return render(request, "register.html", {"form": form})


def uml_model(request: HttpRequest, pk: int) -> HttpResponse:
    if request.user.is_authenticated:
        uml_model = UmlModel.objects.prefetch_related("metadata").get(id=pk)

        # Read and decode the file content
        # TODO: redo after final file format decision
        try:
            xml_content = uml_model.source_file.read().decode("utf-8")

            import xml.dom.minidom as minidom

            # Pretty-print the XML content
            pretty_xml = minidom.parseString(xml_content).toprettyxml(indent="  ")
        except ValueError:
            pretty_xml = uml_model.formatted_data

        return render(
            request,
            "uml-model.html",
            {"uml_model": uml_model, "pretty_xml": pretty_xml},
        )
    else:
        messages.warning(request, "You need to be logged in to view this page")
        return redirect("home")


def delete_uml_model(request: HttpRequest, pk: int) -> HttpResponse:
    if request.user.is_authenticated:
        uml_model_to_delete = UmlModel.objects.get(id=pk)
        uml_model_to_delete.delete()
        messages.success(request, "UML model has been deleted.")
        return redirect("home")
    else:
        messages.warning(request, "You need to be logged in to delete this UML model")
        return redirect("home")


def translate_uml_model(request: HttpRequest, pk: int) -> HttpResponse:
    if request.user.is_authenticated:
        try:
            # TODO: inject with dependency injection
            # TODO: take from env
            connection = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq"))
            channel = connection.channel()

            send_uploaded_file_message(
                channel,
                create_message_data(
                    id=pk,
                )
            )
        except Exception as ex:
            error_message = f"Connection with the translation service cannot be established: {ex}"
            messages.warning(request, error_message)
            return redirect("home")


def _decode_file(file: IO, encoding: str = 'utf-8') -> str:
    try:
        return file.read().decode(encoding)
    except UnicodeDecodeError as ex:
        # TODO: add message
        return None


def add_uml_model(request: HttpRequest) -> HttpResponse:
    SOURCE_FILES_FORMSET_PREFIX = "source_files"
    if request.user.is_authenticated:
        if request.method == "POST":
            mutable_post_data = request.POST.copy()
            form = AddUmlModelForm(mutable_post_data, request.FILES)
            messages.success(request, f"POST: {mutable_post_data}")
            messages.success(request, f"Files: {request.FILES}")
            messages.success(request, f"Files items: {list(request.FILES.items())}")
            messages.success(request, f"Files keys: {list(request.FILES.keys())}")
            messages.success(request, f"Files lists: {list(request.FILES.lists())}")
            if form.is_valid():
                with transaction.atomic():
                    added_uml_model = form.save()

                    config_for_copies_of_forms_with_multiple_files = list()
                    for files_field_name, files_list in request.FILES.lists():
                        form_index = get_form_index(files_field_name, SOURCE_FILES_FORMSET_PREFIX)
                        file_format = mutable_post_data.get(f"{SOURCE_FILES_FORMSET_PREFIX}-{form_index}-format")
                        messages.success(request, f"Form index: {form_index}")
                        messages.success(request, f"file_format: {file_format}")
                        messages.success(request, f"files_list: {files_list}")

                        filenames = deque()
                        decode_files_callables = deque()

                        for file_in_memory in files_list:
                            filenames.append(file_in_memory.name)
                            # decode_files_callables.append(lambda : _decode_file(file_in_memory))
                            decode_files_callables.append(_decode_file(file_in_memory))
                            messages.warning(request, f"file_in_mem: {file_in_memory.name}")
                            messages.warning(request, f"file_in_mem encoding: {file_in_memory.encoding if hasattr(file_in_memory, 'encoding') else 'NO Encoding attr'}")
                            messages.warning(request, f"file_in_mem read: {file_in_memory.read().decode('utf-8')}")
                            messages.warning(request, f"file_in_mem second read: {file_in_memory.read().decode('utf-8')}")
                            

                        messages.success(request, f"filenames: {filenames}")
                        messages.success(request, f"decode_files_callables: {decode_files_callables}")
                        config_for_copies_of_forms_with_multiple_files.append(FormCopiesConfig(form_index, len(files_list), {'data': decode_files_callables, 'format': file_format, 'filename': filenames}))

                    messages.success(request, f"config: {config_for_copies_of_forms_with_multiple_files}")
                    handler_for_copying_forms = create_handler_for_copying_forms(SOURCE_FILES_FORMSET_PREFIX, config_for_copies_of_forms_with_multiple_files)                        
                    
                    messages.success(request, f"view- before apply - request_post: {mutable_post_data}")
                    updated_post_data = apply_to_request_post_elements(mutable_post_data, [handler_for_copying_forms], request)
                    messages.success(request, f"view- after apply - request_post: {mutable_post_data}")
                    messages.success(request, f"view- after apply - return_request_post: {updated_post_data}")

                    messages.success(request, f"Source files file: {files_field_name}\n Index: {form_index}")
            formset = AddUmlFileFormset(mutable_post_data)
            messages.warning(request, f"formset.is_valid() {formset.is_valid()}")
            if formset.is_valid():
                with transaction.atomic():
                    added_uml_model = form.save()
                    messages.success(request, f"Post data: {mutable_post_data}")
                    formset.instance = added_uml_model
                    formset.save()
                    messages.success(request, f"formset.instance: {formset.instance}")
                    return redirect("home")

        else:
            form = AddUmlModelForm()
            formset = AddUmlFileFormset(prefix=SOURCE_FILES_FORMSET_PREFIX)

        return render(request, "add-uml-model.html", {"form": form, "formset": formset})

    return redirect("home")


# TODO: do zmiany
def update_uml_files(files: Dict[str, UploadedFile], associated_model: UmlModel, format: str) -> HttpResponse:
    for file_name, file in files.items():
        UmlFile.objects.create(
            file=file.read(),
            format=format,
            filename = file_name,
            model=associated_model
        )

    return HttpResponse("Files have been updated.")


# TODO: prefetch files and use formset
def update_uml_model(request: HttpRequest, pk: int) -> HttpResponse:
    if request.user.is_authenticated:
        uml_model_to_update = UmlModel.objects.get(id=pk)
        form = AddUmlModelForm(request.POST or None, request.FILES or None, instance=uml_model_to_update)
        if form.is_valid():
            updated_model = form.save()
            update_uml_files(form.cleaned_data["source_files"], form.cleaned_data["format"], updated_model)

            translate_uml_model(request, updated_model.id)

            messages.success(request, "UML model has been updated.")
            return redirect("home")
        return render(request, "update-uml-model.html", {"form": form})
    else:
        messages.warning(request, "You need to be logged in to update this UML model")
        return redirect("home")


def bulk_upload_uml_models(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("home")
    else:
        messages.warning(request, "You need to be logged in to update this UML model")
        return redirect("home")

