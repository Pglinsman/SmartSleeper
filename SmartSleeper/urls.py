"""SmartSleeper URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include, url

import django.contrib.auth.views
import SmartSleeperApp.views

urlpatterns = [
    url(r'^$', SmartSleeperApp.views.home, name='home'),
    url(r'^alarm$', SmartSleeperApp.views.alarm, name='alarm'),
    url(r'^analytics$', SmartSleeperApp.views.analytics, name='analytics'),
    url(r'^settings$', SmartSleeperApp.views.settings, name='settings'),
    url(r'^led-off$', SmartSleeperApp.views.led_off, name='led-off'),
    url(r'^led-on$', SmartSleeperApp.views.led_on, name='led-on'),
    url(r'^check-alarm$', SmartSleeperApp.views.check_alarm, name='check-alarm'),
    url(r'^add-alarm$', SmartSleeperApp.views.add_alarm, name='add-alarm'),
    url(r'^delete-alarm/(?P<item_id>\d+)$', SmartSleeperApp.views.delete_alarm, name='delete-alarm'),
    url(r'^change-tolerance$', SmartSleeperApp.views.change_tolerance, name='change-tolerance'),
]
