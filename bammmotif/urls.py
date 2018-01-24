from django.conf.urls import url
from django.conf.urls.static import static
from django.conf import settings
from . import views
from bammmotif.peng import views as peng_views
from bammmotif.bamm import views as bamm_views
from .mmcompare import views as compare_views
from .database import views as db_views

urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^home/', views.home, name='home'),
    url(r'^aboutBaMMmotif/', views.info, name='info'),
    url(r'^documentation/', views.documentation, name='documentation'),
    url(r'^download/', views.download, name='download'),
    url(r'^contact/', views.contact, name='contact'),
    url(r'^imprint/', views.imprint, name='imprint'),
    url(r'^job/submitted/', views.submitted, name='submitted'),
    # url(r'^job/bamm/$', views.run_bamm_view, name='run_bamm'),
    # url(r'^job/bamm/(?P<mode>\w+)/$', views.run_bamm_view, name='run_bamm'),
    url(r'^job/bamm/$', bamm_views.run_bamm_view, name='run_bamm'),
    url(r'^job/bamm/(?P<mode>\w+)/$', bamm_views.run_bamm_view, name='run_bamm'),
    url(r'^job/bamm_scan/$', views.run_bammscan_view, name='run_bamm_scan'),
    url(r'^job/bamm_scan/(?P<mode>\w+)/$', views.run_bammscan_view, name='run_bamm_scan'),
    url(r'^job/bamm_scan/(?P<mode>\w+)/(?P<pk>.*)/$', views.run_bammscan_view, name='run_bamm_scan'),
    url(r'^job/bamm_compare/$', compare_views.run_compare_view, name='run_compare'),
    url(r'^job/bamm_compare/(?P<mode>\w+)/$', compare_views.run_compare_view, name='run_compare'),
    url(r'^results/$', bamm_views.find_results, name='find_results'),
    url(r'^results/result_overview/$', bamm_views.result_overview, name='result_overview'),
    url(r'^results/(?P<pk>.*)/$', bamm_views.result_detail, name='result_detail'),
    #url(r'^results/$', views.find_results, name='find_results'),
    #url(r'^results/result_overview/$', views.result_overview, name='result_overview'),
    #url(r'^results/(?P<pk>.*)/$', views.result_detail, name='result_detail'),
    #url(r'^results/$', views.find_results, name='find_results'),
    #url(r'^results/result_overview/$', views.result_overview, name='result_overview'),
    #url(r'^results/(?P<pk>.*)/$', views.result_detail, name='result_detail'),
    url(r'^delete/(?P<pk>.*)/$', views.delete, name='delete'),
    url(r'^database/$', db_views.maindb, name='maindb'),
    url(r'^database/(?P<pk>.*)/$', db_views.db_detail, name='db_detail'),
    url(r'^job/run_peng_view/$', peng_views.run_peng_view, name='peng_predict'),
    url(r'^job/run_peng_view/(?P<mode>\w+)/$', peng_views.run_peng_view, name='peng_predict'),
    url(r'^peng_results/(?P<pk>.*)/$', peng_views.peng_result_detail, name='peng_result_detail'),
    url(r'^job/peng_to_bamm/(?P<pk>.*)/$', peng_views.peng_load_bamm, name='peng_to_bamm'),
    url(r'^job/peng_to_bamm/$', peng_views.peng_load_bamm, name='peng_to_bamm'),
    url(r'^peng_to_bamm_results/$', peng_views.find_peng_to_bamm_results, name='find_peng_to_bamm_result'),
    url(r'^peng_to_bamm_results/result_overview/(?P<pk>.*)/$', peng_views.peng_to_bamm_result_overview, name='peng_to_bamm_result_overview'),
    url(r'^peng_to_bamm_results/(?P<pk>.*)/$', peng_views.peng_to_bamm_result_detail, name='peng_to_bamm_result_detail'),
 ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
