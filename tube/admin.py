from django.contrib import admin
from django.utils.html import format_html

from .models import ( Video,VideoView,VideoComment,VideoCommentReply,VideoCommentReplyToReply,
                      VideoCategory,MyList,History,News,NewsCategory,Notify,NotifyTarget,NotifyCategory,
                      UserPolicy,Report,ReportCategory,VideoCommentRefuse,AdvertisingVideo,AdvertisingCategory,
                      Topic,Activity,AdvertisingVideoView )

from .forms import NotifyAdminForm,NotifyTargetAdminForm,NewsAdminForm

from users.models import CustomUser


class VideoAdmin(admin.ModelAdmin):

    # 指定したフィールドを表示、編集ができる
    list_display = [ "format_thumbnail","format_user","id","title","description","category","dt","comment_refuse","private","comment_approval" ,"views"]
    list_editable = [ "category","dt","title","description","comment_refuse","private","comment_approval" ]

    #指定したフィールドの検索と絞り込みができる
    #FIXME:外部キーに対して検索をする時は、外部キーのどのフィールドに対して検索を行うか、明示的に指定する必要がある。検索時にicontainsを使用しているため
    #参照: https://stackoverflow.com/questions/35012942/related-field-got-invalid-lookup-icontains

    search_fields       = [ "id","title","user__handle_name","user__id","description","dt","views" ]
    list_filter         = [ "title","user" ]

    #1ページ当たりに表示する件数、全件表示を許容する最大件数(ローカルでも5000件を超えた辺りから遅くなるので、10000~50000辺りが無難)
    list_per_page       = 10
    list_max_show_all   = 20000

    #日付ごとに絞り込む、ドリルナビゲーションの設置
    date_hierarchy      = "dt"

    #画像のフィールドはimgタグで画像そのものを表示させる
    def format_thumbnail(self,obj):
        if obj.thumbnail:
            return format_html('<img src="{}" alt="画像" style="width:15rem">', obj.thumbnail.url)

    #画像を表示するときのラベル(thumbnailのverbose_nameをそのまま参照している)
    format_thumbnail.short_description      = Video.thumbnail.field.verbose_name
    format_thumbnail.empty_value_display    = "画像なし"

    def format_user(self, obj):
        if obj.user.handle_name:
            return obj.user.handle_name

    format_user.short_description = Video.user.field.verbose_name
    format_user.empty_value_display = "名前がありません"


class VideoViewAdmin(admin.ModelAdmin):
    list_display    = [ "date","target","user","ip" ]


class VideoCommentAdmin(admin.ModelAdmin):

    list_display = [ "id","format_user","target","content","dt","video_comment_approval","read"]
    list_editable = [ "content","video_comment_approval","read" ]

    search_fields       = ["id", "content","dt","user__handle_name","user__id","target__title" ]
    list_filter         = [ "content","user" ]

    list_per_page       = 10
    list_max_show_all   = 20000

    date_hierarchy      = "dt"

    def format_user(self,obj):
        if obj.user.handle_name:
            return obj.user.handle_name

    format_user.short_description      = VideoComment.user.field.verbose_name
    format_user.empty_value_display    = "名前がありません"


class VideoCommentReplyAdmin(admin.ModelAdmin):

    list_display = [ "id","format_user","target","content","dt","comment_reply_approval","read"]
    list_editable = [ "content","comment_reply_approval","read" ]

    search_fields       = ["id", "content","dt","user__handle_name","user__id", ]
    list_filter         = [ "content","user" ]

    list_per_page       = 10
    list_max_show_all   = 20000

    date_hierarchy      = "dt"

    def format_user(self,obj):
        if obj.user.handle_name:
            return obj.user.handle_name

    format_user.short_description      = VideoCommentReply.user.field.verbose_name
    format_user.empty_value_display    = "名前がありません"


class VideoCommentReplyToReplyAdmin(admin.ModelAdmin):

    list_display = [ "id","format_user","target","content","dt","reply_to_reply_approval","read"]
    list_editable = [ "content","reply_to_reply_approval","read" ]

    search_fields       = ["id", "content","dt","user__handle_name","user__id", ]
    list_filter         = [ "content","user" ]

    list_per_page       = 10
    list_max_show_all   = 20000

    date_hierarchy      = "dt"

    def format_user(self,obj):
        if obj.user.handle_name:
            return obj.user.handle_name

    format_user.short_description      = VideoCommentReplyToReply.user.field.verbose_name
    format_user.empty_value_display    = "名前がありません"


