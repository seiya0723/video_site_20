from django.urls import path
from . import views


app_name = "tube"
urlpatterns =[
    path('', views.index, name="index"),

    path('search/', views.search, name="search"),

    # TIPS:<型:変数名>とすることでビューに変数を与えることができる
    #idをuuidにするので、intをuuidに変える。

    path('single/<uuid:video_pk>/', views.single, name="single"),
    path('single_mod/<uuid:video_pk>/', views.single_mod, name="single_mod"),
    path('news/', views.news, name="news"),
    path('news/<uuid:news_pk>/', views.news, name="news_single"),

    ##ランキングページ。DBからデータ抜き取って表示するだけ。GET文だけ
    path('rank/', views.rank, name="rank"),
    path('user_policy/', views.user_policy, name="user_policy"),

    # 以下認証済みユーザー専用
    path('video_comment_reply/<uuid:comment_pk>/', views.video_comment_reply, name="video_comment_reply"),
    path('video_comment_reply_to_reply/<uuid:videocommentreply_pk>/', views.video_comment_reply_to_reply,
         name="video_comment_reply_to_reply"),
    path('video_comment_edit/<uuid:comment_pk>/', views.video_comment_edit, name="video_comment_edit"),
    path('video_comment_reply_edit/<uuid:reply_pk>/', views.video_comment_reply_edit, name="video_comment_reply_edit"),
    path('video_comment_r_to_reply_edit/<uuid:r_to_reply_pk>/', views.video_comment_r_to_reply_edit,
         name="video_comment_r_to_reply_edit"),

    path('mypage/', views.mypage, name="mypage"),
    path('history/', views.history, name="history"),
    path('recommend/', views.recommend, name="recommend"),
    path('notify/', views.notify, name="notify"),
    path('mylist/', views.mylist, name="mylist"),
    path('upload/', views.upload, name="upload"),
    path('advertising_video/', views.advertising_video, name="advertising_video"),

    path('config/', views.config, name="config"),
    path('videoreport/<uuid:pk>/', views.videoreport, name="videoreport"),
    path('video_comment_report/<uuid:pk>/', views.video_comment_report, name="video_comment_report"),
    path('video_comment_reply_report/<uuid:pk>/', views.video_comment_reply_report, name="video_comment_reply_report"),
    path('video_comment_reply_to_reply_report/<uuid:pk>/', views.video_comment_reply_to_reply_report, name="video_comment_reply_to_reply_report"),

    path('usersingle/<uuid:pk>/', views.usersingle, name="usersingle"),
    path('userfollow/<uuid:pk>/', views.userfollow, name="userfollow"),
    path('userblock/<uuid:pk>/', views.userblock, name="userblock"),
    path('invite/<uuid:pk>/', views.invite, name="invite"),

    path('useredit/<uuid:pk>/', views.useredit, name="useredit"),

    #config.htmlコメント受け付け
    path('comment_accept/', views.comment_accept, name="comment_accept"),

    #個々の動画でコメント受付・拒否
    path('single_video_comment_accept/<uuid:video_pk>/', views.single_video_comment_accept, name="single_video_comment_accept"),
    path('single_video_comment_refuse/<uuid:video_pk>/', views.single_video_comment_refuse, name="single_video_comment_refuse"),

    #個々の動画のコメント承認制を解除する
    path('single_video_comment_approval1/<uuid:video_pk>/', views.single_video_comment_approval1, name="single_video_comment_approval1"),
    #個々の動画のコメントを承認制にする
    path('single_video_comment_approval2/<uuid:video_pk>/', views.single_video_comment_approval2, name="single_video_comment_approval2"),

    #全ての動画のコメント承認制を解除。
    path('comment_approval1/', views.comment_approval1, name="comment_approval1"),
    #全動画をコメント承認制にする。
    path('comment_approval2/', views.comment_approval2, name="comment_approval2"),

    #通知欄・動画コメント既読処理
    path('comment_already_read/', views.comment_already_read, name="comment_already_read"),
    path('comment_approval/', views.comment_approval, name="comment_approval"),

    #掲示板usersingle.html
    path('topic/<uuid:pk>/', views.topic, name="topic"),

    #広告動画
    path('advertising_videoreport/<uuid:pk>/', views.advertising_videoreport, name="advertising_videoreport"),
    path('advertising_video_single/<uuid:video_pk>/', views.advertising_video_single, name="advertising_video_single"),
    path('advertising_video_mod/<uuid:video_pk>/', views.advertising_video_mod, name="advertising_video_mod"),

]
