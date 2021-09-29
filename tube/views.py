from rest_framework import status,views,response

from django.shortcuts import render, redirect, HttpResponse

from django.http import HttpResponseForbidden #追加

from django.db.models.functions import TruncMonth
from django.db.models import Q,Count,Sum
from django.http.response import JsonResponse
from django.template.loader import render_to_string

from django.core.paginator import Paginator

from django.core.mail import send_mail

from django.conf import settings

from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone

from .models import (  Video,VideoCategory,VideoComment,VideoCommentReply,VideoCommentReplyToReply,
                    MyList,History,GoodVideo,NotifyTarget,Notify,News,NewsCategory,UserPolicy,Activity,
                    ReportCategory,VideoCommentRefuse,VideoCommentApproval,Topic,GoodTopic,AdvertisingVideo,
                    AdvertisingCategory,GoodAdvertisement,BadAdvertisement )

from users.models import CustomUser,FollowUser,BlockUser,PrivateUser

from .serializer import ( VideoSerializer,ViewSerializer,VideoEditSerializer,VideoCommentSerializer,
                          VideoCommentEditSerializer,VideoCommentReplyEditSerializer,
                          VideoCommentReplyToReplyEditSerializer,VideoCommentReplySerializer,
                          VideoCommentReplyToReplySerializer,MyListSerializer,HistorySerializer,RateSerializer,
                          GoodSerializer,IconSerializer,FollowUserSerializer,BlockUserSerializer,NotifyTargetSerializer,
                          PrivateUserSerializer,AdvertisingVideoSerializer,AdvertisingVideoViewSerializer,
                          YearMonthSerializer,UUIDListSerializer )

from .forms import ( UserPolicyForm,CommentRefuseForm,CommentApprovalForm,ReportForm,UserInformationForm,
                     TopicForm,GoodAdvertisementForm,BadAdvertisementForm,AdvertisingVideoEditForm)


#python-magicで受け取ったファイルのMIMEをチェックする。
#MIMEについては https://developer.mozilla.org/ja/docs/Web/HTTP/Basics_of_HTTP/MIME_types/Common_types を参照。

from PIL import Image
import qrcode, datetime,base64,magic
from io import BytesIO

ALLOWED_MIME   = ["video/mp4"]

# アップロードの上限
LIMIT_SIZE     = 8000 * 1000 * 1000
AD_LIMIT_SIZE     = 200 * 1000 * 1000

DEFAULT_VIDEO_AMOUNT = 100
DEFAULT_TOPIC_AMOUNT = 10000
DEFAULT_HISTORY_AMOUNT = 10
COMMENTS_AMOUNT_PAGE = 10
SEARCH_AMOUNT_PAGE  = 10



#トップページ
class IndexView(views.APIView):

    def get(self, request,*args, **kwargs):

        topics = Topic.objects.all().order_by("-dt")[:DEFAULT_TOPIC_AMOUNT]
        t_amount = topics.count()
        paginator = Paginator(topics, 10)

        if "page" in request.GET:
            topics = paginator.get_page(request.GET["page"])
        else:
            topics = paginator.get_page(1)

        advertisements = AdvertisingVideo.objects.all()
        categories = VideoCategory.objects.all()

        if request.user.is_authenticated:

            # フォローユーザーの動画
            follows = Video.objects.filter(user__followed=request.user.id).exclude(private=True).order_by("-dt")[:DEFAULT_VIDEO_AMOUNT]

            f_amount = follows.count()
            paginator = Paginator(follows, 10)

            if "page" in request.GET:
                follows = paginator.get_page(request.GET["page"])
            else:
                follows = paginator.get_page(1)

            # 新着順(ブロックしたユーザーは除外)
            latests = Video.objects.exclude(user__blocked=request.user.id).exclude(private=True).order_by("-dt")[:DEFAULT_VIDEO_AMOUNT]

            if "category" in request.GET:
                category = request.GET["category"]
                latests = Video.objects.filter(category__name=category).exclude(user__blocked=request.user.id).exclude(private=True).order_by("-dt")[:DEFAULT_VIDEO_AMOUNT]

            amount    = latests.count()
            paginator = Paginator(latests, 10)

            if "page" in request.GET:
                latests = paginator.get_page(request.GET["page"])
            else:
                latests = paginator.get_page(1)


            context = {"latests": latests,
                       "follows": follows,
                       "amount":amount,
                       "f_amount":f_amount,
                       "topics":topics,
                       "t_amount":t_amount,
                       "advertisements":advertisements,
                       "categories":categories,
                       }
            return render(request, "tube/index.html", context)

        else:
            follows = False

            # 新着順
            latests = Video.objects.exclude(private=True).order_by("-dt")[:DEFAULT_VIDEO_AMOUNT]

            if "category" in request.GET:
                category = request.GET["category"]
                latests = Video.objects.filter(category__name=category).exclude(private=True).order_by("-dt")[:DEFAULT_VIDEO_AMOUNT]

            amount    = latests.count()
            paginator = Paginator(latests, 10)

            if "page" in request.GET:
                latests = paginator.get_page(request.GET["page"])
            else:
                latests = paginator.get_page(1)


            context = {"latests": latests,
                       "follows": follows,
                       "amount": amount,
                       "topics":topics,
                       "t_amount":t_amount,
                       "advertisements":advertisements,
                       "categories": categories,
                       }

        return render(request, "tube/index.html", context)

index = IndexView.as_view()

#アップロードページ
class UploadView(LoginRequiredMixin,views.APIView):

    def get(self,request, *args, **kwargs):

        userpolicy = UserPolicy.objects.filter(user=request.user.id).first()

        categories = VideoCategory.objects.all()

        context = {"categories": categories,
                   "userpolicy":userpolicy,
                   }

        return render(request, "tube/upload.html", context)


    def post(self, request, *args, **kwargs):

        request.data["user"]    = request.user.id
        serializer              = VideoSerializer(data=request.data)
        #mime_type               = magic.from_buffer(request.FILES["movie"].read(1024), mime=True)

        #XXX:Cloudinaryでファイルをアップロードする時、このファイル参照が原因で動画ファイルのアップロードに失敗してしまう。
        #この問題は後日対策をブログにて。これではMIMEの参照、ファイルサイズの制限も実現できない。
        """
        if request.FILES["movie"].size >= LIMIT_SIZE:
            mb = str(LIMIT_SIZE / 1000000)

            json = {"error": True,
                    "message": "The maximum file size is " + mb + "MB"}

            return JsonResponse(json)

        if mime_type not in ALLOWED_MIME:
            mime = str(ALLOWED_MIME)
            json = {"error": True,
                    "message": "The file you can post is " + mime + "."}

            return JsonResponse(json)
        """

        if serializer.is_valid():
            serializer.save()
        else:
            json    = { "error":True,
                        "message":"入力内容に誤りがあります。" }
            return JsonResponse(json)

        json    = { "error":False,
                    "message":"アップロード完了しました。" }

        return JsonResponse(json)


upload = UploadView.as_view()


#広告動画アップロードページ
class AdvertisingVideoUploadView(LoginRequiredMixin,views.APIView):

    def get(self,request, *args, **kwargs):

        userpolicy = UserPolicy.objects.filter(user=request.user.id).first()

        categories = AdvertisingCategory.objects.all()

        context = {"categories": categories,
                   "userpolicy":userpolicy,
                   }

        return render(request, "tube/advertising_video_upload.html", context)


    def post(self, request, *args, **kwargs):

        request.data["user"]    = request.user.id
        serializer              = AdvertisingVideoSerializer(data=request.data)
        mime_type               = magic.from_buffer(request.FILES["movie"].read(1024), mime=True)

        if request.FILES["movie"].size >= AD_LIMIT_SIZE:
            mb = str(AD_LIMIT_SIZE / 1000000)

            json = {"error": True,
                    "message": "The maximum file size is " + mb + "MB"}

            return JsonResponse(json)

        if mime_type not in ALLOWED_MIME:
            mime = str(ALLOWED_MIME)
            json = {"error": True,
                    "message": "The file you can post is " + mime + "."}

            return JsonResponse(json)

        if serializer.is_valid():
            serializer.save()
        else:
            json    = { "error":True,
                        "message":"入力内容に誤りがあります。" }
            return JsonResponse(json)

        json    = { "error":False,
                    "message":"アップロード完了しました。" }

        return JsonResponse(json)


advertising_video = AdvertisingVideoUploadView.as_view()


#検索結果表示ページ
class SearchView(views.APIView):

    def get(self, request, *args, **kwargs):
        print(request.GET)
        query = Q()
        page = 1

        if "word" in request.GET:
            word = request.GET["word"]

            if word == "" or word.isspace():
                return redirect("tube:index")

            word_list  = word.replace("　", " ").split(" ")
            word_lists = [ w for w in word_list if w != "" ]

            for w in word_lists:
                query &= Q( Q(title__icontains=w) | Q(description__icontains=w) | Q(user__handle_name__icontains=w) )

        if "page" in request.GET:
            page = request.GET["page"]

        # TODO:ここでログインしていれば、ブロックユーザーを除外した検索をする。
        if request.user.is_authenticated:

            videos = Video.objects.filter(query).exclude(user__blocked=request.user.id).exclude(private=True).order_by("-dt")

        else:
            videos = Video.objects.filter(query).exclude(private=True).order_by("-dt")

        amount = len(videos)

        videos_paginator = Paginator(videos, SEARCH_AMOUNT_PAGE)
        videos           = videos_paginator.get_page(page)

        context = {"videos": videos,
                   "amount": amount}

        return render(request, "tube/search.html", context)

