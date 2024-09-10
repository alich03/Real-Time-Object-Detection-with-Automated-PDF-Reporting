from django.urls import path,include
from kona_detection import views
from .views import SignupView, LoginView, LogoutView

urlpatterns = [

    path('video/', views.run_model_video, name='run_model_video'),
    # path('', views.run_model_live, name='run_model_live'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    
]
