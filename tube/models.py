from django.db import models
from django.utils import timezone
from django.conf import settings
from django.core.validators import MinValueValidator
from django.core.mail import send_mail
from django.contrib.sites.models import Site
import uuid, datetime


class VideoCategory(models.Model):

    class Meta:
        db_table = "category"

    # TIPS:数値型の主キーではPostgreSQLなど一部のDBでエラーを起こす。それだけでなく予測がされやすく衝突しやすいので、UUID型の主キーに仕立てる。
    id     = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False )
    name   = models.CharField(verbose_name="カテゴリー名", max_length=10)

    def __str__(self):
        return self.name


class Video(models.Model):

    class Meta:

        db_table = "video"

    id       = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False )
    category = models.ForeignKey(VideoCategory, verbose_name="カテゴリ", on_delete=models.PROTECT,related_name='video')
    dt       = models.DateTimeField(verbose_name="投稿日", default=timezone.now)

    title        = models.CharField(verbose_name="タイトル", max_length=50)
    description  = models.CharField(verbose_name="動画説明文", max_length=500)
    movie        = models.FileField(verbose_name="動画", upload_to="tube/movie", blank=True)
    thumbnail    = models.ImageField(verbose_name="サムネイル", upload_to="tube/thumbnail/", null=True)
    user         = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="投稿者", on_delete=models.CASCADE,related_name="posted_user")

    edited       = models.BooleanField(default=False)
    views        = models.IntegerField(verbose_name="再生回数", default=0, validators=[MinValueValidator(0)])
    view         = models.ManyToManyField(settings.AUTH_USER_MODEL,verbose_name="再生",through="VideoView",related_name="video_view")

    private      = models.BooleanField(verbose_name="限定公開", default=False)

    comment_refuse    = models.BooleanField(verbose_name="コメント拒否", default=False)
    comment_approval  = models.BooleanField(verbose_name="コメント承認制", default=False)

    comment     = models.ManyToManyField(settings.AUTH_USER_MODEL,verbose_name="コメント",through="VideoComment",related_name="video_comment")
    good        = models.ManyToManyField(settings.AUTH_USER_MODEL,verbose_name="良いね",through="GoodVideo",related_name="posted_good")
    video_mylist      = models.ManyToManyField(settings.AUTH_USER_MODEL,verbose_name="マイリスト",through="Mylist",related_name="video_mylist")
    video_history     = models.ManyToManyField(settings.AUTH_USER_MODEL,verbose_name="視聴履歴",through="History",related_name="video_history")


    def __str__(self):
        return self.title


class VideoView(models.Model):

    class Meta:
        db_table        = "video_view"
        unique_together = (("target","date","user"),("target","date","ip"))

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date        = models.DateField(verbose_name="再生日")
    target      = models.ForeignKey(Video,verbose_name="再生する動画",on_delete=models.CASCADE)
    user        = models.ForeignKey(settings.AUTH_USER_MODEL,verbose_name="再生した人",on_delete=models.CASCADE,null=True,blank=True)
    ip          = models.GenericIPAddressField(verbose_name="再生した人のIPアドレス")


class VideoComment(models.Model):

    class Meta:
        db_table = "video_comment"

    id      = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False )
    content = models.CharField(verbose_name="コメント文", max_length=500)
    target  = models.ForeignKey(Video, verbose_name="コメント先の動画", on_delete=models.CASCADE)
    dt      = models.DateTimeField(verbose_name="投稿日", default=timezone.now)
    user    = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="投稿者", on_delete=models.CASCADE)

    video_comment_approval  = models.BooleanField(verbose_name="動画コメント承認", default=False)
    read = models.BooleanField(verbose_name="既読", default=False)


    def __str__(self):
        return self.content

    def num_reply(self):
        return VideoCommentReply.objects.filter(target=self.id).count()

#コメントに対するリプライのモデル
class VideoCommentReply(models.Model):

    class Meta:
        db_table = "video_comment_reply"

    id      = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False )
    content = models.CharField(verbose_name="リプライ", max_length=500)
    target  = models.ForeignKey(VideoComment, verbose_name="リプライ対象のコメント", on_delete=models.CASCADE)
    dt      = models.DateTimeField(verbose_name="投稿日", default=timezone.now)
    user    = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="投稿者", on_delete=models.CASCADE)

    comment_reply_approval  = models.BooleanField(verbose_name="コメントリプライ承認", default=False)
    read = models.BooleanField(verbose_name="既読", default=False)

    def __str__(self):
        return self.content

    def num_reply(self):
        return VideoCommentReplyToReply.objects.filter(target=self.id).count()