search = SearchView.as_view()


#動画個別ページ
class SingleView(views.APIView):

    def get(self,request, video_pk,*args, **kwargs):

        video = Video.objects.filter(id=video_pk).first()
        if not video:
            return redirect("tube:index")

        #動画視聴回数の処理
        self.add_view(request,video_pk)
        self.add_history(request,video_pk)

        private_users = CustomUser.objects.filter(private=video.user.id)

        #限定動画の分岐
        if video.private:
            if not request.user.is_authenticated:
                print("限定動画：未ログインユーザーがアクセス")
                return HttpResponseForbidden()

            elif request.user.id == video.user.id:
                print("限定動画投稿者です。")
                pass

            elif request.user.is_authenticated and request.user not in private_users:
                print("未招待者が限定動画にアクセス",request.user.handle_name)
                return HttpResponseForbidden()
            else:
                print("招待者が限定動画にアクセス")

        blockeduser = CustomUser.objects.filter(blocked=video.user.id)

        if request.user in blockeduser:
            print("ブロックされています")
            return redirect( "tube:index" )
        else:
            print("ブロックされていません")

        video.views = video.views + 1
        video.save()

        img   = qrcode.make(request.build_absolute_uri()) #動画のQRコード
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qr = base64.b64encode(buffer.getvalue()).decode().replace("'", "")

        if video.comment_approval:
            comments = VideoComment.objects.filter(target=video_pk).exclude(video_comment_approval=False).order_by("-dt")

        else:
            comments = VideoComment.objects.filter(target=video_pk).order_by("-dt")

        already_good    = GoodVideo.objects.filter(target=video_pk, user=request.user.id)

        if request.user.is_authenticated:
            relates     = Video.objects.filter(category=video.category).prefetch_related('category').exclude(user__blocked=request.user.id).exclude(private=True).order_by("-dt")[:10]
        else:
            relates     = Video.objects.filter(category=video.category).prefetch_related('category').exclude(private=True).order_by("-dt")[:10]

        already_mylist  = MyList.objects.filter(target=video_pk, user=request.user.id)

        categories      = VideoCategory.objects.all()

        paginator = Paginator(comments, 10)
        comments  = paginator.get_page(1)

        report_categories = ReportCategory.objects.all()
        userpolicy = UserPolicy.objects.filter(user=request.user.id).first()


        context = {"video": video,
                   "comments": comments,
                   "already_good": already_good,
                   "already_mylist":already_mylist,
                   "relates": relates,
                   "qr":qr,
                   "categories":categories,
                   "report_categories":report_categories,
                   "userpolicy":userpolicy,
                   "private_users":private_users,
                   }

        return render(request, "tube/single/single.html", context)

    def add_view(self,request,video_pk,*args,**kwargs):
        dic             = {}

        if request.user.is_authenticated:
            dic["user"] = request.user.id
        else:
            dic["user"] = None

        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

        dic["ip"]       = ip
        dic["target"]   = video_pk
        dic["date"]     = datetime.date.today()

        serializer      = ViewSerializer(data=dic)
        if serializer.is_valid():
            serializer.save()


    def add_history(self,request,video_pk,*args,**kwargs):

        if request.user.is_authenticated:

            history = History.objects.filter(user=request.user.id, target=video_pk).first()

            if history:
                #履歴の追加加算
                history.views   = history.views + 1
                history.dt      = timezone.now()
                history.save()
            else:
                #履歴の新規作成
                data        = { "target":video_pk,
                                "user":request.user.id,}
                serializer  = HistorySerializer(data=data)

                if serializer.is_valid():
                    serializer.save()

single = SingleView.as_view()


class SingleModView(LoginRequiredMixin,views.APIView):

    #ここでコメントのページネーション↑ のクラス名変えるべきでは？
    def get(self,request,video_pk,*args,**kwargs):

        page        = 1
        if "page" in request.GET:
            page    = request.GET["page"]

        video               = Video.objects.filter(id=video_pk).first()

        if video.comment_approval:
            comments = VideoComment.objects.filter(
                target=video_pk).exclude(video_comment_approval=False).order_by("-dt")
            print("コメント承認制")

        else:
            comments = VideoComment.objects.filter(target=video_pk).order_by("-dt")
            print("コメント全てOK")

        comments_paginator  = Paginator(comments,COMMENTS_AMOUNT_PAGE)
        comments            = comments_paginator.get_page(page)

        report_categories = ReportCategory.objects.all()
        userpolicy = UserPolicy.objects.filter(user=request.user.id).first()


        #コメントをrender_to_stringテンプレートを文字列化、json化させ返却
        context     = { "comments":comments,
                        "video":video,
                        "report_categories":report_categories,
                        "userpolicy":userpolicy,
                        }
        content     = render_to_string('tube/single/comments.html', context ,request)

        json        = { "error":False,
                        "content":content,
                        }

        return JsonResponse(json)


    def post(self, request, video_pk, *args, **kwargs):

        copied   = request.POST.copy()

        copied["target"]  = video_pk
        copied["user"]    = request.user.id

        serializer  = VideoCommentSerializer(data=copied)
        json        = {}

        if serializer.is_valid():
            print("コメントバリデーションOK")
            serializer.save()

            video = Video.objects.filter(id=video_pk).first()

            if video.comment_approval:
                comments = VideoComment.objects.filter(target=video_pk).exclude(video_comment_approval=False).order_by("-dt")
                print("コメント承認制")

            else:
                comments = VideoComment.objects.filter(target=video_pk).order_by("-dt")
                comments.update(video_comment_approval=True)
                print("コメント全てOK")

            comments_paginator  = Paginator(comments,COMMENTS_AMOUNT_PAGE)
            comments            = comments_paginator.get_page(1)
            video               = Video.objects.filter(id=video_pk).first()
            userpolicy = UserPolicy.objects.filter(user=request.user.id).first()

            context     = { "comments":comments,
                            "video":video,
                            "userpolicy":userpolicy,
                            }

            content     = render_to_string('tube/single/comments.html', context, request)

            json        = { "error":False,
                            "message":"投稿完了",
                            "content":content,
                            }

        else:
            print("コメントバリデーションNG")
            json        = {"error":True,
                           "message":"入力内容に誤りがあります。",
                           "content":"",
                           }


        return JsonResponse(json)

    def patch(self,request,video_pk,*args,**kwargs):
        #いいね処理、マイリスト処理。

        serializer  = RateSerializer(data=request.data)

        if not serializer.is_valid():

            json = {"error": True,
                    "message": "入力内容に誤りがあります。",
                    "content": "",
                    }

            return JsonResponse(json)

        validated_data  = serializer.validated_data

        if validated_data["flag"]:

            data    = GoodVideo.objects.filter(user=request.user.id, target=video_pk).first()
            if data:
                data.delete()
                print("削除")
                error = False
                message = "「いいね」を取り消しました。"

            else:
                data    = { "user":request.user.id,
                            "target":video_pk,
                            }
                serializer  = GoodSerializer(data=data)

                if serializer.is_valid():
                    print("セーブ")
                    serializer.save()
                    error = False
                    message = "「いいね」しました。"
                else:
                    print("バリデーションエラー")
                    error = True
                    message = "登録に失敗しました。"

        else:
            data    = MyList.objects.filter(user=request.user.id, target=video_pk).first()
            if data:
                data.delete()
                print("削除")
                error = False
                message = "マイリストから削除しました。"
            else:
                data = {"user": request.user.id,
                        "target": video_pk,
                        }
                serializer = MyListSerializer(data=data)

                if serializer.is_valid():
                    print("セーブ")
                    serializer.save()
                    error = False
                    message = "マイリストに登録しました。"
                else:
                    print("バリデーションエラー")
                    error = True
                    message = "登録に失敗しました。"

        already_good    = GoodVideo.objects.filter(target=video_pk, user=request.user.id)
        already_mylist  = MyList.objects.filter(target=video_pk, user=request.user.id)
        video           = Video.objects.filter(id=video_pk).first()

        context = {"already_good": already_good,
                   "already_mylist": already_mylist,
                   "video": video,
                   }

        content = render_to_string('tube/single/rate.html', context, request)

        json = {"error": error,
                "message": message,
                "content": content,
                }

        return JsonResponse(json)

    #動画に対する編集処理（リクエストユーザーが動画投稿者であることを確認して実行）
    def put(self,request,video_pk,*args,**kwargs):

        json = {"error":True }

        # 編集対象の動画を特定する。
        instance = Video.objects.filter(id=video_pk).first()

        # 無い場合はそのまま返す
        if not instance:
            return JsonResponse(json)

        # TIPS:get_object_or_404を使う方法もある、いずれにせよレコード単体のオブジェクトをシリアライザの第一引数に指定して、編集対象を指定する必要がある点で同じ。こちらは存在しない場合404をリターンするためif文で分岐させる必要はない。
        # instance    = get_object_or_404(Video.objects.all(), pk=video_pk)

        # 受け取ったリクエストのdataにAjaxの送信内容が含まれているのでこれをバリデーション。編集対象は先ほどvideo_pkで特定したレコード単体
        serializer = VideoEditSerializer(instance, data=request.data)

        if serializer.is_valid():
            serializer.save()
            json = {"error": False}
            Video.objects.filter(id=video_pk).update(edited=True)

        return JsonResponse(json)

    #動画に対する削除処理
    def delete(self,request,video_pk,*args,**kwargs):

        video   = Video.objects.filter(id=video_pk).first()

        if video.user.id == request.user.id:
            print("削除")
            video.delete()
            error   = False
            message = "削除しました。"

        else:
            print("拒否")
            error   = True
            message = "削除できませんでした。"

        json        = {"error":error,
                       "message":message,}

        return JsonResponse(json)

