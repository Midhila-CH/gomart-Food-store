import uuid
from decimal import Decimal
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db.models import Sum
from django.shortcuts import redirect, render,HttpResponse,get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.core.files.storage import FileSystemStorage
from django.contrib.auth import authenticate,login as auth_login,logout
from django.contrib.auth.models import AnonymousUser
from django.core.paginator import Paginator
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.http import Http404
from django.contrib.auth.decorators import login_required
from .models import *
import json
from django.http import JsonResponse
import razorpay
from django.conf import settings
# Create your views here.
def index(request):
    category_display=Category.objects.all() 
    brand_display=Brand.objects.all()
    products=Product.objects.select_related('category')
    return render(request,"index.html",{'category_display':category_display,
                                        'brand_display':brand_display,'products':products})
def login(request):
    if request.method=="POST":
        email=request.POST.get("email")
        password=request.POST.get("password")
        user=authenticate(request,email=email,password=password)
        if user is not None:
            auth_login(request,user)
            return redirect('/checkout/')
        else:
            return render(request,"login.html",{"error":"Invlaid email or password"})
    return render(request,"login.html")
def user_ordered_products(request):
    user=request.user
    ordered_items=OrderItem.objects.filter(order__user=user).select_related('product','order')
    return render(request,'user_ordered_products.html',{'ordered_items':ordered_items})
def user_logout(request):
    logout(request)
    return redirect('/login/')
def signup(request):
    if request.method=="POST":
        username=request.POST.get('fname')
        email=request.POST.get('email')
        mobile_number=request.POST.get('number')
        password1=request.POST.get('password1')
        password2=request.POST.get('password2')
        if password1!=password2:
            messages.error(request,"password do not match")
            return redirect('/signup/')
        if User.objects.filter(username=username).exists():
            messages.error(request,"username already taken")
            return redirect('/signup/')
        if User.objects.filter(email=email).exists():
            messages.error(request,"email already used ")
            return redirect('/signup/')
        user=User.objects.create_user(username=username,email=email,password=password1)
        user.save()
        #auto login after signup
        auth_login(request,user)
        messages.success(request,"Registration Successfull!")
        return redirect('/login/')
    return render(request,"signup.html")
def admin_login(request):
    return render(request,"admin_login.html")
def check_admin_login(request):
    username=request.POST.get("username")
    password=request.POST.get("password")
    user=authenticate(request,username=username,password=password)
    if user is not None:
        return redirect("/admin_home/")
    else:
        return redirect("/admin_login/")
def admin_home(request):
    recent_orders = Order.objects.all().order_by('-created_at')[:5]
    customer_details=ShippingAddress.objects.all()[:3]
    Pending_order=Order.objects.filter(order_status='Pending').count()
    Delivered_order=Order.objects.filter(order_status='Delivered').count()
    Out_order=Order.objects.filter(order_status='Out For Delivery').count()
    return render(request,"admin_home.html",{'recent_orders':recent_orders,
                                             'customer_details':customer_details,
                                             'Pending_order':Pending_order,
                                             'Delivered_order':Delivered_order,
                                             'Out_order':Out_order
                                             })
@login_required
def my_orders(request):
    recent_orders = Order.objects.all().order_by('-created_at')
    return render(request,"my_orders.html",{'recent_orders':recent_orders})
def my_customers(request):
    customer_details=ShippingAddress.objects.all()
    return render(request,"my_customers.html",{'customer_details':customer_details})
def country(request):
    cntry_list=Country.objects.all()
    return render(request,"country.html",{"cntry_list":cntry_list})
def add_country(request):
    return render(request,"add_country.html")
def edit_country(request,id):
    edit_cntry=Country.objects.get(id=id)
    edit_cntry.save()
    return render(request,"edit_country.html",{"edit_cntry":edit_cntry})
def update_country(request,id):
    updt_id=Country.objects.get(id=id)
    updt_id.name=request.POST.get("cname")
    updt_id.status=request.POST.get("status")
    updt_id.save()
    return redirect("/country/")
def delete_country(request,id):
    delt_id=Country.objects.get(id=id)
    delt_id.delete()
    return redirect("/country/")
