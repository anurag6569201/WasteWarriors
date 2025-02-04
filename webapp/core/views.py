from django.shortcuts import render, HttpResponse, redirect
from core.models import ScratchCard,redeemCards,total_pts
from django.db.models import Sum

from userauths.models import UserProfile
from userauths.forms import UserProfileForm
from django.views.generic.edit import FormView
from django.urls import reverse_lazy

from django.contrib.auth.decorators import login_required
from django.http import Http404

from userauths.views import ContactForm
from django.core.mail import send_mail
from django.template.loader import render_to_string


from django.shortcuts import render, redirect

from map_app.models import PredictionModel
from django.http import Http404

@login_required(login_url='userauths:sign-in')
def index(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            content = form.cleaned_data['content']

            html = render_to_string('core/email.html', {
                'name': name,
                'email': email,
                'content': content,
            })

            send_mail("The contact form subject", 'this is the message', email, ['anurag6569201@gmail.com'], html_message=html)
            return redirect("core:index")
    else:
        form = ContactForm()

    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        raise Http404("User profile not found")

    context = {
        'form': form,
        "user_profile": user_profile,
        "edit_mode": False,
    }

    if not request.user.verified:
        return render(request, 'core/index.html', context)
    else:
        return redirect("core:verifier")

@login_required
def user_redeem(request):
    user_profile = UserProfile.objects.get(user=request.user)
    redeem_card_instances = redeemCards.objects.all()
    vouchers = ScratchCard.objects.filter(user=request.user)
    tpscore = PredictionModel.objects.filter(user=request.user, is_redeemed=True).aggregate(Sum('score_of_image'))['score_of_image__sum'] or 0
    scoree = PredictionModel.objects.filter(user=request.user)
    totalpoints = PredictionModel.objects.filter(user=request.user, is_redeemed=True).aggregate(Sum('score_of_image'))['score_of_image__sum'] or 0

    redeem_card_pk = None
    totalpoin = totalpoints

    for crci in redeem_card_instances:
        if crci.is_redeemed:
            totalpoin -= crci.score

    if request.method == 'POST':
        total_pts_instance, created = total_pts.objects.get_or_create(user=request.user)
        redeem_card_pk = request.POST.get('redeem_card_pk')
        try:
            clicked_redeem_card_instance = redeemCards.objects.get(pk=redeem_card_pk)
        except redeemCards.DoesNotExist:
            pass
        else:
            scr = clicked_redeem_card_instance.score
            total_pts_instance.totalpts -= scr
            totalpoin = totalpoints
            totalpoin -= scr
            clicked_redeem_card_instance.is_redeemed = True
            clicked_redeem_card_instance.user = request.user  # Assigning the current user
            total_pts_instance.save()
            clicked_redeem_card_instance.save()

    total_pts_instance, created = total_pts.objects.get_or_create(user=request.user)
    ttp_pts = total_pts_instance.totalpts

    redeemcard = redeemCards.objects.all()
    print("Redeem Cards:", redeemcard)  # Debugging print

    calculated_score=tpscore+ttp_pts
    context = {
        "user_profile": user_profile,
        "vouchers": vouchers,
        "ttp_pts": ttp_pts,
        "tpscore": calculated_score,
        "score": scoree,
        "totalpoints": totalpoin,
        "redeemcard": redeemcard,
    }

    print(ttp_pts)  # Debugging print
    if not request.user.verified:
        return render(request, 'core/redeem.html', context)
    else:
        raise Http404("Page not found")
    
@login_required
def mainuser_profile(request):
    user_profile = UserProfile.objects.get(user=request.user)
    context = {
        "user_profile": user_profile,
        "edit_mode": False,
    }
    if not request.user.verified:
        return render(request, 'core/user.html', context)
    else:
        raise Http404("Page not found")

@login_required
def verifier(request):
    user_profile = UserProfile.objects.get(user=request.user)
    context = {
        "user_profile": user_profile,
        "edit_mode": False,
    }
    if request.user.verified:
        return render(request, 'core/index_verifier.html', context)
    else:
        raise Http404("Page not found")

@login_required
def user_profile(request):
    score = PredictionModel.objects.filter(is_redeemed=False)
    user_profile = UserProfile.objects.get(user=request.user)
    context = {
        "user_profile": user_profile,
        "edit_mode": False,
        "score":score,
    }
    if request.user.verified:
        return render(request, 'core/verifier.html', context)
    else:
        raise Http404("Page not found")
    
class UserProfileUpdateView(FormView):
    template_name = 'core/edit_user.html'

    form_class = UserProfileForm
    success_url = reverse_lazy('core:mainuser_profile')

    def get_form_kwargs(self):
        kwargs = super(UserProfileUpdateView, self).get_form_kwargs()
        kwargs['instance'] = UserProfile.objects.get(user=self.request.user)
        return kwargs

    def form_valid(self, form):
        form.save()
        return super(UserProfileUpdateView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(UserProfileUpdateView, self).get_context_data(**kwargs)
        context['user_profile'] = UserProfile.objects.get(user=self.request.user)
        return context

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.verified:
            self.template_name = 'core/edit_user.html'
            self.success_url = reverse_lazy('core:mainuser_profile')
        else:
            self.template_name = 'core/edit_verifier.html'
            self.success_url = reverse_lazy('core:profile')

        return super(UserProfileUpdateView, self).dispatch(request, *args, **kwargs)

def approve_prediction(request, prediction_id):
    if not request.user.is_authenticated:
        raise Http404("Page not found")
    prediction = PredictionModel.objects.get(pk=prediction_id)
    prediction.is_redeemed = True
    prediction.save()
    return redirect('core:profile')