single_mod = SingleModView.as_view()


# コメントの削除、編集
class VideoCommentEditView(LoginRequiredMixin,views.APIView):

    def delete(self, request, comment_pk, *args, **kwargs):

        v_comment = VideoComment.objects.filter(id=comment_pk).first()

        v_comment.delete()
        print("コメント削除")

        error = False
        message = "削除しました。"

        json = {"error": error,
                "message": message,}

        return JsonResponse(json)


    def put(self,request,comment_pk,*args,**kwargs):

        comment = VideoComment.objects.filter(id=comment_pk).first()

        video_pk = comment.target.id

        json = {"error":True }

        # 無い場合はそのまま返す
        if not comment:
            return JsonResponse(json)

        copied   = request.data.copy()
        copied["target"]  = video_pk
        copied["user"]    = request.user.id

        serializer  = VideoCommentEditSerializer(comment, data=copied)

        if serializer.is_valid():

            serializer.save()
            print("コメント編集バリデーションOK")

            video = Video.objects.filter(id=video_pk).first()

            if video.comment_approval:
                VideoComment.objects.filter(id=comment_pk).update(video_comment_approval=False)

                comments = VideoComment.objects.filter(target=video_pk).exclude(video_comment_approval=False).order_by("-dt")
                print("コメント承認制")

            else:
                comments = VideoComment.objects.filter(target=video_pk).order_by("-dt")
                print("コメント非承認制")

            comments_paginator  = Paginator(comments,COMMENTS_AMOUNT_PAGE)
            comments            = comments_paginator.get_page(1)

            userpolicy = UserPolicy.objects.filter(user=request.user.id).first()

            context     = { "comments":comments,
                            "video":video,
                            "userpolicy":userpolicy,
                            }

            content     = render_to_string('tube/single/comments.html', context, request)

            json        = { "error":False,
                            "message":"コメント編集完了しました。",
                            "content":content,
                            }

        else:
            print("コメント編集バリデーションNG")
            json        = {"error":True,
                           "message": "入力内容に誤りがあります。",
                           "content": "",
                           }


        return JsonResponse(json)

video_comment_edit = VideoCommentEditView.as_view()


# 動画コメントのリプライの削除、編集
class VideoCommentReplyEditView(LoginRequiredMixin,views.APIView):

    def delete(self, request, reply_pk, *args, **kwargs):

        comment_reply = VideoCommentReply.objects.filter(id=reply_pk).first()

        comment_reply.delete()
        print("コメント削除")

        error = False
        message = "削除しました。"

        json = {"error": error,
                "message": message,}

        return JsonResponse(json)


    def put(self,request,reply_pk,*args,**kwargs):
        print(request.data)


        reply = VideoCommentReply.objects.filter(id=reply_pk).first()
        print(reply)
        comment_pk = reply.target.id

        video_pk = reply.target.target.id

        json = {"error":True }

        # 無い場合はそのまま返す
        if not reply:
            return JsonResponse(json)

        copied   = request.data.copy()
        copied["target"]  = comment_pk
        copied["user"]    = request.user.id

        serializer  = VideoCommentReplyEditSerializer(reply, data=copied)

        if serializer.is_valid():
            serializer.save()
            print("リプライ編集バリデーションOK")

            v = Video.objects.filter(id=video_pk).first()

            if v.comment_approval:
                VideoCommentReply.objects.filter(target=comment_pk).update(comment_reply_approval=False)

                replies = VideoCommentReply.objects.filter(target=comment_pk).exclude(comment_reply_approval=False).order_by("-dt")
                comments = VideoComment.objects.filter(target=video_pk).exclude(video_comment_approval=False).order_by("-dt")

                print("コメント承認制")
            else:

                replies = VideoCommentReply.objects.filter(target=comment_pk).order_by("-dt")
                comments = VideoComment.objects.filter(target=video_pk).order_by("-dt")

                print("コメント全てOK")

            comments_paginator  = Paginator(comments,COMMENTS_AMOUNT_PAGE)
            comments            = comments_paginator.get_page(1)
            video               = Video.objects.filter(id=video_pk).first()
            userpolicy = UserPolicy.objects.filter(user=request.user.id).first()

            context     = { "replies":replies,
                            "comments":comments,
                            "video":video,
                            "userpolicy":userpolicy,
                            }

            content     = render_to_string('tube/single/comments.html', context, request)

            json        = { "error":False,
                            "message":"編集完了しました。",
                            "content":content,
                            }

        else:
            print("コメント編集バリデーションNG")
            json        = {"error":True,
                           "message": "入力内容に誤りがあります。",
                           "content": "",
                           }

        return JsonResponse(json)


video_comment_reply_edit = VideoCommentReplyEditView.as_view()



# 動画コメントの3次コメントの削除、編集
class VideoCommentReplyToReplyEditView(LoginRequiredMixin,views.APIView):

    def delete(self, request, r_to_reply_pk, *args, **kwargs):

        r_to_reply = VideoCommentReplyToReply.objects.filter(id=r_to_reply_pk).first()
        r_to_reply.delete()
        print("コメント削除")

        error = False
        message = "削除しました。"

        json = {"error": error,
                "message": message,}

        return JsonResponse(json)


    def put(self,request,r_to_reply_pk,*args,**kwargs):
        print(request.data)

        r_to_reply = VideoCommentReplyToReply.objects.filter(id=r_to_reply_pk).first()
        print(r_to_reply)

        reply_pk   = r_to_reply.target.id
        comment_pk = r_to_reply.target.target.id
        video_pk   = r_to_reply.target.target.target.id

        json = {"error":True }

        # 無い場合はそのまま返す
        if not r_to_reply:
            return JsonResponse(json)

        copied   = request.data.copy()
        copied["target"]  = reply_pk
        copied["user"]    = request.user.id

        serializer  = VideoCommentReplyToReplyEditSerializer(r_to_reply, data=copied)

        if serializer.is_valid():

            serializer.save()
            print("リプライ編集バリデーションOK")

            video = Video.objects.filter(id=video_pk).first()
            if video.comment_approval:
                VideoCommentReplyToReply.objects.filter(id=r_to_reply_pk).update(reply_to_reply_approval=False)

                r_to_replies = VideoCommentReplyToReply.objects.filter(id=r_to_reply_pk).exclude(
                    reply_to_reply_approval=False).order_by("-dt")
                replies = VideoCommentReply.objects.filter(target=comment_pk).exclude(comment_reply_approval=False).order_by("-dt")
                comments = VideoComment.objects.filter(target=video_pk).exclude(video_comment_approval=False).order_by("-dt")

                print("コメント承認制")
            else:
                r_to_replies = VideoCommentReplyToReply.objects.filter(id=r_to_reply_pk).order_by("-dt")
                print("コメント全てOK")

                replies = VideoCommentReply.objects.filter(target=comment_pk).order_by("-dt")

                comments = VideoComment.objects.filter(target=video_pk).order_by("-dt")

            comments_paginator  = Paginator(comments,COMMENTS_AMOUNT_PAGE)
            comments            = comments_paginator.get_page(1)
            userpolicy = UserPolicy.objects.filter(user=request.user.id).first()

            context     = { "r_to_replies":r_to_replies,
                            "replies":replies,
                            "comments":comments,
                            "video":video,
                            "userpolicy":userpolicy,
                            }

            content     = render_to_string('tube/single/comments.html', context, request)

            json        = { "error":False,
                            "message":"編集完了しました。",
                            "content":content,
                            }

        else:
            print("リプライ編集バリデーションNG")
            json        = {"error":True,
                           "message": "入力内容に誤りがあります。",
                           "content": "",
                           }

        return JsonResponse(json)


video_comment_r_to_reply_edit = VideoCommentReplyToReplyEditView.as_view()