def save_country(request):
    if(request.method)=="POST":
        obj_country=Country()
        obj_country.name=request.POST.get("cname")
        obj_country.status=request.POST.get("status") 
        obj_country.save()
        return redirect('/country/')
def brands(request):
    brnd_list=Brand.objects.all()
    return render(request,"brands.html",{"brnd_list":brnd_list})
def edit_brnd(request,id):
    edit_id=Brand.objects.get(id=id)
    return render(request,"edit_brnd.html",{"edit_id":edit_id})
def update_brnd(request,id):
    updt_brnd=Brand.objects.get(id=id)
    updt_brnd.name=request.POST.get("bname")
    updt_brnd.image=request.POST.get("image")
    updt_brnd.status=request.POST.get("status")
    updt_brnd.save()
    return redirect('/brands/')
def delete_brnd(request,id):
    delt_brnd=Brand.objects.get(id=id)
    delt_brnd.delete()
    return redirect('/country/')
def add_brand(request):
    return render(request,"add_brand.html")
def save_brands(request):
    obj_brand=Brand()
    if(request.method)=="POST":
        obj_brand.name=request.POST.get("bname")
        image=request.FILES["image"]
        fs=FileSystemStorage()
        file=fs.save(image.name,image)
        url=fs.url(file)
        obj_brand.image=url
        obj_brand.status=request.POST.get("status")
        obj_brand.save()
        return redirect('/brands/')
def category(request):
    cate_list=Category.objects.all()
    return render(request,"category.html",{"cate_list":cate_list})
def edit_ctgry(request,id):
    edit_ctgry=Category.objects.get(id=id)
    return render(request,"edit_ctgry.html",{"edit_ctgry":edit_ctgry})
def update_ctgry(request,id):
    updt_ctgry=Category.objects.get(id=id)
    updt_ctgry.name=request.POST.get("cname")
    updt_ctgry.image=request.POST.get("cimage")
    updt_ctgry.status=request.POST.get("status")
    return render(request,"category.html")
def delete_ctgry(request,id):
    delt_ctgry=Category.objects.get(id=id)
    delt_ctgry.delete()
    return redirect('/category/')
def add_category(request):
    return render(request,"add_category.html")
def save_category(request):
    if(request.method)=="POST":
        obj_category=Category()
        obj_category.name=request.POST.get("cname")
        image=request.FILES['cimage']
        fs=FileSystemStorage()
        file=fs.save(image.name,image)
        url=fs.url(file)
        obj_category.image=url
        obj_category.status=request.POST.get("status")
        obj_category.save()
        return redirect("/category/")
def add_product(request):
    category=Category.objects.all()
    brand=Brand.objects.all()
    country=Country.objects.all()
    return render(request,"add_product.html",{"category":category,"brand":brand,"country":country})
def products(request):
    prdct_list=Product.objects.all()
    return render(request,"products.html",{"prdct_list":prdct_list})
def save_product(request):
    if(request.method)=="POST":
        obj_product=Product()
        brand_id=request.POST.get("brand")
        if brand_id == "none":  # If the brand is selected
            obj_product.brand_id=None
        elif brand_id:
            try:
                obj_product.brand = Brand.objects.get(id=brand_id)  # Get the actual brand from DB
            except Brand.DoesNotExist:
                obj_product.brand = None  # Or you could assign a default brand if needed
        else:
            obj_product.brand = None  # Or you could assign a default brand if needed        
        category_id = request.POST.get("category")
        try:
            obj_product.category = Category.objects.get(id=category_id)  
        except Category.DoesNotExist:
            obj_product.category = None
        country_id=request.POST.get("sc")
        try:
            obj_product.country = Country.objects.get(id=country_id)  # Set country based on selected ID
        except Country.DoesNotExist:
            obj_product.country = None  # If no valid country is selected
        obj_product.code=request.POST.get("pcode")
        obj_product.name=request.POST.get("pname")
        obj_product.detail=request.POST.get("about")
        obj_product.originalprice=request.POST.get("originalp")
        obj_product.ourprice=request.POST.get("ourp")
        obj_product.taxrate=request.POST.get("rate")
        obj_product.taxamount=request.POST.get("ta")
        obj_product.grosstotal=request.POST.get("gt")
        obj_product.weight=request.POST.get("weight")
        obj_product.openingstock=request.POST.get("os")
        obj_product.currentstock=request.POST.get("cs")
        obj_product.status=request.POST.get("status")
        image=request.FILES['pimage']
        fs=FileSystemStorage()
        file=fs.save(image.name,image)
        url=fs.url(file)
        obj_product.image=url
        obj_product.save()
        return redirect("/products/")