class MyListAdmin(admin.ModelAdmin):
    list_display = ["id", "dt", "target", "format_user"]

    search_fields       = [ "id","target__title","user__handle_name","user__id","dt" ]
    list_filter         = [ "target","user" ]

    list_per_page       = 10
    list_max_show_all   = 20000

    def format_user(self, obj):
        if obj.user.handle_name:
            return obj.user.handle_name

    format_user.short_description = MyList.user.field.verbose_name
    format_user.empty_value_display = "名前がありません"

class HistoryAdmin(admin.ModelAdmin):
    list_display = ["id", "dt", "target", "format_user", "views"]

    search_fields       = [ "id","target__title","user__handle_name","user__id","dt" ]
    list_filter         = [ "target","user" ]

    list_per_page       = 10
    list_max_show_all   = 20000

    def format_user(self, obj):
        if obj.user.handle_name:
            return obj.user.handle_name

    format_user.short_description = History.user.field.verbose_name
    format_user.empty_value_display = "名前がありません"



class NewsAdmin(admin.ModelAdmin):
    list_display    = [ "dt","start_date","end_date","category","title","content" ]
    form            = NewsAdminForm

class NotifyAdmin(admin.ModelAdmin):
    list_display = ["category", "dt", "title", "content"]
    form = NotifyAdminForm

    actions = ["all_notify", "change_read", "change_not_read"]

    # 選択した通知を全員に通知するアクション。管理画面でチェックしたものがquerysetに入る。
    def all_notify(self, request, queryset):

        # 特定の条件に一致するユーザーに対して通知を送りたい場合は、下記をfilterに書き換え
        users = list(CustomUser.objects.all().values_list("id", flat=True))

        for q in queryset:
            for user in users:
                formset = NotifyTargetAdminForm({"notify": q.id, "user": user})

                if formset.is_valid():
                    formset.save()

    all_notify.short_description = "チェックした通知内容を全員に通知する"

    def change_read(self, request, queryset):
        id_list = list(queryset.values_list("id", flat=True))
        notifies = NotifyTarget.objects.filter(notify__in=id_list)

        for n in notifies:
            n.read = True
            n.save()

    change_read.short_description = "チェックした通知を全て既読化"

    def change_not_read(self, request, queryset):
        id_list = list(queryset.values_list("id", flat=True))
        notifies = NotifyTarget.objects.filter(notify__in=id_list)

        for n in notifies:
            n.read = False
            n.save()

    change_not_read.short_description = "チェックした通知を全て未読化"


class NotifyTargetAdmin(admin.ModelAdmin):
    list_display = ["notify", "user", "read"]
    actions = ["change_read", "change_not_read"]

    # チェックした通知とターゲットの組み合わせを未読化させる
    def change_not_read(self, request, queryset):
        id_list = list(queryset.values_list("id", flat=True))
        notifies = NotifyTarget.objects.filter(id__in=id_list)

        for n in notifies:
            n.read = False
            n.save()

    change_not_read.short_description = "チェックした通知ターゲットを未読化"

    def change_read(self, request, queryset):
        id_list = list(queryset.values_list("id", flat=True))
        notifies = NotifyTarget.objects.filter(id__in=id_list)

        for n in notifies:
            n.read = True
            n.save()

    change_read.short_description = "チェックした通知ターゲットを既読化"



class NotifyCategoryAdmin(admin.ModelAdmin):

    list_display    = [ "name" ]

class UserPolicyAdmin(admin.ModelAdmin):

    list_display    = [ "dt","user","accept" ]
    search_fields       = [ "user__handle_name","user__id", ]
    list_filter         = [ "user" ]

    list_per_page       = 20
    list_max_show_all   = 20000

class ReportCategoryAdmin(admin.ModelAdmin):

    list_display    = [ "name" ]

