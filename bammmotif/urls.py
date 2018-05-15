from django.conf.urls import url
from django.conf.urls.static import static
from django.conf import settings
from . import views
from .peng import views as peng_views
from .bamm import views as bamm_views
from .mmcompare import views as compare_views
from .database import views as db_views
from .bammscan import views as scan_views

urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^home/', views.home, name='home'),
    url(r'^aboutBaMMmotif/', views.info, name='info'),
    url(r'^documentation/', views.documentation, name='documentation'),
    url(r'^links/', views.links, name='links'),
    url(r'^contact/', views.contact, name='contact'),
    url(r'^imprint/', views.imprint, name='imprint'),
    url(r'^job/submitted/', views.submitted, name='submitted'),
    # scan
    url(r'^job/bamm_scan/$', scan_views.run_bammscan_view, name='run_bamm_scan'),
    url(r'^job/bamm_scan/(?P<mode>\w+)/$', scan_views.run_bammscan_view, name='run_bamm_scan'),
    url(r'^job/bamm_scan/(?P<mode>\w+)/(?P<pk>.*)/$', scan_views.run_bammscan_view, name='run_bamm_scan'),
    url(r'^scan_results/(?P<pk>.*)/$', scan_views.result_details, name='scan_results'),
    # compare
    url(r'^job/bamm_compare/$', compare_views.run_compare_view, name='run_compare'),
    url(r'^job/bamm_compare/(?P<mode>\w+)/$', compare_views.run_compare_view, name='run_compare'),
    url(r'^compare_results/(?P<pk>.*)/$', compare_views.result_detail, name='run_compare'),

    # denovo
    url(r'^job/seeding/$', peng_views.run_peng_view, name='peng_predict'),
    url(r'^job/seeding/(?P<mode>\w+)/$', peng_views.run_peng_view, name='peng_predict'),
    url(r'^seed_results/(?P<pk>.*)/$', peng_views.peng_results, name='peng_result_detail'),

    url(r'job/denovo/$', bamm_views.one_step_denovo, name='one_step_denovo'),
    url(r'job/denovo/(?P<mode>\w+)/$', bamm_views.one_step_denovo, name='one_step_denovo'),
    url(r'denovo_results/(?P<pk>.*)/$', bamm_views.denovo_results, name='denovo_results'),

    url(r'^job/refinement/(?P<pk>.*)/$', peng_views.run_refine, name='peng_to_bamm'),
    url(r'^refine_results/(?P<pk>.*)/$', peng_views.peng_to_bamm_result_detail, name='bamm_refinement'),

    # serve bed files for the genome browser
    url(r'^bedtrack/(?P<job_id>.*)/(?P<motif_no>.*)/$', views.serve_bed_file, name='serve_bed'),
    url(r'^redirect_genome_browser/$', views.run_genome_browser, name='run_genome_browser'),

    # database
    url(r'^database/$', db_views.maindb, name='maindb'),
    url(r'^database/browse/(?P<db_id>.*)/$', db_views.db_browse, name='db_browse'),
    url(r'^database/(?P<pk>.*)/$', db_views.db_detail, name='db_detail'),

    # find results
    url(r'^my_results/$', views.find_results, name='find_results'),
    url(r'^find_result/(?P<pk>.*)/$', views.find_results_by_id, name='find_results_by_id'),
    url(r'^peng_to_bamm_results/(?P<pk>.*)/$', peng_views.peng_to_bamm_result_detail, name='peng_to_bamm_result_detail'),
 ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
