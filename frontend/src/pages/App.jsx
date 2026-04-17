// src/pages/App.jsx
import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { Layout } from "../components/Layout";
import Login from "./Login";
import Dashboard from "./Dashboard";
import NewRequest from "./NewRequest";
import RequestList from "./RequestList";
import DriverMaster from "./DriverMaster";
import VehicleMaster from "./VehicleMaster";
import DriverVehicleMap from "./DriverVehicleMap";
import EmployeeMaster from "./EmployeeMaster";
import EmployeeAllotmentList from "./EmployeeAllotmentList";
import Profile from "./Profile";

function AppInner() {
  const { user } = useAuth();
  const [page, setPage]           = useState("dashboard");
  const [pageFilter, setPageFilter] = useState("");

  if (!user) return <Login />;

  const navigate = (pageName, filter = "") => {
    setPage(pageName);
    setPageFilter(filter);
  };

  const renderPage = () => {
    switch (page) {
      case "dashboard":
        return <Dashboard setPage={navigate} />;
      case "new-request":
        return <NewRequest setPage={navigate} />;
      case "my-requests":
        return <RequestList title="My Requests" initialStatus={pageFilter} />;
      case "pending-approval":
        return <RequestList title="Pending Approval" viewRole="APPROVER" initialStatus={pageFilter} />;
      case "all-requests":
        return <RequestList title="All Requests" viewRole="APPROVER" initialStatus={pageFilter} />;
      case "vehicle-allotment":
        return <RequestList title="Vehicle Allotment" viewRole="TRANSPORT_ADMIN" initialStatus={pageFilter} />;
      case "driver-master":
        return <DriverMaster />;
      case "vehicle-master":
        return <VehicleMaster />;
      case "driver-vehicle-map":
        return <DriverVehicleMap />;
      case "employee-master":
        return <EmployeeMaster />;
      case "employee-allotment":
        return <EmployeeAllotmentList />;
      case "profile":
        return <Profile />;
      default:
        return <Dashboard setPage={navigate} />;
    }
  };

  return (
    <Layout page={page} setPage={navigate}>
      {renderPage()}
    </Layout>
  );
}

export default function App() {
  return <AppInner />;
}