# GET:リプライの参照、レンダリングして返す。POST:リプライの送信とバリデーション保存。いずれもAjaxで実装させる

# CHECK:ここのcomment_pkはコメントのID意味している。
class VideoCommentReplyView(LoginRequiredMixin,views.APIView):

    def get(self, request, comment_pk, *args, **kwargs):

        c =VideoComment.objects.filter(id=comment_pk).first()

        json = {"error": True, }

        if c.target.comment_approval:
            replies = VideoCommentReply.objects.filter(target=comment_pk).exclude(comment_reply_approval=False).order_by("-dt")
            print("コメント承認制")
        else:
            replies = VideoCommentReply.objects.filter(target=comment_pk).order_by("-dt")
            print("コメント全てOK")

        report_categories = ReportCategory.objects.all()

        context = {"replies": replies,
                   "report_categories":report_categories,}
        content = render_to_string('tube/single/comments_reply.html', context, request)

        json["error"] = False
        json["content"] = content

        return JsonResponse(json)

    def post(self, request, comment_pk, *args, **kwargs):

        copied = request.POST.copy()
        copied["target"] = comment_pk
        copied["user"] = request.user.id

        serializer = VideoCommentReplySerializer(data=copied)

        json = {"error": True}

        if serializer.is_valid():
            print("リプライバリデーションOK")
            json["error"] = False
            serializer.save()

            c = VideoComment.objects.filter(id=comment_pk).first()
            if c.target.comment_approval:
                replies = VideoCommentReply.objects.filter(target=comment_pk).exclude(comment_reply_approval=False).order_by("-dt")
                print("コメント承認制")
                json["message"] = "コメントを受け付けました。承認後に表示されます。"
            else:
                replies = VideoCommentReply.objects.filter(target=comment_pk).order_by("-dt")
                replies.update(comment_reply_approval=True)
                print("コメント not 拒否、not 承認制、既読処理")

        else:
            print("リプライバリデーションNG")

        context = {"replies": replies}
        content = render_to_string('tube/single/comments_reply.html', context, request)

        json["content"] = content

        return JsonResponse(json)


video_comment_reply = VideoCommentReplyView.as_view()


# CHECK:ここのvideocommentreply_pkはコメントへのリプライのIDを意味している。
class VideoCommentReplyToReplyView(LoginRequiredMixin,views.APIView):

    def get(self, request, videocommentreply_pk, *args, **kwargs):

        r = VideoCommentReply.objects.filter(id=videocommentreply_pk).first()

        json = {"error": True, }

        if r.target.target.comment_approval:
            r_to_replies = VideoCommentReplyToReply.objects.filter(target=videocommentreply_pk).exclude(reply_to_reply_approval=False).order_by("-dt")
            print("コメント承認制")

        else:
            r_to_replies = VideoCommentReplyToReply.objects.filter(target=videocommentreply_pk).order_by("-dt")

            print("コメント not 拒否、not 承認制")

        report_categories = ReportCategory.objects.all()

        context = {"r_to_replies": r_to_replies,
                   "report_categories":report_categories,}
        content = render_to_string('tube/single/comments_reply_to_reply.html', context, request)

        json["error"] = False
        json["content"] = content

        return JsonResponse(json)

    def post(self, request, videocommentreply_pk, *args, **kwargs):

        copied = request.POST.copy()
        copied["target"] = videocommentreply_pk
        copied["user"] = request.user.id

        serializer = VideoCommentReplyToReplySerializer(data=copied)

        json = {"error": True}

        if serializer.is_valid():
            print("リプライへのリプライバリデーションOK")

            json["error"] = False
            serializer.save()

            r = VideoCommentReply.objects.filter(id=videocommentreply_pk).first()

            if r.target.target.comment_approval:
                r_to_replies = VideoCommentReplyToReply.objects.filter(target=videocommentreply_pk).exclude(
                    reply_to_reply_approval=False).order_by("-dt")
                print("コメント承認制")
                json["message"] = "コメントを受け付けました。承認後に表示されます。"

            else:
                r_to_replies = VideoCommentReplyToReply.objects.filter(target=videocommentreply_pk).order_by("-dt")
                r_to_replies.update(reply_to_reply_approval=True)

                print("コメント not 拒否、not 承認制、既読処理")

        else:
            print("リプライへのリプライバリデーションNG")

        context = {"r_to_replies": r_to_replies}
        content = render_to_string('tube/single/comments_reply_to_reply.html', context, request)

        json["content"] = content

        return JsonResponse(json)


video_comment_reply_to_reply = VideoCommentReplyToReplyView.as_view()


# ランキング表示
class RankingView(views.APIView):

    # ランキング計算式
    def rank_calc(self, play, mylist, good, comment):
        return play + mylist + good + comment

    #モデルオブジェクトの状態をキープするため、重複をまとめてひとつのレコードに加算する
    def aggregate(self,obj,*args,**kwargs):

        #重複する動画IDがあれば、ひとつのアクティビティにまとめる(スコアを加算)。その時、ユーザー属性は削除
        id_list     = []
        new_objects = []

        initial     = Activity()

        for o in obj:
            if o.target.id in id_list:
    
                #一箇所にまとめる
                for n in new_objects:
                    if o.target.id == n.target.id:
                        #スコアを加算
                        n.score += o.score
                        break

                continue

            #この状態でアペンドすると、アクティビティに紐付いたユーザーの情報まで記録されるため、予め削除しておく。
            o.user  = initial.user
            new_objects.append(o)
            id_list.append(o.target.id)

        #ソーティング
        # https://stackoverflow.com/questions/2412770/good-ways-to-sort-a-queryset-django
        import operator

        return sorted(new_objects, key=operator.attrgetter('score'), reverse=True)


    def get(self, request, *args, **kwargs):

        context = {}

        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)
        last_week = today - datetime.timedelta(days=7)
        last_month = today - datetime.timedelta(days=30)

        yesterday_query = Q(date=yesterday)
        last_week_query = Q(date__gte=last_week, date__lte=yesterday)
        last_month_query = Q(date__gte=last_month, date__lte=yesterday)

        # 同一動画の複数のレコードを1つに束ね、なおかつスコアが大きい順に並べる

        context["daily_all_ranks"]      = self.aggregate(Activity.objects.filter(yesterday_query).annotate(
                                            score = self.rank_calc(play=Sum("play"),mylist=Sum("mylist"),good=Sum("good"),comment=Sum("comment")) ).order_by())
        context["weekly_all_ranks"]     = self.aggregate(Activity.objects.filter(last_week_query).annotate(
                                            score = self.rank_calc(play=Sum("play"),mylist=Sum("mylist"),good=Sum("good"),comment=Sum("comment")) ).order_by())
        context["monthly_all_ranks"]    = self.aggregate(Activity.objects.filter(last_month_query).annotate(
                                            score = self.rank_calc(play=Sum("play"),mylist=Sum("mylist"),good=Sum("good"),comment=Sum("comment")) ).order_by())

        """
        # ただし、valuesを使用しているため、辞書型になる。テンプレート側で動画タイトル、サムネイルの参照が通常のモデルオブジェクトとは違う。
        context["daily_all_ranks"] = sorted(
            Activity.objects.filter(yesterday_query).values("target", "target__title", "target__thumbnail").annotate(
                score=self.rank_calc(play=Sum("play"), mylist=Sum("mylist"), good=Sum("good"),
                                     comment=Sum("comment"))
            ).order_by(), key=lambda obj: obj["score"], reverse=True)
        context["weekly_all_ranks"] = sorted(
            Activity.objects.filter(last_week_query).values("target", "target__title", "target__thumbnail").annotate(
                score=self.rank_calc(play=Sum("play"), mylist=Sum("mylist"), good=Sum("good"),
                                     comment=Sum("comment"))
            ).order_by(), key=lambda obj: obj["score"], reverse=True)
        context["monthly_all_ranks"] = sorted(
            Activity.objects.filter(last_month_query).values("target", "target__title", "target__thumbnail").annotate(
                score=self.rank_calc(play=Sum("play"), mylist=Sum("mylist"), good=Sum("good"),
                                     comment=Sum("comment"))
            ).order_by(), key=lambda obj: obj["score"], reverse=True)
        """

        context["daily_cate_ranks"] = []
        context["weekly_cate_ranks"] = []
        context["monthly_cate_ranks"] = []

        categories = VideoCategory.objects.all()

        # カテゴリごとに検索してアペンド
        for category in categories:
            dic = {}
            dic["category"] = category.name
            print(dic["category"])

            daily_dic   = dic.copy()
            weekly_dic  = dic.copy()
            monthly_dic = dic.copy()

            cate_yesterday_query  = Q(category=category.id) & yesterday_query
            cate_last_week_query  = Q(category=category.id) & last_week_query
            cate_last_month_query = Q(category=category.id) & last_month_query



            
            daily_dic["ranks"]      = self.aggregate(Activity.objects.filter(cate_yesterday_query).annotate(
                                        score = self.rank_calc(play=Sum("play"),mylist=Sum("mylist"),good=Sum("good"),comment=Sum("comment")) ).order_by())
            weekly_dic["ranks"]     = self.aggregate(Activity.objects.filter(cate_last_week_query).annotate(
                                        score = self.rank_calc(play=Sum("play"),mylist=Sum("mylist"),good=Sum("good"),comment=Sum("comment")) ).order_by())
            monthly_dic["ranks"]    = self.aggregate(Activity.objects.filter(cate_last_month_query).annotate(
                                        score = self.rank_calc(play=Sum("play"),mylist=Sum("mylist"),good=Sum("good"),comment=Sum("comment")) ).order_by())



            """
            daily_dic["ranks"]      = sorted( Activity.objects.filter(cate_yesterday_query).values("target","target__title","target__thumbnail").annotate(score   = self.rank_calc(play=Sum("play"),mylist=Sum("mylist"),good=Sum("good"),comment=Sum("comment"))).order_by(),key=lambda obj: obj["score"], reverse=True)
            weekly_dic["ranks"]     = sorted( Activity.objects.filter(cate_last_week_query).values("target","target__title","target__thumbnail").annotate(score   = self.rank_calc(play=Sum("play"),mylist=Sum("mylist"),good=Sum("good"),comment=Sum("comment"))).order_by(),key=lambda obj: obj["score"], reverse=True)
            monthly_dic["ranks"]    = sorted( Activity.objects.filter(cate_last_month_query).values("target","target__title","target__thumbnail").annotate(score   = self.rank_calc(play=Sum("play"),mylist=Sum("mylist"),good=Sum("good"),comment=Sum("comment"))).order_by(),key=lambda obj: obj["score"], reverse=True)

            """


            print(daily_dic["ranks"])

            if daily_dic["ranks"]:
                context["daily_cate_ranks"].append(daily_dic)

            if weekly_dic["ranks"]:
                context["weekly_cate_ranks"].append(weekly_dic)

            if monthly_dic["ranks"]:
                context["monthly_cate_ranks"].append(monthly_dic)

        return render(request, "tube/rank/rank.html", context)


