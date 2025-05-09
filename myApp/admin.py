from django.contrib import admin
from .models import Product, TeamMember, AboutPageStats, ContactMessage, Cart, CartItem, Wishlist, WishlistItem

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category', 'is_featured', 'is_new_arrival')
    list_filter = ('category', 'is_featured', 'is_new_arrival')
    search_fields = ('name', 'description')
    list_editable = ('is_featured', 'is_new_arrival')
    
    # Remove any custom methods that might cause issues

@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'position', 'order')
    list_editable = ('order',)
    search_fields = ('name', 'position')

@admin.register(AboutPageStats)
class AboutPageStatsAdmin(admin.ModelAdmin):
    list_display = ('customers', 'products', 'years', 'awards')

    def has_add_permission(self, request):
        # Check if any stats object already exists
        if AboutPageStats.objects.exists():
            return False
        return True

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    list_editable = ('status',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_cart_total', 'get_cart_items_count', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username',)

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('product', 'cart', 'quantity', 'get_total')
    list_filter = ('created_at',)
    search_fields = ('product__name', 'cart__user__username')

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_wishlist_count', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username',)

@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ('product', 'wishlist', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('product__name', 'wishlist__user__username')