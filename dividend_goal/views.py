from django.shortcuts import render, redirect
from .models import DividendGoal
from .forms import DividendGoalForm
from django.contrib.auth.decorators import login_required


@login_required
def set_or_edit_goal(request):
    try:
        goal = DividendGoal.objects.get(user=request.user)
    except DividendGoal.DoesNotExist:
        goal = None

    if request.method == 'POST':
        form = DividendGoalForm(request.POST, instance=goal)
        if form.is_valid():
            new_goal = form.save(commit=False)
            new_goal.user = request.user
            new_goal.save()
            return redirect('dashboard')  # redirect to wherever you want
    else:
        form = DividendGoalForm(instance=goal)

    return render(request, 'goal/set_or_edit_goal.html', {'form': form})