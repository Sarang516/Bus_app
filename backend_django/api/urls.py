"""
api/urls.py  –  All URL patterns (trailing slash optional on every route)
"""
from django.urls import re_path

from api.views.auth      import LoginView, EmployeeProfileView, SetRoleView
from api.views.employees import EmployeeListView, EmployeeWithAllotmentView, EmployeeDetailView
from api.views.drivers   import DriverListView, DriverDetailView
from api.views.vehicles  import VehicleListView, VehicleDetailView
from api.views.mappings  import MappingListView, MappingDetailView
from api.views.routes    import RouteListView, RoutePickupsView
from api.views.requests  import (
    RequestListView, AdminAllotView,
    RequestDetailView, RequestActionView, RequestLogsView,
)
from api.views.dashboard import DashboardView, MyDashboardView
from api.views.uploads   import UploadView, DownloadView
from api.views.health    import HealthView, RootView

urlpatterns = [
    # ── Root & Health ─────────────────────────────────────────────────────────
    re_path(r"^$",                                              RootView.as_view(),                  name="root"),
    re_path(r"^api/health/?$",                                  HealthView.as_view(),                name="health"),

    # ── Authentication ────────────────────────────────────────────────────────
    re_path(r"^api/auth/login/?$",                              LoginView.as_view(),                 name="auth-login"),
    re_path(r"^api/auth/employee/(?P<pernr>[^/]+)/?$",          EmployeeProfileView.as_view(),       name="auth-employee"),
    re_path(r"^api/auth/admin/set-role/(?P<pernr>[^/]+)/?$",    SetRoleView.as_view(),               name="auth-set-role"),

    # ── Employees ─────────────────────────────────────────────────────────────
    re_path(r"^api/employees/with-allotment/?$",                EmployeeWithAllotmentView.as_view(),  name="employee-with-allotment"),
    re_path(r"^api/employees/(?P<pernr>[^/]+)/?$",              EmployeeDetailView.as_view(),        name="employee-detail"),
    re_path(r"^api/employees/?$",                               EmployeeListView.as_view(),          name="employee-list"),

    # ── Drivers ───────────────────────────────────────────────────────────────
    re_path(r"^api/drivers/(?P<driver_id>[^/]+)/?$",            DriverDetailView.as_view(),          name="driver-detail"),
    re_path(r"^api/drivers/?$",                                 DriverListView.as_view(),            name="driver-list"),

    # ── Vehicles ──────────────────────────────────────────────────────────────
    re_path(r"^api/vehicles/(?P<vehicle_no>[^/]+)/?$",          VehicleDetailView.as_view(),         name="vehicle-detail"),
    re_path(r"^api/vehicles/?$",                                VehicleListView.as_view(),           name="vehicle-list"),

    # ── Driver-Vehicle Mappings ───────────────────────────────────────────────
    re_path(r"^api/mappings/(?P<map_id>[^/]+)/?$",              MappingDetailView.as_view(),         name="mapping-detail"),
    re_path(r"^api/mappings/?$",                                MappingListView.as_view(),           name="mapping-list"),

    # ── Routes ────────────────────────────────────────────────────────────────
    re_path(r"^api/routes/(?P<seqnr>[^/]+)/pickups/?$",         RoutePickupsView.as_view(),          name="route-pickups"),
    re_path(r"^api/routes/?$",                                  RouteListView.as_view(),             name="route-list"),

    # ── Bus Requests ──────────────────────────────────────────────────────────
    re_path(r"^api/requests/admin-allot/?$",                    AdminAllotView.as_view(),            name="request-admin-allot"),
    re_path(r"^api/requests/(?P<reqid>[^/]+)/action/?$",        RequestActionView.as_view(),         name="request-action"),
    re_path(r"^api/requests/(?P<reqid>[^/]+)/logs/?$",          RequestLogsView.as_view(),           name="request-logs"),
    re_path(r"^api/requests/(?P<reqid>[^/]+)/?$",               RequestDetailView.as_view(),         name="request-detail"),
    re_path(r"^api/requests/?$",                                RequestListView.as_view(),           name="request-list"),

    # ── Dashboard ─────────────────────────────────────────────────────────────
    re_path(r"^api/dashboard/my/(?P<pernr>[^/]+)/?$",           MyDashboardView.as_view(),           name="dashboard-my"),
    re_path(r"^api/dashboard/?$",                               DashboardView.as_view(),             name="dashboard"),

    # ── Uploads ───────────────────────────────────────────────────────────────
    re_path(r"^api/uploads/(?P<file_id>[^/]+)/?$",              DownloadView.as_view(),              name="download"),
    re_path(r"^api/uploads/?$",                                 UploadView.as_view(),                name="upload"),
]
