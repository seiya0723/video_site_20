# Generated by Django 3.2.7 on 2021-09-20 07:47

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('tube', '0004_video_comment'),
    ]

    operations = [
        migrations.CreateModel(
            name='NewsCategory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=20, verbose_name='ニュースカテゴリ')),
            ],
            options={
                'db_table': 'news_category',
            },
        ),
        migrations.CreateModel(
            name='News',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('dt', models.DateTimeField(default=django.utils.timezone.now, verbose_name='作成日時')),
                ('start_date', models.DateField(verbose_name='カルーセル掲示期間(開始日)')),
                ('end_date', models.DateField(verbose_name='カルーセル掲示期間(終了日)')),
                ('title', models.CharField(max_length=200, verbose_name='ニュースタイトル')),
                ('content', models.CharField(max_length=2000, verbose_name='ニュース内容')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='tube.newscategory', verbose_name='ニュースカテゴリ')),
            ],
            options={
                'db_table': 'news',
            },
        ),
    ]
