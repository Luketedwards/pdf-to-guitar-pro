from django.shortcuts import render

def home(request):
    return render(request, 'index.html')


def upload_pdf(request):
    if request.method == 'POST':
        # handle file upload and conversion here
        return render(request, 'pdf_upload_success.html')
    else:
        return render(request, 'upload.html')