#コメントに対するリプライのモデル
class VideoCommentReplyToReply(models.Model):

    class Meta:
        db_table = "video_comment_reply_to_reply"

    id      = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False )
    content = models.CharField(verbose_name="動画コメントのリプライに対するリプライ", max_length=500)
    target  = models.ForeignKey(VideoCommentReply, verbose_name="リプライ対象のコメント", on_delete=models.CASCADE)
    dt      = models.DateTimeField(verbose_name="投稿日", default=timezone.now)
    user    = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="投稿者", on_delete=models.CASCADE)

    reply_to_reply_approval = models.BooleanField(verbose_name="リプライのリプライ承認", default=False)
    read = models.BooleanField(verbose_name="既読", default=False)

    def __str__(self):
        return self.content


class History(models.Model):

    class Meta:
        db_table     = "history"

    id     = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    dt     = models.DateTimeField(verbose_name="視聴日時", default=timezone.now)
    target = models.ForeignKey(Video, verbose_name="視聴した動画", on_delete=models.CASCADE)
    user   = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="視聴したユーザー", on_delete=models.CASCADE)
    views  = models.IntegerField(verbose_name="視聴回数", default=1, validators=[MinValueValidator(1)])

    def __str__(self):
        return self.target.title


class MyList(models.Model):

    class Meta:
        db_table    = "mylist"

    id       = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    dt       = models.DateTimeField(verbose_name="登録日時", default=timezone.now)
    target   = models.ForeignKey(Video, verbose_name="マイリスト動画", on_delete=models.CASCADE)
    user     = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="登録したユーザー", on_delete=models.CASCADE)

    def __str__(self):
        return self.target.title


class NotifyCategory(models.Model):
    class Meta:
        db_table = "notify_category"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(verbose_name="通知カテゴリ名", max_length=10)

    def __str__(self):
        return self.name


class Notify(models.Model):
    class Meta:
        db_table = "notify"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(NotifyCategory, verbose_name="通知カテゴリ", on_delete=models.CASCADE, null=True)
    dt = models.DateTimeField(verbose_name="通知作成日時", default=timezone.now)
    title = models.CharField(verbose_name="通知タイトル", max_length=200,null=True)
    content = models.CharField(verbose_name="通知内容", max_length=2000)
    target = models.ManyToManyField(settings.AUTH_USER_MODEL, verbose_name="通知対象のユーザー", through="NotifyTarget",
                                    through_fields=("notify", "user"))

    def __str__(self):
        return self.title


class NotifyTarget(models.Model):

    class Meta:
        db_table = "notify_target"
        unique_together = ("user", "notify")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dt = models.DateTimeField(verbose_name="通知日時", default=timezone.now)
    notify = models.ForeignKey(Notify, verbose_name="通知", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="通知対象", on_delete=models.CASCADE)
    read = models.BooleanField(verbose_name="既読", default=False)

    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)

        target = NotifyTarget.objects.filter(user=self.user).first()

        site   = Site.objects.filter(id=settings.SITE_ID).first()
        print(site.domain,site.name)

        send_mail(
            'site.nameからお知らせ',
            'site.name よりお知らせがあります。通知欄をご確認ください。',
            'no-reply@site.domain',
            [target.user.email],
            fail_silently=False,
        )


class NewsCategory(models.Model):

    class Meta:
        db_table    = "news_category"

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name        = models.CharField(verbose_name="ニュースカテゴリ",max_length=20)

    def __str__(self):
        return self.name

#TODO:ニュースの原稿はいずれマークダウン記法ができるよう配慮する予定。画像の挿入も。
class News(models.Model):

    class Meta:
        db_table    = "news"

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dt          = models.DateTimeField(verbose_name="作成日時",default=timezone.now)
    start_date  = models.DateField(verbose_name="カルーセル掲示期間(開始日)")
    end_date    = models.DateField(verbose_name="カルーセル掲示期間(終了日)")
    category    = models.ForeignKey(NewsCategory, verbose_name="ニュースカテゴリ", on_delete=models.PROTECT)
    title       = models.CharField(verbose_name="ニュースタイトル",max_length=200)
    content     = models.CharField(verbose_name="ニュース内容",max_length=2000)

    def __str__(self):
        return self.title