def edit_prdct(request,id):
    edit_prdct=Product.objects.get(id=id)
    return render(request,"edit_prdct.html",{"edit_prdct":edit_prdct})
def update_prdct(request,id):
    update_prdct=Product.objects.get(id=id)
    update_prdct.name=request.POST.get("pname")
    update_prdct.code=request.POST.get("pcode")
    update_prdct.detail=request.POST.get("about")
    update_prdct.originalprice=request.POST.get("originalp")
    update_prdct.ourprice=request.POST.get("ourp")
    update_prdct.taxrate=request.POST.get("rate")
    update_prdct.taxamount=request.POST.get("ta")
    update_prdct.grosstotal=request.POST.get("gt")
    update_prdct.weight=request.POST.get("weight")
    update_prdct.openingstock=request.POST.get("os")
    update_prdct.currentstock=request.POST.get("cs")
    update_prdct.status=request.POST.get("status")
    return render(request,"products.html")
def dlt_prdct(request,id):
    dlt_prdct=Product.objects.get(id=id)
    dlt_prdct.delete()
    return redirect("/products/")
def product_list(request):
    products=Product.objects.all().order_by('name')
    category_display=Category.objects.all()
    brand_display=Brand.objects.all()
    paginator=Paginator(products,3)
    page_number=request.GET.get('page')
    page_obj=paginator.get_page(page_number)
    return render(request,"product_list.html",{
        'page_obj':page_obj,
        'products':page_obj,
        'category_display':category_display,
        'brand_display':brand_display
        })
def category_detail(request,id):
    categories=Category.objects.all()
    category=get_object_or_404(Category,id=id)
    products=Product.objects.filter(category=category)
    brand_display=Brand.objects.all()
    paginator=Paginator(products,3)
    page_number=request.GET.get('page')
    page_obj=paginator.get_page(page_number)
    return render(request,'category_detail.html',{
        'category':category,
        'products':products,
        'categories':categories,
        'brand_display':brand_display,
        'page_obj':page_obj,
        'products':page_obj
        })
def brand_filter(request, brand_id):
    brand = get_object_or_404(Brand, id=brand_id)
    products = Product.objects.filter(brand=brand)
    brand_display=Brand.objects.all()
    paginator = Paginator(products, 3)  # Adjust per page limit
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'category_detail.html',{
        'products': page_obj,
        'page_obj': page_obj,
        'brand_name': brand.name,
        'total_count': products.count(),
        'brand':brand,
        'brand_display':brand_display,
        'products':products})
def all_products_sort(request):
    sort_by = request.GET.get('sort', '')  # Get the sort option from query parameter

    if sort_by == 'price_asc':
        products = Product.objects.all().order_by('ourprice')
    elif sort_by == 'price_desc':
        products = Product.objects.all().order_by('-ourprice')
    else:
        products = Product.objects.all()  
    paginator=Paginator(products,10)
    page_number=request.GET.get('page')
    page_obj=paginator.get_page(page_number)
    return render(request,'products_list.html',{'sort_by':sort_by,'page_obj':page_obj})   
 
