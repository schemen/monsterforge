from django.urls import path
from . import views
from django.conf.urls import include

urlpatterns = [
    path('', views.index, name='index'),
    #path('creatures/', views.CreatureListView.as_view(), name='creatures'),
    path('creature/<int:pk>', views.CreatureDetailView.as_view(), name='creature-detail'),
    path('creatures/', views.CreatureByUserListView.as_view(), name='creatures'),
    path('bestiary/<int:pk>', views.BestiaryDetailView.as_view(), name='bestiary-detail'),
    path('bestiaries/', views.BestiaryListView.as_view(), name='bestiaries'),
]

# creature management
urlpatterns += [
    path('creature/create/', views.CreatureCreate.as_view(), name='creature-create'),
    path('creature/<int:pk>/update/', views.CreatureUpdate.as_view(), name='creature-update'),
    path('creature/<int:pk>/delete/', views.CreatureDelete.as_view(), name='creature-delete'),
    path('creature/upload/', views.json_upload, name='creature-upload'),
    path('creatures/delete-all/', views.CreatureAllDelete.as_view(), name='creature-delete-all'),
]

# bestiary management
urlpatterns += [
    path('bestiary/create/', views.BestiaryCreate.as_view(), name='bestiary-create'),
    path('bestiary/ddbcreate/', views.create_ddb_enc_bestiary, name='ddb-enc-bestiary-create'),
    path('bestiary/<int:pk>/update/', views.BestiaryUpdate.as_view(), name='bestiary-update'),
    path('bestiary/<int:pk>/delete/', views.BestiaryDelete.as_view(), name='bestiary-delete'),
    path('bestiary/<int:pk>/link/', views.bestiary_link, name='bestiary-link'),
    path('bestiary/<int:pk>/<int:ci>/unlink/', views.bestiary_unlink, name='bestiary-unlink'),
    path('bestiary/<int:pk>/unlink/', views.bestiary_unlink, name='bestiary-unlink'),
    path('bestiary/<int:pk>/print/', views.bestiary_print, name='bestiary-print'),
    #path('bestiary/<int:pk>/serve/', views.bestiary_serve_file, name='bestiary-serve')
]

# patreon
urlpatterns += [
    path('patreon/', views.patreon, name='patreon'),
]