class GoodVideo(models.Model):

    class Meta:
        db_table    = "good_video"

    dt      = models.DateTimeField(verbose_name="評価日時", default=timezone.now)
    target  = models.ForeignKey(Video, verbose_name="対象動画", on_delete=models.CASCADE)
    user    = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="高評価したユーザー", on_delete=models.CASCADE)

    def __str__(self):
        return self.target.title


class ReportCategory(models.Model):
    class Meta:
        db_table = "report_category"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(verbose_name="通報カテゴリ名", max_length=10)

    def __str__(self):
        return self.name


class Report(models.Model):

    class Meta:
        db_table    = "report"

    id             = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    dt             = models.DateTimeField(verbose_name="通報日時", default=timezone.now)
    report_user    = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="通報したユーザー", on_delete=models.CASCADE,related_name="report_user")
    reported_user  = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="通報されたユーザー", on_delete=models.CASCADE,related_name="reported_user")
    reason         = models.CharField(verbose_name="通報理由", max_length=200)
    category       = models.ForeignKey(ReportCategory, verbose_name="通報カテゴリ", on_delete=models.PROTECT, null=True)
    target         = models.CharField(verbose_name="通報対象", max_length=500)
    target_id      = models.CharField(verbose_name="通報対象id", max_length=100)


    def __str__(self):
        return self.reason

    #TODO:通報が保存される度、メール送信を行う。
    def save(self, *args, **kwargs):

        send_mail(
            'TubeIntegrity-Report',
            '通報がありました。管理画面から、通報内容を確認してください。',
            'no-reply@tubeintegrity.com',
            ['y_nara26@yahoo.co.jp'],
            fail_silently = False,
        )

        print("===================================")
        #これらを組み合わせる
        print("通報者",self.report_user)
        print(self.report_user.id)
        print("被通報者",self.reported_user)
        print(self.reported_user.id)
        print("通報理由",self.reason)

        # settingsからAPIキーを参照、sendgridのライブラリから本文と件名、メールアドレスを指定して送信する。
        # https://noauto-nolife.com/post/django-sendgrid/

        print("管理者へメール送信")
        print("===================================")

        super().save(*args, **kwargs)

class UserPolicy(models.Model):

    class Meta:
        db_table    = "userpolicy"

    id       = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    dt       = models.DateTimeField(verbose_name="利用規約同意日時", default=timezone.now)
    user     = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="ユーザー", on_delete=models.CASCADE)
    accept   = models.BooleanField(verbose_name="同意", default=False)


class Activity(models.Model):

    class Meta:
        db_table    = "activity"

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date        = models.DateField(verbose_name="実行日",default=datetime.date.today)
    user        = models.ForeignKey(settings.AUTH_USER_MODEL,verbose_name="実行したユーザー",on_delete=models.CASCADE,null=True,blank=True)
    target      = models.ForeignKey(Video,verbose_name="対象動画",on_delete=models.CASCADE)
    category    = models.ForeignKey(VideoCategory,verbose_name="実行時の動画カテゴリ",on_delete=models.PROTECT)

    play        = models.IntegerField(verbose_name="再生点")
    mylist      = models.IntegerField(verbose_name="マイリスト点")
    good        = models.IntegerField(verbose_name="良いね点")
    #bad         = models.IntegerField(verbose_name="悪いね点")
    comment     = models.IntegerField(verbose_name="コメント点")



class VideoCommentRefuse(models.Model):

    class Meta:
        db_table    = "config"

    id      = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user    = models.OneToOneField(settings.AUTH_USER_MODEL,verbose_name="動画投稿者",on_delete=models.CASCADE,null=True)
    video_comment_refuse   = models.BooleanField(verbose_name="動画コメント全拒否", default=False)

    def __str__(self):
        return self.video_comment_refuse


class VideoCommentApproval(models.Model):

    class Meta:
        db_table    = "config_approval"

    id      = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user    = models.OneToOneField(settings.AUTH_USER_MODEL,verbose_name="動画投稿者",on_delete=models.CASCADE,null=True)
    video_comment_approval   = models.BooleanField(verbose_name="全動画コメント承認制", default=False)

    def __str__(self):
        return self.video_comment_approval