def add_to_cart(request, product_id):
    print(f"🔹 add_to_cart triggered for product_id: {product_id}")

    product = get_object_or_404(Product, id=product_id)  # Get the product

    if request.user.is_authenticated:
        # Fetch all cart items for this user and product
        cart_items = CartItem.objects.filter(user=request.user, product=product)
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key

        # Fetch all cart items for this session and product
        cart_items = CartItem.objects.filter(session_id=session_key, product=product)

    # Merge duplicate cart items (if any)
    if cart_items.exists():
        total_quantity = cart_items.aggregate(Sum('quantity'))['quantity__sum']
        first_item = cart_items.first()  # Keep the first item
        first_item.quantity = total_quantity + 1  # Add 1 more quantity
        first_item.save()

        # Delete all other duplicate items
        cart_items.exclude(id=first_item.id).delete()
        print(f"🔼 Merged duplicate cart items. New quantity: {first_item.quantity}")

    else:
        # No existing cart item, so create a new one
        if request.user.is_authenticated:
            CartItem.objects.create(user=request.user, product=product, quantity=1)
        else:
            CartItem.objects.create(session_id=session_key, product=product, quantity=1)
        print("🆕 New CartItem created.")

    return redirect('cart_detail')
def remove_from_cart(request, cart_item_id):
    if request.user.is_authenticated:
        # Remove item for authenticated user
        cart_item = get_object_or_404(CartItem, id=cart_item_id, user=request.user)
    else:
        # Ensure session exists
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        
        # Remove item for guest user
        cart_item = get_object_or_404(CartItem, id=cart_item_id, session_id=session_key)
    
    cart_item.delete()  # Remove item from cart
    return redirect('cart_detail')  # Redirect back to cart page
def move_to_cart(request, product_id):
    print(f"🔹 move_to_cart triggered for product_id: {product_id}")

    product = get_object_or_404(Product, id=product_id)  # Get the product

    # Determine if user is authenticated or using session
    if request.user.is_authenticated:
        wishlist_item = Wishlist.objects.filter(user=request.user, product=product).first()

        # Fetch existing cart item (if exists) or create new one
        cart_item = CartItem.objects.filter(user=request.user, product=product).first()

        if cart_item:
            cart_item.quantity += 1  # Increase quantity
            cart_item.save()
            print(f"🔼 Quantity updated: {cart_item.quantity}")
        else:
            cart_item = CartItem.objects.create(user=request.user, product=product, quantity=1)
            print("🆕 New CartItem created.")

    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key

        wishlist_item = Wishlist.objects.filter(session_id=session_key, product=product).first()

        cart_item = CartItem.objects.filter(session_id=session_key, product=product).first()

        if cart_item:
            cart_item.quantity += 1  # Increase quantity
            cart_item.save()
            print(f"🔼 Quantity updated: {cart_item.quantity}")
        else:
            cart_item = CartItem.objects.create(session_id=session_key, product=product, quantity=1)
            print("🆕 New CartItem created.")

    # Remove from wishlist
    if wishlist_item:
        wishlist_item.delete()
        print("🗑️ Wishlist item deleted.")

    return redirect('cart_detail')  # Redirect to cart page

def remove_from_wishlist(request,product_id):
    Wishlist.objects.filter(user=request.user,product_id=product_id).delete()
    return redirect('wishlist')

def update_cart(request, cart_item_id, action):
    print(f"Received cart_item_id: {cart_item_id}, action: {action}")  # Debugging
    cart_item = get_object_or_404(CartItem, id=cart_item_id)  # This line is causing 404
    
    print(f"CartItem found: {cart_item}")  # Debugging
    
    if action == "increase":
        cart_item.quantity += 1
        cart_item.save()
    elif action == "decrease" and cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()
    
    return redirect('cart_detail')

def cart_detail(request):
    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(user=request.user)  # Get the user's cart
    else:
        session_id=request.session.session_key
        if not session_id:
            request.session.create()
            session_id=request.session.session_key
        cart_items = CartItem.objects.filter(session_id=session_id)
    total_price = sum(item.subtotal() for item in cart_items)  # Calculate grand total
    return render(request, "cart_detail.html", {"cart_items": cart_items, "total_price": total_price})

def wishlist(request):
    if request.user.is_authenticated:
        wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')
    else:
        session_key = request.session.session_key
        if not session_key: 
            request.session.create()
            session_key = request.session.session_key
            
        wishlist_items = Wishlist.objects.filter(session_key=session_key).select_related('product')

    return render(request, 'wishlist.html', {'wishlist_items': wishlist_items})
