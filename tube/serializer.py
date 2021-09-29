from rest_framework import serializers

from .models import Video,VideoView,VideoComment,VideoCommentReply,VideoCommentReplyToReply,MyList,History,GoodVideo,Report,Activity,AdvertisingVideo,AdvertisingVideoView
from users.models import CustomUser,FollowUser,BlockUser,PrivateUser

import datetime



class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model   = Activity
        fields  = [ "date","user","target","category","play","mylist","good","comment" ]

def activity_calc(user,target,category,attr,add):

    date        = datetime.date.today()
    dic         = { "date":date, "user":user, "target":target, "category":category , "play":0, "mylist":0, "good":0, "comment":0 }
    instance    = Activity.objects.filter(user=user,target=target,category=category,date=date).first()

    if instance:

        print("追加加算処理")
        dic             = Activity.objects.filter(user=user,target=target,category=category,date=date).values().first()

        dic["user"]     = dic["user_id"]
        dic["target"]   = dic["target_id"]
        dic["category"] = dic["category_id"]
        dic[attr]       = dic[attr] + add

        serializer      = ActivitySerializer(instance,data=dic)

        if serializer.is_valid():
            print("OK")
            serializer.save()

    else:
        #無いのであれば必要なデータを加減算する処理
        print("新規作成後加算処理")

        dic[attr]   = dic[attr] + add
        serializer  = ActivitySerializer(data=dic)

        if serializer.is_valid():
            print("OK")
            data=serializer.validated_data
            if data["target"].private:
                print("限定動画：ランキング除外")
                pass
            else:
                print("一般動画")
                serializer.save()

    print("完了")

#広告動画
class AdvertisingVideoSerializer(serializers.ModelSerializer):

    class Meta:
        model  = AdvertisingVideo
        fields =["title","description","category","movie","thumbnail","user"]


class AdvertisingVideoViewSerializer(serializers.ModelSerializer):

    class Meta:
        model   = AdvertisingVideoView
        fields  = [ "date","target","user","ip"  ]

#個々の動画
class VideoSerializer(serializers.ModelSerializer):

    class Meta:
        model  = Video
        fields =["title","description","category","movie","thumbnail","user","comment_refuse","private","comment_approval"]

class ViewSerializer(serializers.ModelSerializer):

    class Meta:
        model   = VideoView
        fields  = [ "date","target","user","ip"  ]


    def save(self, *args, **kwargs):
        if not self.instance:
            #未ログインユーザーはIDがないためattribute Errorを引き起こす。その対策
            user_id     = None
            if self.validated_data["user"]:
                user_id = self.validated_data["user"].id

            activity_calc(user_id, self.validated_data["target"].id, self.validated_data["target"].category.id, "play",1)

        super().save(*args, **kwargs)


class VideoEditSerializer(serializers.ModelSerializer):

    class Meta:
        model  = Video
        fields =[ "title","description","category", ]


class VideoCommentSerializer(serializers.ModelSerializer):

    class Meta:
        model  = VideoComment
        fields = ["content","target","user",]


    def save(self, *args, **kwargs):
        if not self.instance:
            activity_calc(self.validated_data["user"].id, self.validated_data["target"].id, self.validated_data["target"].category.id, "comment",1)

        super().save(*args, **kwargs)



class VideoCommentEditSerializer(serializers.ModelSerializer):

    class Meta:
        model  = VideoComment
        fields = [ "content","target","user",]

class VideoCommentReplyEditSerializer(serializers.ModelSerializer):

    class Meta:
        model  = VideoCommentReply
        fields = [ "content","target","user",]

class VideoCommentReplyToReplyEditSerializer(serializers.ModelSerializer):

    class Meta:
        model  = VideoCommentReplyToReply
        fields = [ "content","target","user",]

#TIPS:フィールド名はVideoCommentSerializerと全く同じだが、外部キーで繋がっているものが全く違うので、リプライのバリデーションにVideoCommentSerializerを流用してはならない
class VideoCommentReplySerializer(serializers.ModelSerializer):

    class Meta:
        model  = VideoCommentReply
        fields = ["content","target","user",]

class VideoCommentReplyToReplySerializer(serializers.ModelSerializer):

    class Meta:
        model  = VideoCommentReplyToReply
        fields = ["content","target","user",]

#動画マイリスト
class MyListSerializer(serializers.ModelSerializer):

    class Meta:
        model   = MyList
        fields  = ["target","user",]


    def save(self, *args, **kwargs):
        if not self.instance:
            activity_calc(self.validated_data["user"].id, self.validated_data["target"].id, self.validated_data["target"].category.id, "mylist",1)

        super().save(*args, **kwargs)

#動画視聴履歴
class HistorySerializer(serializers.ModelSerializer):

    class Meta:
        model   = History
        fields  = ["target","user",]

#動画のいいね、マイリスト分岐、広告のいいね、悪いね分岐
class RateSerializer(serializers.Serializer):

    flag    = serializers.BooleanField()

#動画いいね
class GoodSerializer(serializers.ModelSerializer):

    class Meta:
        model   = GoodVideo
        fields  = [ "target","user",]

    def save(self, *args, **kwargs):
        if not self.instance:
            activity_calc(self.validated_data["user"].id, self.validated_data["target"].id, self.validated_data["target"].category.id, "good",1)

        super().save(*args, **kwargs)


#ユーザーアイコン
class IconSerializer(serializers.ModelSerializer):

    class Meta:
        model  = CustomUser
        fields = ["usericon",]

class FollowUserSerializer(serializers.ModelSerializer):

    class Meta:
        model  = FollowUser
        fields =[ "from_user","to_user" ]

class BlockUserSerializer(serializers.ModelSerializer):

    class Meta:
        model  = BlockUser
        fields =[ "from_user","to_user" ]

class PrivateUserSerializer(serializers.ModelSerializer):

    class Meta:
        model  = PrivateUser
        fields =[ "from_user","to_user" ]


#モデルとは紐付かないシリアライザを作る。
class NotifyTargetSerializer(serializers.Serializer):
    notify  = serializers.UUIDField()
    user    = serializers.UUIDField()


class YearMonthSerializer(serializers.Serializer):
    year    = serializers.IntegerField()
    month   = serializers.IntegerField()


class UUIDListSerializer(serializers.Serializer):

    id = serializers.ListField( child=serializers.UUIDField() )