#掲示板
class Topic(models.Model):

    class Meta:
        db_table  = "topic"

    id       = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False )
    dt       = models.DateTimeField(verbose_name="投稿日", default=timezone.now)
    content  = models.CharField(verbose_name="投稿内容", max_length=200)
    user     = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="トピック投稿者", on_delete=models.CASCADE,related_name="topic_user")
    good     = models.ManyToManyField(settings.AUTH_USER_MODEL,verbose_name="良いね",through="GoodTopic",related_name="good_topic")
    read     = models.IntegerField(verbose_name="閲覧数", default=0, validators=[MinValueValidator(0)])

    def __str__(self):
        return self.content


class GoodTopic(models.Model):

    class Meta:
        db_table    = "good_topic"

    dt      = models.DateTimeField(verbose_name="評価日時", default=timezone.now)
    target  = models.ForeignKey(Topic, verbose_name="対象掲示板", on_delete=models.CASCADE)
    user    = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="高評価したユーザー", on_delete=models.CASCADE)

    def __str__(self):
        return self.target.title



#広告動画


class AdvertisingCategory(models.Model):

    class Meta:
        db_table = "advertising_category"

    id     = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False )
    name   = models.CharField(verbose_name="広告カテゴリー名", max_length=10)

    def __str__(self):
        return self.name


class AdvertisingVideo(models.Model):

    class Meta:

        db_table = "advertising_video"

    id       = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False )
    category = models.ForeignKey(AdvertisingCategory, verbose_name="カテゴリ", on_delete=models.PROTECT,related_name='advertising_video')
    dt       = models.DateTimeField(verbose_name="投稿日", default=timezone.now)

    title        = models.CharField(verbose_name="タイトル", max_length=50)
    description  = models.CharField(verbose_name="動画説明文", max_length=500)
    movie        = models.FileField(verbose_name="動画", upload_to="tube/movie", blank=True)
    thumbnail    = models.ImageField(verbose_name="サムネイル", upload_to="tube/thumbnail/", null=True)
    user         = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="投稿者", on_delete=models.CASCADE,related_name="advertiser")

    views        = models.IntegerField(verbose_name="再生回数", default=0, validators=[MinValueValidator(0)])
    view         = models.ManyToManyField(settings.AUTH_USER_MODEL,verbose_name="再生",through="AdvertisingVideoView",related_name="advertising_video_view")

    good         = models.ManyToManyField(settings.AUTH_USER_MODEL,verbose_name="良いね",through="GoodAdvertisement",related_name="good_advertisement")
    bad          = models.ManyToManyField(settings.AUTH_USER_MODEL,verbose_name="悪いね",through="BadAdvertisement",related_name="bad_advertisement")


    def __str__(self):
        return self.title



class GoodAdvertisement(models.Model):

    class Meta:
        db_table    = "good_advertisement"

    dt      = models.DateTimeField(verbose_name="評価日時", default=timezone.now)
    target  = models.ForeignKey(AdvertisingVideo, verbose_name="対象広告動画", on_delete=models.CASCADE)
    user    = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="高評価したユーザー", on_delete=models.CASCADE)

    def __str__(self):
        return self.target.title


class BadAdvertisement(models.Model):

    class Meta:
        db_table    = "bad_advertisement"

    dt      = models.DateTimeField(verbose_name="評価日時", default=timezone.now)
    target  = models.ForeignKey(AdvertisingVideo, verbose_name="対象広告動画", on_delete=models.CASCADE)
    user    = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="Bad評価したユーザー", on_delete=models.CASCADE)

    def __str__(self):
        return self.target.title


class AdvertisingVideoView(models.Model):

    class Meta:
        db_table        = "advertising_video_view"
        unique_together = (("target","date","user"),("target","date","ip"))

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date        = models.DateField(verbose_name="再生日")
    target      = models.ForeignKey(AdvertisingVideo,verbose_name="再生する広告動画",on_delete=models.CASCADE)
    user        = models.ForeignKey(settings.AUTH_USER_MODEL,verbose_name="再生した人",on_delete=models.CASCADE,null=True,blank=True)
    ip          = models.GenericIPAddressField(verbose_name="再生した人のIPアドレス")