def add_to_wishlist(request,product_id):
    product=get_object_or_404(Product,id=product_id)
    if request.user.is_authenticated:
        wishlist_items,created=Wishlist.objects.get_or_create(user=request.user,product=product)
    else:
        session_key=request.session.session_key
        if not session_key:
            request.session.create()
            session_key=request.session.session_key
        wishlist_item, created = Wishlist.objects.get_or_create(
            session_key=session_key, product=product  # ✅ Fixed for guest users
        )
    if created:
        print("Product added to wishlist successfully!")
    else:
        print("Product was already in wishlist")
    return redirect('wishlist')
def remove_from_wishlist(request,product_id):
    product=get_object_or_404(Product,id=product_id)
    if request.user.is_authenticated:
       Wishlist.objects.filter(user=request.user,product=product).delete()  
    else:
        session_key=request.session.session_key
        if session_key:
             Wishlist.objects.filter(session_key=session_key,product=product).delete()
    return redirect('wishlist')
def update_cart_quantity(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            item_id = data.get("item_id")

            if not item_id:
                return JsonResponse({"success": False, "error": "Invalid item_id"})

            cart_item = get_object_or_404(CartItem, id=int(item_id))

            new_quantity = int(data.get("quantity"))
            if new_quantity > 0:
                cart_item.quantity = new_quantity
                cart_item.save()

            # Recalculate total price
            cart = cart_item.cart
            total = cart.total_price()

            return JsonResponse({"success": True, "total": total})
        
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request"})
def checkout(request):
    user=request.user if request.user.is_authenticated else None
    session_id=request.session.session_key
    cart_items = CartItem.objects.filter(user=user) if user else CartItem.objects.filter(session_id=session_id)
    subtotal = sum(item.subtotal() for item in cart_items)
    shipping = 50
    total = subtotal + shipping
    return render(request, 'checkout.html', {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping': shipping,
        'total': total,
        'razorpay_merchant_key': settings.RAZORPAY_KEY_ID,
        'razorpay_amount': int(total * 100),
    })

def process_checkout(request):
    if request.method == "POST":
        user = request.user if request.user.is_authenticated else None
        session_id = request.session.session_key

        cart_items = CartItem.objects.filter(user=user) if user else CartItem.objects.filter(session_id=session_id)
        if not cart_items:
            return redirect('cart_detail')

        subtotal = sum(item.product.ourprice * item.quantity for item in cart_items)
        shipping_cost = 50  # Fixed shipping cost
        total_price = subtotal + shipping_cost

        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        address = request.POST.get("address")
        mobile = request.POST.get("mobile")
        email = request.POST.get("email")
        state = request.POST.get("state")
        pincode = request.POST.get("pincode")
        payment_method = request.POST.get("payment_method") 

        # ✅ Save shipping address
        shipping_address, created = ShippingAddress.objects.get_or_create(
            user=user,
            defaults=
            {
                "first_name":first_name,
                "last_name":last_name,
                "address":address,
                "mobile":mobile,
                "email":email,
                "state":state,
                "pincode":pincode
            })
        if not created:
            shipping_address.first_name=first_name
            shipping_address.last_name=last_name
            shipping_address.address=address
            shipping_address.mobile=mobile
            shipping_address.email=email
            shipping_address.state=state
            shipping_address.pincode=pincode
            shipping_address.save()

        # ✅ Create the order
        order = Order.objects.create(
            user=user,
            shipping_address=shipping_address,
            total_price=total_price,
            payment_status="Pending",
            payment_method=payment_method
        )

        # ✅ Add items to order
        for item in cart_items:
            OrderItem.objects.create(order=order, product=item.product, quantity=item.quantity, price=item.product.ourprice)

        # ✅ Create Razorpay Order
        if payment_method=="online":
            razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            payment_data = {
                "amount": int(total_price * 100),  # Convert to paisa
                "currency": "INR",
                "payment_capture": "1"
            }
            razorpay_order = razorpay_client.order.create(data=payment_data)

            order.razorpay_order_id = razorpay_order["id"]
            order.save()

            cart_items.delete()  # Clear cart after order placement

            return render(request, "payment.html", {
                "order": order,
                "razorpay_key": settings.RAZORPAY_KEY_ID,
                "razorpay_order_id": razorpay_order["id"],
                "razorpay_amount": int(total_price * 100),  
            })
        else:
            order.payment_status="Pending"
            order.save()
            cart_items.delete()
            return redirect("cod_invoice_view",order_id=order.id)
    return redirect("checkout")

def cod_invoice_view(request,order_id):
    order=get_object_or_404(Order,id=order_id)
    cart_items = OrderItem.objects.filter(order=order)
    shipping_cost=Decimal("50")
    subtotal=sum(item.product.ourprice * item.quantity for item in cart_items)
    print(subtotal)
    return render(request, 'invoice.html', {
        "order": order,
        "cart_items": cart_items,
        "subtotal": subtotal,
        "shipping": shipping_cost,
        "total": order.total_price,
    })
@login_required
@transaction.atomic
def cod_checkout(request):
    if request.method == 'POST':

        try:
            # Get saved address ID from session
            address_id = request.session.get('shipping_address_id')
            print("Address ID from session:", address_id)
            if not address_id:
                print("❗ Address ID not found in session")
                messages.error(request, "Shipping address not found.")
                return redirect('checkout')

            shipping_address = get_object_or_404(ShippingAddress, id=address_id)
            
            # Get cart items
            cart_items = CartItem.objects.filter(user=request.user)
            print("🛒 Cart items found:", cart_items)
            print("Count:",cart_items.count())
            for item in cart_items:
                print(f"➡️ {item.product} x {item.quantity}")
            
            if not cart_items.exists():
                messages.warning(request, "Your cart is empty.")
                return redirect('checkout')

            # Calculate total
            subtotal = sum(item.product.ourprice * item.quantity for item in cart_items)
            shipping = 50  # Fixed shipping fee or calculate dynamically
            total = subtotal + shipping

            # Create order
            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                shipping_address=shipping_address,
                total_price=total,
                payment_method='COD',
                payment_status='Pending',
                order_status='Pending',
                created_at=timezone.now()
            )
            # Create order items
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.ourprice
                )
                print("✅ Order items saved.", OrderItem.objects.filter(order=order))

            # Clear cart
            cart_items.delete()
            # Redirect to invoice page
            return redirect('cod_invoice_view', order_id=order.id)

        except Exception as e:
            messages.error(request, "Something went wrong while placing your order.")
            return redirect('checkout')

    else:
        return HttpResponse("Invalid request method", status=405)
        
