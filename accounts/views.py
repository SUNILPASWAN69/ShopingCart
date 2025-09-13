from django.shortcuts import render,redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponseRedirect,HttpResponse
from django.contrib.auth import authenticate, login,logout
from django.contrib.auth.decorators import login_required
from .models import *
from products.models import *
from django.http import HttpResponseRedirect 
from accounts.models import *

# Create your views here.

def login_page(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        user_obj = User.objects.filter(username = email)
        if not user_obj.exists():
            messages.warning(request , 'Account not registered!!')
            return HttpResponseRedirect(request.path_info)
        
        if not user_obj[0].profile.is_email_verfied:
            messages.warning(request , 'Account not Verified!!')
            return HttpResponseRedirect(request.path_info)
        
        user_obj = authenticate(username = email ,password = password)
        if user_obj:
            login(request, user_obj)
            return redirect('/')
        else:
            messages.warning(request , 'Invalid Credentials!!')
            return HttpResponseRedirect(request.path_info)     
    return render(request,'accounts/login.html')
def logout_page(request):
    logout(request)
    return redirect('/')
def register_page(request):
    if request.method == "POST":
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm-password')
        
        if password == confirm_password:
            user_obj = User.objects.filter(username = email)
            if user_obj.exists():
                messages.warning(request , 'Email alreday exists')
                return HttpResponseRedirect(request.path_info)

            user_obj = User.objects.create(
                first_name = first_name,
                last_name = last_name,
                email = email,
                username = email,
            )           
            user_obj.set_password(password) 
            user_obj.save()

            messages.success(request, 'mail sent in your mail-box')
            return HttpResponseRedirect(request.path_info)
        else:
            messages.error(request, 'password and confirm_password is not same')
            return HttpResponseRedirect(request.path_info)
    return render(request, 'accounts/register.html')
        
def activate_email(request, email_token):
    try:
        user = Profile.objects.get(email_token=email_token)
        user.is_email_verfied = True
        user.save()
        return redirect('/')
    except Exception as e :
        return HttpResponse('inavlid email token')

@login_required
def cart(request):
    cart_obj= Cart.objects.filter(is_paid = False, user = request.user).first()
    if not cart_obj:
        messages.warning(request, 'Empty Cart')
        return HttpResponse('No active cart found')
    if request.method == 'POST':
        coupon = request.POST.get('coupon')
        coupon_obj = Coupon.objects.filter(coupon_code__icontains = coupon)
        if not coupon_obj.exists():
            messages.warning(request, 'Invalid Coupon')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        if cart_obj.coupon:
            messages.warning(request, 'Coupon already applied')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        
        if cart_obj.get_cart_total() < coupon_obj[0].minimum_amount:
            messages.warning(request, 'Minimum amount should be {}'.format(coupon_obj[0].minimum_amount))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        
        if coupon_obj[0].is_expired:
            messages.warning(request, 'Coupon is expired')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
                    
        cart_obj.coupon = coupon_obj[0]
        cart_obj.save()
        messages.success(request, 'Coupon applied')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    context = {'cart':cart_obj}
    return render(request,'accounts/cart.html',context)
@login_required
def add_to_cart(request,uid):
    user = request.user    # Ensure the user has a profile
    if not hasattr(user, 'profile'):
        Profile.objects.create(user=user)
    variant = request.GET.get('variant')
    product = Product.objects.get(uid = uid)
    cart , _ = Cart.objects.get_or_create(user = user , is_paid = False)
    cart_item = CartItems.objects.create(cart=cart,product=product)
    if variant:
        # print(variant)
        variant = request.GET.get('variant')    
        size_variant = SizeVariant.objects.get(size_name = variant)
        cart_item.size_variant = size_variant
        cart_item.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

def remove_cart(request,cart_item_uid):
    try:
        cart_item = CartItems.objects.get(uid = cart_item_uid)
        cart_item.delete()
    except Exception as e:
        print(e)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

def remove_coupon(request,cart_id):
    cart = Cart.objects.get(uid=cart_id)    
    cart.coupon = None
    cart.save()
    messages.success(request, 'Coupon Removed')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))