rank = RankingView.as_view()


class UserPolicyView(views.APIView):

    def get(self,request,*args,**kwargs):

        userpolicy = UserPolicy.objects.filter(user=request.user.id).first()

        form = UserPolicyForm()
        context = { "userpolicy":userpolicy,
                    "form":form, }

        return render(request,"tube/user_policy.html", context )


    def post(self,request,*args,**kwargs):

        formset = UserPolicyForm(request.POST)

        if formset.is_valid():
            print("バリデーションOK")
            f = formset.save(commit=False)
            f.user = request.user
            f.save()

        else:
            print("バリデーションエラー")

        return redirect("tube:index")


user_policy   = UserPolicyView.as_view()


class MyPageView(LoginRequiredMixin, views.APIView):

    def get(self, request,*args, **kwargs):

        context = {}
        context["custom_user"]  = CustomUser.objects.filter(id=request.user.id).first()

        videos = Video.objects.filter(user=request.user.id).order_by("-dt")
        context["amount"] = videos.count()
        paginator = Paginator(videos, 20)

        if "page" in request.GET:
            context["videos"] = paginator.get_page(request.GET["page"])
        else:
            context["videos"] = paginator.get_page(1)

        good_videos = GoodVideo.objects.filter(user=request.user.id).order_by("-dt")
        context["g_amount"] = good_videos.count()
        paginator = Paginator(good_videos, 20)

        if "page" in request.GET:
            context["good_videos"] = paginator.get_page(request.GET["page"])
        else:
            context["good_videos"] = paginator.get_page(1)

        return render(request, "tube/mypage/mypage.html", context)


    def post(self,request, *args,**kwargs):

        instance = CustomUser.objects.get(id=request.user.id)

        serializer = IconSerializer(instance, data=request.data)

        if serializer.is_valid():
            serializer.save()

            custom_user = CustomUser.objects.filter(id=request.user.id).first()
            context     = {"custom_user":custom_user}

            content     = render_to_string('tube/mypage/mypage_usericon.html', context ,request)

            json = {"error": False,
                    "message":"アイコンが登録されました。",
                    "content":content,
                    }

        else:
            print("バリデーションエラー")
            json = {"error": True,
                    "message": "アイコン登録に失敗しました。",
                    }

        return JsonResponse(json)

mypage = MyPageView.as_view()



# 閲覧履歴表示
class HistoryView(LoginRequiredMixin, views.APIView):

    def get(self, request, *args, **kwargs):
        histories = History.objects.filter(user=request.user.id).order_by("-dt")[:DEFAULT_VIDEO_AMOUNT]
        amount    = len(histories)

        paginator = Paginator(histories, 10)

        if "page" in request.GET:
            histories = paginator.get_page(request.GET["page"])
        else:
            histories = paginator.get_page(1)

        context = {"histories": histories,
                   "amount": amount}

        return render(request, "tube/history.html", context)


history = HistoryView.as_view()


# おすすめ動画
class RecommendView(LoginRequiredMixin,views.APIView):

    def get(self,request,*args,**kwargs):

        return render(request, "tube/recommend.html")

recommend = RecommendView.as_view()


#News

class NewsView(views.APIView):

    def get(self, request, *args, **kwargs):

        context = {}
        context["monthly"] = News.objects.annotate(monthly_dt=TruncMonth('dt')).values('monthly_dt').annotate(
            num=Count('id')).values('monthly_dt', 'num').order_by("-monthly_dt")
        context["categories"] = NewsCategory.objects.annotate(num=Count("news"))
        context["latests"] = News.objects.all().order_by("-dt")[:10]

        if "news_pk" in kwargs:
            article = News.objects.filter(id=kwargs["news_pk"]).first()

            if not article:
                return redirect("tube:news")

            context["article"] = article
            return render(request, "tube/news.html", context)

        # 検索処理
        if "search" in request.GET:
            search = request.GET["search"]

            if search == "" or search.isspace():
                return redirect("tube:news")

            search = search.replace("　", " ").split(" ")
            searches = [w for w in search if w != ""]

            query = Q()
            for w in searches:
                query &= Q(Q(title__contains=w) | Q(content__contains=w))

            articles = News.objects.filter(query).order_by("-dt")

        # 月別アーカイブ
        elif "month" in request.GET and "year" in request.GET:
            serializer = YearMonthSerializer(data=request.GET)

            if not serializer.is_valid():
                return redirect("tube:news")

            validated = serializer.validated_data
            articles = News.objects.filter(dt__year=validated["year"], dt__month=validated["month"]).order_by("-dt")

        # カテゴリ検索
        elif "category" in request.GET:
            category = request.GET["category"]
            articles = News.objects.filter(category__name=category).order_by("-dt")

        # 未指定
        else:
            articles = News.objects.all().order_by("-dt")

        # ページネーション
        paginator = Paginator(articles, 4)
        page = 1
        if "page" in request.GET:
            page = request.GET["page"]

        context["articles"] = paginator.get_page(page)

        return render(request, "tube/news.html", context)


news = NewsView.as_view()


# 通知表示
class NotifyView(LoginRequiredMixin, views.APIView):

    def get(self, request, *args, **kwargs):
        videos = Video.objects.filter(user=request.user.id).order_by("-dt")
        context = {}

        if not videos:
            context["notify_targets"] = NotifyTarget.objects.filter(user=request.user.id).order_by("-dt")

            return render(request, "tube/notify.html", context)

        list = []
        for v in videos:
            list.append(v.id)

            #このif notがないと、承認待ちコメントがある状態で全動画のコメント承認制解除したときに、通知欄でエラーが起きる。
            if not v.comment_approval:
                context["comments"] = VideoComment.objects.filter(target__id__in=list).exclude(read=True).order_by("-dt")
                context["replies"]  = VideoCommentReply.objects.filter(target__target__id__in=list).exclude(read=True).order_by("-dt")
                context["r_to_r"]   = VideoCommentReplyToReply.objects.filter(target__target__target__id__in=list).exclude(read=True).order_by("-dt")

                context["notify_targets"] = NotifyTarget.objects.filter(user=request.user.id).order_by("-dt")

            else:
                context["comments_approval"] = VideoComment.objects.filter(target__id__in=list,
                                                                video_comment_approval=False).order_by("-dt")
                context["replies_approval"]  = VideoCommentReply.objects.filter(target__target__id__in=list,
                                                                    comment_reply_approval=False).order_by("-dt")
                context["r_to_r_approval"]  = VideoCommentReplyToReply.objects.filter(target__target__target__id__in=list,
                                                                          reply_to_reply_approval=False).order_by("-dt")

                context["comments"] = VideoComment.objects.filter(target__id__in=list).exclude(read=True).order_by("-dt")
                context["replies"]  = VideoCommentReply.objects.filter(target__target__id__in=list).exclude(read=True).order_by("-dt")
                context["r_to_r"]   = VideoCommentReplyToReply.objects.filter(target__target__target__id__in=list).exclude(read=True).order_by("-dt")

                # アクセスしたユーザーの通知を
                context["notify_targets"] = NotifyTarget.objects.filter(user=request.user.id).order_by("-dt")

        return render(request, "tube/notify.html", context)


    def patch(self, request, *args, **kwargs):
        #お知らせの既読処理
        json = {"error": True}

        data = request.data.copy()
        data["user"] = request.user.id
        print(data)

        serializer = NotifyTargetSerializer(data=data)

        if serializer.is_valid():
            validated = serializer.validated_data

            # TIPS:notify_targetのidで指定すると、通知を受け取ったユーザー以外が既読にされてしまう可能性があるため、
            # unique_togetherを実装した場合、.first()でひとつだけでいい。
            notify_target = NotifyTarget.objects.filter(notify=validated["notify"], user=validated["user"]).first()

            if notify_target:
                notify_target.read = True
                notify_target.save()

                json["error"] = False
                print("バリデーションOK")
            else:
                print("存在しないNotify")

        else:
            json["error"] = True
            print("バリデーションNG")

        return JsonResponse(json)

    def post(self, request, *args, **kwargs):
        #既読の通知を全て削除
        instance = NotifyTarget.objects.filter(user=request.user.id).exclude(read=False)
        instance.delete()

        return redirect("tube:notify")