def online_checkout(request):
    if request.method == "POST":
        user = request.user if request.user.is_authenticated else None
        session_id = request.session.session_key
        payment_id = request.POST.get('payment_id')
        shipping_id = request.session.get('shipping_id')

        cart_items = CartItem.objects.filter(user=user) if user else CartItem.objects.filter(session_id=session_id)
        shipping_address = ShippingAddress.objects.get(id=shipping_id)

        subtotal = sum(item.subtotal() for item in cart_items)
        shipping = 50
        total = subtotal + shipping

        order = Order.objects.create(
            user=user,
            payment_method="Online Payment",
            payment_status="Paid",
            shipping_address=shipping_address,
            total_price=total,
            payment_id=payment_id
        )

        for item in cart_items:
            OrderItem.objects.create(order=order, product=item.product, quantity=item.quantity, price=item.product.ourprice)

        cart_items.delete()
        return JsonResponse({"status": "success"})

    return JsonResponse({"status": "failed"}, status=400)

def payment_success(request):
    payment_id=request.GET.get('payment_id')
    try:
        order=Order.objects.get(payment_id=payment_id)
        order.payment_status="Paid"
        order.save()
        return render(request,'payment_success.html',{"order":order})
    except Order.DoesNotExist:
        return redirect("checkout")
def order_history(request):
    order=Order.objects.filter(user=request.user).order_by("-created_at")
    return render(request,"order_history.html",{{"orders":order}})


