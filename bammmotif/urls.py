from django.conf.urls import url
from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from . import views
from .peng import views as peng_views
from .bamm import views as bamm_views
from .mmcompare import views as compare_views
from .database import views as db_views
from .bammscan import views as scan_views

urlpatterns = [
    path('', views.home, name='home'),
    path('home/', views.home, name='home'),
    path('aboutBaMMmotif/', views.info, name='info'),
    path('documentation/', views.documentation, name='documentation'),
    path('links/', views.links, name='links'),
    path('contact/', views.contact, name='contact'),
    path('imprint/', views.imprint, name='imprint'),
    path('job/submitted/', views.submitted, name='submitted'),

    # scan
    path('job/bamm_scan/', scan_views.run_bammscan_view, name='run_bamm_scan'),
    path('job/bamm_scan/<mode>/', scan_views.run_bammscan_view, name='run_bamm_scan'),
    path('job/bamm_scan/<mode>/<pk>/', scan_views.run_bammscan_view, name='run_bamm_scan'),
    path('scan_results/<uuid:pk>/', scan_views.result_details, name='scan_results'),

    # compare
    path('job/bamm_compare/', compare_views.run_compare_view, name='run_compare'),
    path('job/bamm_compare/<mode>)/', compare_views.run_compare_view, name='run_compare'),
    path('compare_results/<uuid:pk>/', compare_views.result_detail, name='run_compare'),

    # denovo
    path('job/seeding/', peng_views.run_peng_view, name='peng_predict'),
    path('job/seeding/<mode>/', peng_views.run_peng_view, name='peng_predict'),
    path('seed_results/<uuid:pk>/', peng_views.peng_results, name='peng_result_detail'),

    path('job/denovo/', bamm_views.one_step_denovo, name='one_step_denovo'),
    path('job/denovo/<mode>/', bamm_views.one_step_denovo, name='one_step_denovo'),
    path('denovo_results/<uuid:pk>/', bamm_views.denovo_results, name='denovo_results'),

    path('job/refinement/<uuid:pk>/', peng_views.run_refine, name='peng_to_bamm'),
    path('refine_results/<uuid:pk>/', peng_views.peng_to_bamm_result_detail, name='bamm_refinement'),

    # serve bed files for the genome browser
    path('bedtrack/<job_id>/<motif_no>/', views.serve_bed_file, name='serve_bed'),
    path('redirect_genome_browser/', views.run_genome_browser, name='run_genome_browser'),

    # database
    path('database/', db_views.maindb, name='maindb'),
    path('database/browse/<db_id>/', db_views.db_browse, name='db_browse'),
    path('database/<pk>/', db_views.db_detail, name='db_detail'),

    # find results
    path('my_results/', views.find_results, name='find_results'),
    path('my_results/csv/', views.serve_job_csv, name='download_job_list_csv'),
    path('find_result/<uuid:pk>/', views.find_results_by_id, name='find_results_by_id'),
    path('find_result/<uuid:pk>/status/', views.get_job_status, name='get_job_status'),
    path('peng_to_bamm_results/<uuid:pk>/', peng_views.peng_to_bamm_result_detail, name='peng_to_bamm_result_detail'),
 ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
