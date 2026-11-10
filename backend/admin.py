from django.contrib import admin

# Register your models here.



from .models import Attraction

# admin 后台用的
admin.site.site_header = "澳門漫遊 · 内容管理"
admin.site.site_title = "澳門漫遊后台"
admin.site.index_title = "景点管理"


@admin.register(Attraction)
class AttractionAdmin(admin.ModelAdmin):

    # 列表显示
    list_display = ("name", "region", "sight_type", "world_heritage", "enabled")

    # 筛选
    list_filter = ("region", "sight_type", "world_heritage", "category", "less_known", "enabled")

    # 搜索
    search_fields = ("name", "name_en", "address")

    # 允许直接修改
    list_editable = ("enabled",)

    # 根据英文名称自动填写 slug
    prepopulated_fields = {"slug": ("name_en",)}
