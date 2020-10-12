from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings

from rest_framework_swagger.views import get_swagger_view

from calendars.views import CompleteView

schema_view = get_swagger_view(title='API')

urlpatterns = [
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^schema/', schema_view),
    re_path(r'^api/', include('rest_framework.urls')),
    re_path(r'^api/v1/', include('api.urls')),
    re_path(r'^completeview/', CompleteView.as_view())
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        re_path(r'^__debug__/', include(debug_toolbar.urls)),
    ]