class ReportAdmin(admin.ModelAdmin):

    list_display = ["id","dt","format_report_user","format_reported_user","reason","category","target","target_id" ]
    search_fields       = [ "id", "report_user__handle_name","reported_user__handle_name","reason","category__name","dt","target" ]
    list_filter         = [ "report_user","reported_user","reason","category" ]

    list_per_page       = 10
    list_max_show_all   = 20000

    def format_report_user(self, obj):
        if obj.report_user.handle_name:
            return obj.report_user.handle_name

    format_report_user.short_description = Report.report_user.field.verbose_name
    format_report_user.empty_value_display = "名前がありません"

    def format_reported_user(self, obj):
        if obj.reported_user.handle_name:
            return obj.reported_user.handle_name

    format_reported_user.short_description = Report.reported_user.field.verbose_name
    format_reported_user.empty_value_display = "名前がありません"



class VideoCommentRefuseAdmin(admin.ModelAdmin):
    list_display = ["format_user","video_comment_refuse"]
    list_editable = ["video_comment_refuse"]

    search_fields       = [ "user__handle_name" ]
    list_filter         = [ "user" ]

    list_per_page       = 20
    list_max_show_all   = 20000


    def format_user(self, obj):
        if obj.user.handle_name:
            return obj.user.handle_name

    format_user.short_description = Video.user.field.verbose_name
    format_user.empty_value_display = "名前がありません"


class ActivityAdmin(admin.ModelAdmin):
    list_display    = [ "date","user","target","category","play","mylist","good","comment" ]



class AdvertisingVideoAdmin(admin.ModelAdmin):

    list_display = [ "format_thumbnail","format_user","id","title","description","category","dt"]
    list_editable = [ "category","dt","title","description"]

    search_fields       = [ "id","title","user__handle_name","user__id","description","dt" ]
    list_filter         = [ "title","user" ]

    list_per_page       = 10
    list_max_show_all   = 20000

    date_hierarchy      = "dt"

    def format_thumbnail(self,obj):
        if obj.thumbnail:
            return format_html('<img src="{}" alt="画像" style="width:15rem">', obj.thumbnail.url)

    format_thumbnail.short_description      = AdvertisingVideo.thumbnail.field.verbose_name
    format_thumbnail.empty_value_display    = "画像なし"

    def format_user(self, obj):
        if obj.user.handle_name:
            return obj.user.handle_name

    format_user.short_description = Video.user.field.verbose_name
    format_user.empty_value_display = "名前がありません"


class AdvertisingVideoViewAdmin(admin.ModelAdmin):
    list_display    = [ "date","target","user","ip" ]
    search_fields       = [ "date","target","user","ip" ]


class TopicAdmin(admin.ModelAdmin):

    list_display = [ "id","format_user","content","dt"]
    list_editable = [ "content"]

    search_fields       = ["id", "content","dt","user__handle_name","user__id" ]
    list_filter         = [ "content","user" ]

    list_per_page       = 10
    list_max_show_all   = 20000

    date_hierarchy      = "dt"

    def format_user(self,obj):
        if obj.user.handle_name:
            return obj.user.handle_name

    format_user.short_description      = VideoComment.user.field.verbose_name
    format_user.empty_value_display    = "名前がありません"




admin.site.register(Video,VideoAdmin)
admin.site.register(VideoView,VideoViewAdmin)
admin.site.register(VideoComment,VideoCommentAdmin)
admin.site.register(VideoCommentReply,VideoCommentReplyAdmin)
admin.site.register(VideoCommentReplyToReply,VideoCommentReplyToReplyAdmin)
admin.site.register(VideoCategory)
admin.site.register(MyList,MyListAdmin)
admin.site.register(History,HistoryAdmin)
admin.site.register(UserPolicy,UserPolicyAdmin)

admin.site.register(News,NewsAdmin)
admin.site.register(NewsCategory)

admin.site.register(Notify,NotifyAdmin)
admin.site.register(NotifyTarget,NotifyTargetAdmin)
admin.site.register(NotifyCategory,NotifyCategoryAdmin)

admin.site.register(ReportCategory)
admin.site.register(Report,ReportAdmin)
admin.site.register(VideoCommentRefuse,VideoCommentRefuseAdmin)
admin.site.register(Activity,ActivityAdmin)

admin.site.register(AdvertisingVideo,AdvertisingVideoAdmin)
admin.site.register(AdvertisingCategory)
admin.site.register(AdvertisingVideoView,AdvertisingVideoViewAdmin)

admin.site.register(Topic,TopicAdmin)

