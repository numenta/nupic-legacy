require "spec_helper"

describe NotificationsController do
  describe "routing" do
    it "routes to #show" do
      get("/profile/notifications").should route_to("notifications#show")
    end

    it "routes to #update" do
      put("/profile/notifications").should route_to("notifications#update")
    end
  end
end