notify = NotifyView.as_view()

#notify.html 動画コメント欄を空(既読)にする。
class CommentAlreadyReadView(LoginRequiredMixin,views.APIView):

    def post(self,request,*args,**kwargs):

        videos = Video.objects.filter(user=request.user.id)

        list=[]
        for v in videos:
            list.append(v.id)

        comments = VideoComment.objects.filter(target__id__in=list).exclude(read=True)
        replies  = VideoCommentReply.objects.filter(target__target__id__in=list).exclude(read=True)
        r_to_r   = VideoCommentReplyToReply.objects.filter(target__target__target__id__in=list).exclude(read=True)

        comments.update(read=True)
        replies.update(read=True)
        r_to_r.update(read=True)

        return redirect("tube:notify")


    def patch(self,request,*args,**kwargs):
        #checkを既読
        serializer = UUIDListSerializer(data=request.data)

        if serializer.is_valid():
            data = serializer.validated_data

            VideoComment.objects.filter(id__in=data["id"]).update(read=True)
            VideoCommentReply.objects.filter(id__in=data["id"]).update(read=True)
            VideoCommentReplyToReply.objects.filter(id__in=data["id"]).update(read=True)

            json = {"error": False,
                    }
        else:
            json = {"error": True, }

            print("バリデーションNG:既読処理失敗")

        return JsonResponse(json)


    def delete(self, request, *args, **kwargs):
        #通知欄の承認待ちコメント、動画コメントの削除

        serializer = UUIDListSerializer(data=request.data)

        if serializer.is_valid():
            data = serializer.validated_data

            comment = VideoComment.objects.filter(id__in=data["id"])
            comment.delete()

            second_comment = VideoCommentReply.objects.filter(id__in=data["id"])
            second_comment.delete()

            third_comment = VideoCommentReplyToReply.objects.filter(id__in=data["id"])
            third_comment.delete()

            json = {"error": False,
                    }
        else:
            json = {"error": True, }

            print("バリデーションNG:削除処理失敗")

        return JsonResponse(json)


comment_already_read = CommentAlreadyReadView.as_view()


#notify.htmlでチェックしたコメントを承認/削除
class CommentApprovalView(LoginRequiredMixin,views.APIView):

    def post(self,request,*args,**kwargs):
        #通知欄の承認待ちコメント全て承認

        videos = Video.objects.filter(user=request.user.id)

        list=[]
        for v in videos:
            list.append(v.id)

        comments = VideoComment.objects.filter(target__id__in=list).exclude(video_comment_approval=True)
        replies  = VideoCommentReply.objects.filter(target__target__id__in=list).exclude(comment_reply_approval=True)
        r_to_r   = VideoCommentReplyToReply.objects.filter(target__target__target__id__in=list).exclude(reply_to_reply_approval=True)

        comments.update(video_comment_approval=True,read=True)
        replies.update(comment_reply_approval=True,read=True)
        r_to_r.update(reply_to_reply_approval=True,read=True)

        return redirect("tube:notify")

    def patch(self,request,*args,**kwargs):
        #チェックされたものを承認

        serializer = UUIDListSerializer(data=request.data)

        if serializer.is_valid():
            print("バリデーションOK：コメント承認と既読処理")
            data = serializer.validated_data
            print(data)

            VideoComment.objects.filter(id__in=data["id"]).update(video_comment_approval=True,read=True)
            VideoCommentReply.objects.filter(id__in=data["id"]).update(comment_reply_approval=True,read=True)
            VideoCommentReplyToReply.objects.filter(id__in=data["id"]).update(reply_to_reply_approval=True,read=True)

            json = {"error": False,}
        else:
            json = {"error": True, }

            print("バリデーション失敗：コメント承認失敗")

        return JsonResponse(json)

comment_approval = CommentApprovalView.as_view()


#マイリスト
class MyListView(LoginRequiredMixin,views.APIView):

    def get(self,request,*args,**kwargs):

        context = {}
        mylists= MyList.objects.filter(user=request.user.id).order_by("-dt")

        context["amount"] = len(mylists)

        paginator = Paginator(mylists, 10)
        if "page" in request.GET:
            context["mylists"] = paginator.get_page(request.GET["page"])
        else:
            context["mylists"] = paginator.get_page(1)

        return render(request,"tube/mylist.html",context)


    def post(self,request,*args,**kwargs):

        instance = MyList.objects.filter(user=request.user.id)
        instance.delete()

        return redirect("tube:mylist")


    def delete(self,request,*args,**kwargs):

        serializer = UUIDListSerializer(data=request.data)

        if serializer.is_valid():
            data = serializer.validated_data

            instance = MyList.objects.filter(id__in=data["id"])
            instance.delete()

            json = {"error": False,}
        else:
            json = {"error": True, }

            print("バリデーションNG:削除処理失敗")

        return JsonResponse(json)

mylist = MyListView.as_view()


class ConfigViews(LoginRequiredMixin,views.APIView):

    def get(self, request, *args, **kwargs):

        #全ての投稿動画のコメントを拒否、承認制。
        refuse   = VideoCommentRefuse.objects.filter(user=request.user.id).first()
        approval = VideoCommentApproval.objects.filter(user=request.user.id).first()

        context = {"refuse":refuse,
                   "approval":approval,
                  }

        return render(request, "tube/config.html", context)

    def post(self,request,*args,**kwargs):
        #動画に対するコメントを全て拒否。

        instance = VideoCommentRefuse.objects.filter(user=request.user.id).first()

        formset = CommentRefuseForm(request.POST, instance=instance)

        if formset.is_valid():
            print("コメント全拒否バリデーションOK")
            f = formset.save(commit=False)
            f.user = request.user
            f.video_comment_refuse = True
            f.save()
            Video.objects.filter(user=request.user.id).update(comment_refuse=True)
            json = {"error": False, }
        else:
            json = {"error": True, }
            print("コメント全拒否バリデーションエラー")

        return JsonResponse(json)


config = ConfigViews.as_view()

class CommentAcceptViews(LoginRequiredMixin,views.APIView):

    def post(self,request,*args,**kwargs):
        #config.html 動画に対するコメントを全て受け付ける。

        instance = VideoCommentRefuse.objects.filter(user=request.user.id).first()
        instance.delete()
        Video.objects.filter(user=request.user.id).update(comment_refuse=False)

        print("コメント全拒否解除")
        json = {"error": False, }

        return JsonResponse(json)

comment_accept = CommentAcceptViews.as_view()


#全ての動画のコメント承認制を解除。
class CommentApproval1Views(LoginRequiredMixin,views.APIView):

    def post(self,request,*args,**kwargs):

        instance = VideoCommentApproval.objects.filter(user=request.user.id).first()
        instance.delete()

        videos = Video.objects.filter(user=request.user.id)
        videos.update(comment_approval=False)

        #ここで、承認待ちコメントは承認処理をしておく。
        list = []
        for v in videos:
            list.append(v.id)

            comments = VideoComment.objects.filter(target__id__in=list).exclude(video_comment_approval=True)
            replies  = VideoCommentReply.objects.filter(target__target__id__in=list).exclude(comment_reply_approval=True)
            r_to_r   = VideoCommentReplyToReply.objects.filter(target__target__target__id__in=list).exclude(reply_to_reply_approval=True)
    
            comments.update(video_comment_approval=True)
            replies.update(comment_reply_approval=True)
            r_to_r.update(reply_to_reply_approval=True)

        print("全動画のコメント承認制解除")

        json = {"error": False, }

        return JsonResponse(json)

comment_approval1 = CommentApproval1Views.as_view()


