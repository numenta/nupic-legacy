require "spec_helper"

describe API::API do
  include ApiHelpers

  let(:user) { create(:user ) }
  let!(:project) { create(:project_with_code, creator_id: user.id) }
  let!(:merge_request) { create(:merge_request, author: user, assignee: user, project: project, title: "Test") }
  before { project.team << [user, :reporters] }

  describe "GET /projects/:id/merge_requests" do
    context "when unauthenticated" do
      it "should return authentication error" do
        get api("/projects/#{project.id}/merge_requests")
        response.status.should == 401
      end
    end

    context "when authenticated" do
      it "should return an array of merge_requests" do
        get api("/projects/#{project.id}/merge_requests", user)
        response.status.should == 200
        json_response.should be_an Array
        json_response.first['title'].should == merge_request.title
      end
    end
  end

  describe "GET /projects/:id/merge_request/:merge_request_id" do
    it "should return merge_request" do
      get api("/projects/#{project.id}/merge_request/#{merge_request.id}", user)
      response.status.should == 200
      json_response['title'].should == merge_request.title
    end

    it "should return a 404 error if merge_request_id not found" do
      get api("/projects/#{project.id}/merge_request/999", user)
      response.status.should == 404
    end
  end

  describe "POST /projects/:id/merge_requests" do
    it "should return merge_request" do
      post api("/projects/#{project.id}/merge_requests", user),
        title: 'Test merge_request', source_branch: "stable", target_branch: "master", author: user
      response.status.should == 201
      json_response['title'].should == 'Test merge_request'
    end

    it "should return 422 when source_branch equals target_branch" do
      post api("/projects/#{project.id}/merge_requests", user),
        title: "Test merge_request", source_branch: "master", target_branch: "master", author: user
      response.status.should == 422
    end

    it "should return 400 when source_branch is missing" do
      post api("/projects/#{project.id}/merge_requests", user),
        title: "Test merge_request", target_branch: "master", author: user
      response.status.should == 400
    end

    it "should return 400 when target_branch is missing" do
      post api("/projects/#{project.id}/merge_requests", user),
        title: "Test merge_request", source_branch: "stable", author: user
      response.status.should == 400
    end

    it "should return 400 when title is missing" do
      post api("/projects/#{project.id}/merge_requests", user),
        target_branch: 'master', source_branch: 'stable'
      response.status.should == 400
    end
  end

  describe "PUT /projects/:id/merge_request/:merge_request_id to close MR" do
    it "should return merge_request" do
      put api("/projects/#{project.id}/merge_request/#{merge_request.id}", user), state_event: "close"
      response.status.should == 200
      json_response['state'].should == 'closed'
    end
  end

  describe "PUT /projects/:id/merge_request/:merge_request_id to merge MR" do
    it "should return merge_request" do
      put api("/projects/#{project.id}/merge_request/#{merge_request.id}", user), state_event: "merge"
      response.status.should == 200
      json_response['state'].should == 'merged'
    end
  end

  describe "PUT /projects/:id/merge_request/:merge_request_id" do
    it "should return merge_request" do
      put api("/projects/#{project.id}/merge_request/#{merge_request.id}", user), title: "New title"
      response.status.should == 200
      json_response['title'].should == 'New title'
    end

    it "should return 422 when source_branch and target_branch are renamed the same" do
      put api("/projects/#{project.id}/merge_request/#{merge_request.id}", user),
        source_branch: "master", target_branch: "master"
      response.status.should == 422
    end

    it "should return merge_request with renamed target_branch" do
      put api("/projects/#{project.id}/merge_request/#{merge_request.id}", user), target_branch: "test"
      response.status.should == 200
      json_response['target_branch'].should == 'test'
    end
  end

  describe "POST /projects/:id/merge_request/:merge_request_id/comments" do
    it "should return comment" do
      post api("/projects/#{project.id}/merge_request/#{merge_request.id}/comments", user), note: "My comment"
      response.status.should == 201
      json_response['note'].should == 'My comment'
    end

    it "should return 400 if note is missing" do
      post api("/projects/#{project.id}/merge_request/#{merge_request.id}/comments", user)
      response.status.should == 400
    end

    it "should return 404 if note is attached to non existent merge request" do
      post api("/projects/#{project.id}/merge_request/111/comments", user), note: "My comment"
      response.status.should == 404
    end
  end

end