def order_detail(request,order_id):
    order=Order.objects.get(id=order_id,user=request.user)
    return render(request,"order_detail.html",{"order":order})


@login_required
def save_address(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        address = request.POST.get('address')
        mobile = request.POST.get('mobile')
        email = request.POST.get('email')
        state = request.POST.get('state')
        pincode = request.POST.get('pincode')

        # Save address
        shipping_address = ShippingAddress.objects.create(
            user=request.user,
            first_name=first_name,
            last_name=last_name,
            address=address,
            mobile=mobile,
            email=email,
            state=state,
            pincode=pincode
        )

        # ✅ SAVE ADDRESS ID TO SESSION
        request.session['shipping_address_id'] = shipping_address.id
        print("✅ Address ID saved to session:", shipping_address.id)
        user=request.user if request.user.is_authenticated else None
        session_id=request.session.session_key
        cart_items=CartItem.objects.filter(user=user) if user else CartItem.objects.filter(session_id=session_id)
        subtotal=sum(item.subtotal() for item in cart_items)
        shipping_fee=50
        total_amount=subtotal+shipping_fee
        total_paise=int(total_amount*100)
        #Razorpay order creation
        razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        razorpay_order = razorpay_client.order.create(dict(
            amount=total_paise,
            currency='INR',
            payment_capture='1',
        ))
        return JsonResponse({
             "razorpay_order_id": razorpay_order['id']
        })
@staff_member_required
def pending_orders(request):
    orders=Order.objects.filter(order_status='Pending')
    delivery_staffs=DeliveryStaff.objects.all()
    order_items = OrderItem.objects.select_related('product', 'order')
    return render(request,'pending.html',{'orders':orders,'delivery_staffs':delivery_staffs,'order_items':order_items})
@staff_member_required
def mark_as_out_for_delivery(request,order_id):
    order=get_object_or_404(Order,id=order_id)
    order.order_status='Out For Delivery'
    order.save()
    return redirect("pending")
@staff_member_required
def cancel_order(request,order_id):
    order=get_object_or_404(Order,id=order_id)
    order.order_status='Cancelled'
    order.save()
    return redirect('pending')
@require_POST
def assign_delivery_staff(request):
    item_id = request.POST.get('order_item_id')
    staff_id = request.POST.get('staff_id')
    print(item_id,staff_id)

    try:
        item = Order.objects.get(id=item_id)
        staff = DeliveryStaff.objects.get(id=staff_id)
        assign=Assigned_Order()
        assign.delivery_staff=staff
        assign.order=item
        assign.save()
        item.order_status="Out for Delivery"
        item.save()
        return JsonResponse({'status': 'success'})
    except (Order.DoesNotExist, DeliveryStaff.DoesNotExist):
        return JsonResponse({'status': 'error'}, status=400)
def delivery_staff_list(request):
    staffs=DeliveryStaff.objects.all()
    return render(request,'delivery_staff_list.html',{'staffs':staffs})

def add_delivery_staff(request):
    if request.method=="POST":
        name=request.POST.get("name")
        number=request.POST.get("number")
        is_active=request.POST.get("is_active")=="on"
        DeliveryStaff.objects.create(name=name,number=number,is_active=is_active)
        return redirect("delivery_staff_list")
    return render(request,'add_delivery_staff.html',{'action':'Add'})
def delivery_staff_edit(request,staff_id):
    staff=get_object_or_404(DeliveryStaff,id=staff_id)
    if request.method=='POST':
        staff.name=request.POST.get('name')
        staff.number=request.POST.get('number')
        staff.is_active=request.POST.get('is_active')=='on'
        staff.save()
        return redirect('delivery_staff_list')
    return render(request,'add_delivery_staff.html',{'action':'Edit','staff':staff})
@login_required
def delivery_dashboard(request):
    try:
        staff=DeliveryStaff.objects.get(user=request.user)
        assigned_deliveries=OrderItem.objects.filter(delivery_staff=staff)
    except DeliveryStaff.DoesNotExist:
        assigned_deliveries=[]
    return render(request, 'delivery_dashboard.html', {'deliveries': assigned_deliveries})


