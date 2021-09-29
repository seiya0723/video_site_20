from django import forms
from .models import Notify,NotifyTarget,News,UserPolicy,VideoCommentRefuse,VideoCommentApproval,Report,Topic,GoodAdvertisement,BadAdvertisement,AdvertisingVideo
from users.models import CustomUser



class NewsAdminForm(forms.ModelForm):

    class Meta:
        model   = News
        fields  = [ "dt","start_date","end_date","category","title","content" ]

    content     = forms.CharField(  widget  = forms.Textarea( attrs={ "maxlength":str(News.content.field.max_length), } ),
                                    label   = News.content.field.verbose_name
                                    )

class NotifyAdminForm(forms.ModelForm):

    class Meta:
        model   = Notify
        fields  = [ "category","dt","title","content", ]


    content     = forms.CharField(  widget  = forms.Textarea( attrs={ "maxlength":str(Notify.content.field.max_length), } ),
                                    label   = Notify.content.field.verbose_name
                                    )


class NotifyTargetAdminForm(forms.ModelForm):

    class Meta:
        model   = NotifyTarget
        fields  = [ "notify","user" ]

class UserPolicyForm(forms.ModelForm):

    class Meta:
        model   = UserPolicy
        fields  = [ "accept"]
        labels  = { "accept":"利用規約に同意する。"}

class CommentRefuseForm(forms.ModelForm):

    class Meta:
        model  = VideoCommentRefuse
        fields = ["video_comment_refuse"] #全ての動画に対するコメント拒否

class CommentApprovalForm(forms.ModelForm):

    class Meta:
        model  = VideoCommentApproval
        fields = ["video_comment_approval"] #全動画をコメント承認制に


class ReportForm(forms.ModelForm):

    class Meta:
        model  = Report
        fields = [ "report_user","reported_user","reason","category","target","target_id" ]


class UserInformationForm(forms.ModelForm):

    class Meta:
        model  = CustomUser
        fields =[ "handle_name","self_introduction"]


class TopicForm(forms.ModelForm):

    class Meta:
        model  = Topic
        fields = ["content"]



class GoodAdvertisementForm(forms.ModelForm):

    class Meta:
        model   = GoodAdvertisement
        fields  = [ "target","user",]


class BadAdvertisementForm(forms.ModelForm):

    class Meta:
        model   = BadAdvertisement
        fields  = [ "target","user",]


class AdvertisingVideoEditForm(forms.ModelForm):

    class Meta:
        model  = AdvertisingVideo
        fields =[ "title","description","category", ]