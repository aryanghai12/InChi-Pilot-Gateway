from django.contrib import admin
from apps.registry.models import Supplier, Product, EvidenceItem


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ["legal_name", "trade_name", "country_of_registration", "supplier_type", "record_status", "version", "created_at"]
    list_filter = ["record_status", "supplier_type", "country_of_registration"]
    search_fields = ["legal_name", "trade_name", "contact_name"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["product_name", "supplier", "product_category", "translation_status", "version", "created_at"]
    list_filter = ["product_category", "translation_status", "currency"]
    search_fields = ["product_name", "product_name_zh", "description"]


@admin.register(EvidenceItem)
class EvidenceItemAdmin(admin.ModelAdmin):
    list_display = ["document_type", "evidence_reference", "supplier", "product", "presence_status", "review_status"]
    list_filter = ["document_type", "presence_status", "review_status"]