#全動画をコメント承認制にする。
class CommentApproval2Views(LoginRequiredMixin,views.APIView):

    def post(self,request,*args,**kwargs):

        instance = VideoCommentApproval.objects.filter(user=request.user.id).first()

        formset = CommentApprovalForm(request.POST, instance=instance)

        if formset.is_valid():
            f = formset.save(commit=False)
            f.user = request.user
            f.video_comment_approval = True
            f.save()
            Video.objects.filter(user=request.user.id).update(comment_approval=True)

            instance = VideoCommentRefuse.objects.filter(user=request.user.id).first()
            if instance:
                instance.delete()

            Video.objects.filter(user=request.user.id).update(comment_refuse=False)

            print("全動画をコメント承認制にした（コメント拒否は解除）")
            json = {"error": False, }

        else:
            json = {"error": True, }
            print("全動画をコメント承認制バリデーションエラー")

        return JsonResponse(json)

comment_approval2 = CommentApproval2Views.as_view()


class SingleVideoCommentAcceptView(LoginRequiredMixin,views.APIView):

    def post(self,request,video_pk,*args,**kwargs):
        #個々の動画に対するコメントを受け付ける。

        Video.objects.filter(id=video_pk).update(comment_refuse=False)
        print("この動画に対するコメント拒否解除")

        return redirect("tube:single", video_pk)

single_video_comment_accept = SingleVideoCommentAcceptView.as_view()


class SingleVideoCommentRefuseView(LoginRequiredMixin, views.APIView):

    def post(self, request,video_pk, *args, **kwargs):
        # 個々の動画に対するコメントを拒否する。
        Video.objects.filter(id=video_pk).update(comment_refuse=True)

        instance = VideoCommentApproval.objects.filter(user=request.user.id).first()
        if instance:
            instance.delete()
            print("全動画に対するコメント承認制は解除。個々のものは残る。")

        print("この動画のコメント拒否(承認制は解除)")

        return redirect("tube:single",video_pk)

single_video_comment_refuse = SingleVideoCommentRefuseView.as_view()

#個々の動画のコメント承認制を解除する
class SingleVideoCommentApproval1View(LoginRequiredMixin, views.APIView):

    def post(self, request,video_pk, *args, **kwargs):

        Video.objects.filter(id=video_pk).update(comment_approval=False)
        print("この動画のコメント承認制を解除した")

        comments = VideoComment.objects.filter(target__id=video_pk).exclude(video_comment_approval=True)
        replies = VideoCommentReply.objects.filter(target__target__id=video_pk).exclude(comment_reply_approval=True)
        r_to_r = VideoCommentReplyToReply.objects.filter(target__target__target__id=video_pk).exclude(
            reply_to_reply_approval=True)

        comments.update(video_comment_approval=True)
        replies.update(comment_reply_approval=True)
        r_to_r.update(reply_to_reply_approval=True)
        print("承認待ちコメントは自動的に承認")

        return redirect("tube:single",video_pk)


single_video_comment_approval1 = SingleVideoCommentApproval1View.as_view()

#個々の動画のコメントを承認制にする
class SingleVideoCommentApproval2View(LoginRequiredMixin, views.APIView):

    def post(self, request,video_pk, *args, **kwargs):

        print(video_pk)
        Video.objects.filter(id=video_pk).update(comment_approval=True,comment_refuse=False)

        print("この動画のコメントを承認制にした(コメント拒否の場合は解除)")

        instance = VideoCommentRefuse.objects.filter(user=request.user.id).first()
        if instance:
            instance.delete()
            print("コメント全拒否は解除。")

        return redirect("tube:single",video_pk)

single_video_comment_approval2 = SingleVideoCommentApproval2View.as_view()


#ユーザーページの表示
class UserSingleView(LoginRequiredMixin,views.APIView):

    def get(self, request, pk, *args, **kwargs):

        user    = CustomUser.objects.filter(id=pk).first()

        blockeduser = CustomUser.objects.filter(blocked=user.id)

        if request.user in blockeduser:
            print("ブロックされています")
            return redirect( "tube:index" )
        else:
            print("ブロックされていません")


        #フォロー中のユーザー、ブロック中のユーザーの一覧
        follow_users = FollowUser.objects.filter(from_user=pk)
        block_users  = BlockUser.objects.filter(from_user=pk)


        #フォロワー
        follower_users    = FollowUser.objects.filter(to_user=pk)

        #招待者
        private_users = PrivateUser.objects.filter(from_user=pk)

        private_videos     = Video.objects.filter(user=pk, private=True).order_by("-dt")

        p_amount = private_videos.count()
        paginator = Paginator(private_videos, 20)

        if "page" in request.GET:
            private_videos = paginator.get_page(request.GET["page"])
        else:
            private_videos = paginator.get_page(1)

        videos = Video.objects.filter(user=pk).exclude(private=True).order_by("-dt")

        amount = videos.count()
        paginator = Paginator(videos, 20)

        if "page" in request.GET:
            videos = paginator.get_page(request.GET["page"])
        else:
            videos = paginator.get_page(1)

        #掲示板
        id_list = []
        for follow in follow_users:
            id_list.append(follow.to_user.id)  #フォロー中のユーザーidをリストに。

        id_list.append(user.id)  #自分自身のidをリストに追加。

        topics  = Topic.objects.filter(user__id__in=id_list).order_by("-dt")  #自分とフォローユーザーのtopics

        context = { "user":user,
                    "follow_users":follow_users,
                    "block_users":block_users,
                    "follower_users":follower_users,
                    "videos":videos,
                    "amount":amount,
                    "private_videos":private_videos,
                    "p_amount":p_amount,
                    "private_users":private_users,
                    "topics":topics,
                  }

        return render(request, "tube/usersingle.html", context)

usersingle  = UserSingleView.as_view()


class UserFollowView(LoginRequiredMixin,views.APIView):

    def post(self,request,pk,*args,**kwargs):

        target_id = request.POST.get("target_id")

        followusers  = FollowUser.objects.filter(from_user=request.user.id,to_user=target_id) #from_userは自分自身。to_user はフォローした相手。

        json    = { "error":False }

        #すでにある場合は該当レコードを削除、無い場合は挿入
        #TIPS:↑メソッドやビュークラスを切り分けてしまうと、多重に中間テーブルへレコードが挿入されてしまう可能性があるため1つのメソッド内で分岐するやり方が無難。
        if followusers:
            print("ある。フォロー解除。")
            followusers.delete()

            json["message"]="フォローを解除しました。"

            return JsonResponse(json)
        else:
            print("無い")

        data        = { "from_user":request.user.id,"to_user":target_id }
        serializer  = FollowUserSerializer(data=data)

        if serializer.is_valid():
            print("フォローOK")
            serializer.save()
            json["message"] = "フォローしました。"
        else:
            print("フォロー失敗")
            json["error"]   = True

        return JsonResponse(json)


userfollow   = UserFollowView.as_view()


class UserBlockView(LoginRequiredMixin,views.APIView):

    def post(self,request,pk,*args,**kwargs):

        blockusers  = BlockUser.objects.filter(from_user=request.user.id,to_user=pk)

        json    = { "error":False }

        if blockusers:
            print("ある。ブロック解除。")
            blockusers.delete()
            json["message"]="ブロックを解除しました。"

            return JsonResponse(json)
        else:
            print("無い")

        data        = { "from_user":request.user.id,"to_user":pk }
        serializer  = BlockUserSerializer(data=data)

        if serializer.is_valid():
            print("ブロックOK")
            serializer.save()
            json["message"] = "ブロックしました。"

        else:
            print("ブロック失敗")
            json["error"]   = True

        return JsonResponse(json)


userblock   = UserBlockView.as_view()


#限定公開動画への招待
class InviteView(LoginRequiredMixin,views.APIView):

    def post(self,request,pk,*args,**kwargs):
        print(pk)

        privateusers  = PrivateUser.objects.filter(from_user=request.user.id,to_user=pk)

        json    = { "error":False }

        if privateusers:
            print("ある。招待解除。")
            privateusers.delete()
            json["message"]="招待者リストから削除しました。"

            return JsonResponse(json)
        else:
            print("無い")

        data        = { "from_user":request.user.id,"to_user":pk }
        serializer  = PrivateUserSerializer(data=data)

        if serializer.is_valid():
            print("招待OK")
            serializer.save()
            json["message"] = "招待者リストに追加しました。"

        else:
            print("招待失敗")
            json["error"]   = True

        return JsonResponse(json)

invite   = InviteView.as_view()


#自己紹介、ユーザーハンドルネーム編集
class UserEditView(LoginRequiredMixin,views.APIView):

    def post(self, request, pk, *args, **kwargs):

        instance = CustomUser.objects.filter(id=request.user.id).first()

        formset = UserInformationForm(request.POST, instance=instance)

        if formset.is_valid():
            print("バリデーションOK")
            formset.save()

        else:
            print('バリデーションエラー')

        return redirect("tube:mypage")

useredit = UserEditView.as_view()

