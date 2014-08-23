require 'spec_helper'

describe API::API do
  include ApiHelpers

  let(:user) { create(:user) }
  let(:admin) { create(:admin) }
  let!(:hook) { create(:system_hook, url: "http://example.com") }

  before { stub_request(:post, hook.url) }

  describe "GET /hooks" do
    context "when no user" do
      it "should return authentication error" do
        get api("/hooks")
        response.status.should == 401
      end
    end

    context "when not an admin" do
      it "should return forbidden error" do
        get api("/hooks", user)
        response.status.should == 403
      end
    end

    context "when authenticated as admin" do
      it "should return an array of hooks" do
        get api("/hooks", admin)
        response.status.should == 200
        json_response.should be_an Array
        json_response.first['url'].should == hook.url
      end
    end
  end

  describe "POST /hooks" do
    it "should create new hook" do
      expect {
        post api("/hooks", admin), url: 'http://example.com'
      }.to change { SystemHook.count }.by(1)
    end

    it "should respond with 400 if url not given" do
      post api("/hooks", admin)
      response.status.should == 400
    end

    it "should not create new hook without url" do
      expect {
        post api("/hooks", admin)
      }.to_not change { SystemHook.count }
    end
  end

  describe "GET /hooks/:id" do
    it "should return hook by id" do
      get api("/hooks/#{hook.id}", admin)
      response.status.should == 200
      json_response['event_name'].should == 'project_create'
    end

    it "should return 404 on failure" do
      get api("/hooks/404", admin)
      response.status.should == 404
    end
  end

  describe "DELETE /hooks/:id" do
    it "should delete a hook" do
      expect {
        delete api("/hooks/#{hook.id}", admin)
      }.to change { SystemHook.count }.by(-1)
    end

    it "should return success if hook id not found" do
      delete api("/hooks/12345", admin)
      response.status.should == 200
    end
  end
end
