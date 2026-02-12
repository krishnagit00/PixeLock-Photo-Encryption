
from django.shortcuts import render

def history_view(request):
    # In a real "no-logs" scenario, history might be stored in the client's
    # browser localstorage and rendered via JS.
    # If server-side session history is required:
    transfer_history = request.session.get('transfer_history', [])
    
    context = {
        'transfer_history': transfer_history
    }
    # Using the template shown in Image 1 & 5
    return render(request, 'history.html', context)
#feedback logic
from django.http import JsonResponse
from .forms import FeedbackForm

def submit_feedback(request):
    if request.method == "POST":
        form = FeedbackForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'message': 'Thank you! Your feedback has been received.'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    return JsonResponse({'success': False, 'message': 'Invalid request'})