class VideoReportView(LoginRequiredMixin,views.APIView):


    def post(self,request,pk,*args,**kwargs):
        print(pk,request.user.id)
        print(request.data)
        print(request.POST.get("target_id"))

        id = request.POST.get("target_id")

        reported = Video.objects.filter(id=id).first()
        print(reported.user)
        print(reported.user.id)

        copied = request.POST.copy()
        copied["reported_user"] = reported.user.id
        copied["report_user"]   = request.user.id

        formset = ReportForm(data=copied)

        if formset.is_valid():
            print("通報バリデーションOK")

            formset.save()
            json = {"error": False,
                    "message": "通報内容を受け取りました。当社にて内容を吟味し、対応致します。",
                    }
        else:
            print("通報バリデーションNG")
            json = { "error" :True,
                     "message":"通報内容に誤りがあります。"}

        return JsonResponse(json)

videoreport  = VideoReportView.as_view()


class AdvertisingVideoReportView(LoginRequiredMixin,views.APIView):


    def post(self,request,pk,*args,**kwargs):
        print(pk,request.user.id)
        print(request.data)
        print(request.POST.get("target_id"))

        id = request.POST.get("target_id")

        reported = AdvertisingVideo.objects.filter(id=id).first()
        print(reported.user)
        print(reported.user.id)

        copied = request.POST.copy()
        copied["reported_user"] = reported.user.id
        copied["report_user"]   = request.user.id

        formset = ReportForm(data=copied)

        if formset.is_valid():
            print("通報バリデーションOK")

            formset.save()
            json = {"error": False,
                    "message": "通報内容を受け取りました。当社にて内容を吟味し、対応致します。",
                    }
        else:
            print("通報バリデーションNG")
            json = { "error" :True,
                     "message":"通報内容に誤りがあります。"}

        return JsonResponse(json)

advertising_videoreport  = AdvertisingVideoReportView.as_view()

class VideoCommentReportView(LoginRequiredMixin,views.APIView):

    def post(self,request,pk,*args,**kwargs):
        print(pk,request.user.id)
        print(request.data)
        print(request.POST.get("target_id"))

        id = request.POST.get("target_id")

        reported = VideoComment.objects.filter(id=id).first()
        print(reported.user)
        print(reported.user.id)

        copied = request.POST.copy()
        copied["reported_user"] = reported.user.id
        copied["report_user"]   = request.user.id

        formset = ReportForm(data=copied)

        if formset.is_valid():
            print("通報バリデーションOK")

            formset.save()
            json = {"error": False,
                    "message": "通報内容を受け取りました。当社にて内容を吟味し、対応致します。",
                    }
        else:
            print("通報バリデーションNG")
            json = { "error" :True,
                     "message":"通報内容に誤りがあります。"}

        return JsonResponse(json)


video_comment_report  = VideoCommentReportView.as_view()


class VideoCommentReplyReportView(LoginRequiredMixin,views.APIView):

    def post(self,request,pk,*args,**kwargs):
        print(pk,request.user.id)
        print(request.data)
        print(request.POST.get("target_id"))

        id = request.POST.get("target_id")

        reported = VideoCommentReply.objects.filter(id=id).first()

        copied = request.POST.copy()
        copied["reported_user"] = reported.user.id
        copied["report_user"] = request.user.id

        formset = ReportForm(data=copied)

        if formset.is_valid():
            print("通報バリデーションOK")

            formset.save()
            json = {"error": False,
                    "message": "通報内容を受け取りました。当社にて内容を吟味し、対応致します。",
                    }
        else:
            print("通報バリデーションNG")
            json = { "error" :True,
                     "message":"通報内容に誤りがあります。"}

        return JsonResponse(json)


video_comment_reply_report  = VideoCommentReplyReportView.as_view()


class VideoCommentReplyToReplyReportView(LoginRequiredMixin,views.APIView):

    def post(self,request,pk,*args,**kwargs):
        print(pk,request.user.id)
        print(request.data)
        print(request.POST.get("target_id"))

        id = request.POST.get("target_id")

        reported = VideoCommentReplyToReply.objects.filter(id=id).first()

        copied = request.POST.copy()
        copied["reported_user"] = reported.user.id
        copied["report_user"] = request.user.id

        formset = ReportForm(data=copied)

        if formset.is_valid():
            print("通報バリデーションOK")

            formset.save()
            json = {"error": False,
                    "message": "通報内容を受け取りました。当社にて内容を吟味し、対応致します。",
                    }
        else:
            print("通報バリデーションNG")
            json = { "error" :True,
                     "message":"通報内容に誤りがあります。"}

        return JsonResponse(json)


video_comment_reply_to_reply_report  = VideoCommentReplyToReplyReportView.as_view()


#掲示板
class TopicView(LoginRequiredMixin,views.APIView):

    def post(self,request,pk,*args,**kwargs):
        print(request.POST)

        formset  = TopicForm(request.POST)

        if formset.is_valid():
            print("トピックバリデーションOK")
            f = formset.save(commit=False)
            f.user = request.user
            formset.save()
        else:
            print("トピックバリデーションエラー")

        return redirect( "tube:usersingle", pk )

topic  = TopicView.as_view()



#広告動画個別ページ
class AdvertisingVideoSingleView(views.APIView):

    def get(self,request, video_pk,*args, **kwargs):

        video = AdvertisingVideo.objects.filter(id=video_pk).first()

        self.add_view(request,video_pk)


        video.views = video.views + 1
        video.save()

        already_good    = GoodAdvertisement.objects.filter(target=video_pk, user=request.user.id)
        already_bad     = BadAdvertisement.objects.filter(target=video_pk, user=request.user.id)

        categories      = AdvertisingCategory.objects.all()

        report_categories = ReportCategory.objects.all()

        context = {"video": video,
                   "already_good": already_good,
                   "already_bad": already_bad,
                   "categories":categories,
                   "report_categories":report_categories,
                   }

        return render(request, "tube/single/advertisement.html", context)


    def add_view(self,request,video_pk,*args,**kwargs):
        dic             = {}

        if request.user.is_authenticated:
            dic["user"] = request.user.id
        else:
            dic["user"] = None

        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

        dic["ip"]       = ip
        dic["target"]   = video_pk
        dic["date"]     = datetime.date.today()

        serializer      = AdvertisingVideoViewSerializer(data=dic)
        if serializer.is_valid():
            serializer.save()



advertising_video_single = AdvertisingVideoSingleView.as_view()


class AdvertisingVideoModView(LoginRequiredMixin,views.APIView):

    def patch(self, request, video_pk, *args, **kwargs):
        # いいね処理、悪いね処理。

        serializer = RateSerializer(data=request.data)

        if not serializer.is_valid():
            json = {"error": True,
                    "message": "入力内容に誤りがあります。",
                    "content": "",
                    }

            return JsonResponse(json)

        validated_data = serializer.validated_data

        if validated_data["flag"]:

            data = GoodAdvertisement.objects.filter(user=request.user.id, target=video_pk).first()
            if data:
                data.delete()
                error = False
                message = "「いいね」を取り消しました。"

            else:
                data = {"user": request.user.id,
                        "target": video_pk,
                        }
                formset = GoodAdvertisementForm(data=data)

                if formset.is_valid():
                    formset.save()
                    error = False
                    message = "「いいね」しました。"
                else:
                    error = True
                    message = "登録に失敗しました。"

        else:
            data = BadAdvertisement.objects.filter(user=request.user.id, target=video_pk).first()
            if data:
                data.delete()
                error = False
                message = "「悪いね」を取り消しました。"
            else:
                data = {"user": request.user.id,
                        "target": video_pk,
                        }
                formset = BadAdvertisementForm(data=data)

                if formset.is_valid():
                    formset.save()
                    error = False
                    message = "「悪いね」しました。"
                else:
                    error = True
                    message = "登録に失敗しました。"

        already_good = GoodAdvertisement.objects.filter(target=video_pk, user=request.user.id)
        already_bad = BadAdvertisement.objects.filter(target=video_pk, user=request.user.id)
        video = AdvertisingVideo.objects.filter(id=video_pk).first()

        context = {"already_good": already_good,
                   "already_bad": already_bad,
                   "video": video,
                   }

        content = render_to_string('tube/single/advertisement_rate.html', context, request)

        json = {"error": error,
                "message": message,
                "content": content,
                }

        return JsonResponse(json)

    # 広告動画に対する編集処理（リクエストユーザーが動画投稿者であることを確認して実行）
    def put(self, request, video_pk, *args, **kwargs):

        json = {"error": True}

        instance = AdvertisingVideo.objects.filter(id=video_pk).first()

        if not instance:
            return JsonResponse(json)

        formset = AdvertisingVideoEditForm(request.data, instance=instance)

        if formset.is_valid():
            formset.save()
            json = {"error": False}

        return JsonResponse(json)

    # 動画に対する削除処理
    def delete(self, request, video_pk, *args, **kwargs):

        video = AdvertisingVideo.objects.filter(id=video_pk).first()

        if video.user.id == request.user.id:
            print("削除")
            video.delete()
            error = False
            message = "削除しました。"

        else:
            print("拒否")
            error = True
            message = "削除できませんでした。"

        json = {"error": error,
                "message": message, }

        return JsonResponse(json)


advertising_video_mod = AdvertisingVideoModView.as_view()
