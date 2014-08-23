# == Schema Information
#
# Table name: projects
#
#  id                     :integer          not null, primary key
#  name                   :string(255)
#  path                   :string(255)
#  description            :text
#  created_at             :datetime         not null
#  updated_at             :datetime         not null
#  creator_id             :integer
#  default_branch         :string(255)
#  issues_enabled         :boolean          default(TRUE), not null
#  wall_enabled           :boolean          default(TRUE), not null
#  merge_requests_enabled :boolean          default(TRUE), not null
#  wiki_enabled           :boolean          default(TRUE), not null
#  namespace_id           :integer
#  public                 :boolean          default(FALSE), not null
#  issues_tracker         :string(255)      default("gitlab"), not null
#  issues_tracker_id      :string(255)
#  snippets_enabled       :boolean          default(TRUE), not null
#  last_activity_at       :datetime
#

require 'spec_helper'

describe Project do
  describe "Associations" do
    it { should belong_to(:group) }
    it { should belong_to(:namespace) }
    it { should belong_to(:creator).class_name('User') }
    it { should have_many(:users) }
    it { should have_many(:events).dependent(:destroy) }
    it { should have_many(:merge_requests).dependent(:destroy) }
    it { should have_many(:issues).dependent(:destroy) }
    it { should have_many(:milestones).dependent(:destroy) }
    it { should have_many(:users_projects).dependent(:destroy) }
    it { should have_many(:notes).dependent(:destroy) }
    it { should have_many(:snippets).class_name('ProjectSnippet').dependent(:destroy) }
    it { should have_many(:deploy_keys_projects).dependent(:destroy) }
    it { should have_many(:deploy_keys) }
    it { should have_many(:hooks).dependent(:destroy) }
    it { should have_many(:protected_branches).dependent(:destroy) }
    it { should have_one(:forked_project_link).dependent(:destroy) }
  end

  describe "Mass assignment" do
    it { should_not allow_mass_assignment_of(:namespace_id) }
    it { should_not allow_mass_assignment_of(:creator_id) }
  end

  describe "Validation" do
    let!(:project) { create(:project) }

    it { should validate_presence_of(:name) }
    it { should validate_uniqueness_of(:name) }
    it { should ensure_length_of(:name).is_within(0..255) }

    it { should validate_presence_of(:path) }
    it { should validate_uniqueness_of(:path) }
    it { should ensure_length_of(:path).is_within(0..255) }
    it { should ensure_length_of(:description).is_within(0..2000) }
    it { should validate_presence_of(:creator) }
    it { should ensure_length_of(:issues_tracker_id).is_within(0..255) }

    it "should not allow new projects beyond user limits" do
      project.stub(:creator).and_return(double(can_create_project?: false, projects_limit: 1))
      project.should_not be_valid
      project.errors[:limit_reached].first.should match(/Your own projects limit is 1/)
    end
  end

  describe "Respond to" do
    it { should respond_to(:url_to_repo) }
    it { should respond_to(:repo_exists?) }
    it { should respond_to(:satellite) }
    it { should respond_to(:update_merge_requests) }
    it { should respond_to(:execute_hooks) }
    it { should respond_to(:transfer) }
    it { should respond_to(:name_with_namespace) }
    it { should respond_to(:namespace_owner) }
    it { should respond_to(:owner) }
    it { should respond_to(:path_with_namespace) }
  end

  it "should return valid url to repo" do
    project = Project.new(path: "somewhere")
    project.url_to_repo.should == Gitlab.config.gitlab_shell.ssh_path_prefix + "somewhere.git"
  end

  it "returns the full web URL for this repo" do
    project = Project.new(path: "somewhere")
    project.web_url.should == "#{Gitlab.config.gitlab.url}/somewhere"
  end

  describe "last_activity methods" do
    before { enable_observers }
    let(:project)    { create(:project) }
    let(:last_event) { double(created_at: Time.now) }

    describe "last_activity" do
      it "should alias last_activity to last_event"do
        project.stub(last_event: last_event)
        project.last_activity.should == last_event
      end
    end

    describe 'last_activity_date' do
      it 'returns the creation date of the project\'s last event if present' do
        last_activity_event = create(:event, project: project)
        project.last_activity_at.to_i.should == last_event.created_at.to_i
      end

      it 'returns the project\'s last update date if it has no events' do
        project.last_activity_date.should == project.updated_at
      end
    end
  end

  describe :update_merge_requests do
    let(:project) { create(:project_with_code) }

    before do
      @merge_request = create(:merge_request, project: project)
      @key = create(:key, user_id: project.owner.id)
    end

    it "should close merge request if last commit from source branch was pushed to target branch" do
      @merge_request.reloaded_commits
      @merge_request.last_commit.id.should == "bcf03b5de6c33f3869ef70d68cf06e679d1d7f9a"
      project.update_merge_requests("8716fc78f3c65bbf7bcf7b574febd583bc5d2812", "bcf03b5de6c33f3869ef70d68cf06e679d1d7f9a", "refs/heads/stable", @key.user)
      @merge_request.reload
      @merge_request.merged?.should be_true
    end

    it "should update merge request commits with new one if pushed to source branch" do
      @merge_request.last_commit.should == nil
      project.update_merge_requests("8716fc78f3c65bbf7bcf7b574febd583bc5d2812", "bcf03b5de6c33f3869ef70d68cf06e679d1d7f9a", "refs/heads/master", @key.user)
      @merge_request.reload
      @merge_request.last_commit.id.should == "bcf03b5de6c33f3869ef70d68cf06e679d1d7f9a"
    end
  end


  describe :find_with_namespace do
    context 'with namespace' do
      before do
        @group = create :group, name: 'gitlab'
        @project = create(:project, name: 'gitlab-ci', namespace: @group)
      end

      it { Project.find_with_namespace('gitlab/gitlab-ci').should == @project }
      it { Project.find_with_namespace('gitlab-ci').should be_nil }
    end

    context 'w/o namespace' do
      before do
        @project = create(:project, name: 'gitlab-ci')
      end

      it { Project.find_with_namespace('gitlab-ci').should == @project }
      it { Project.find_with_namespace('gitlab/gitlab-ci').should be_nil }
    end
  end

  describe :to_param do
    context 'with namespace' do
      before do
        @group = create :group, name: 'gitlab'
        @project = create(:project, name: 'gitlab-ci', namespace: @group)
      end

      it { @project.to_param.should == "gitlab/gitlab-ci" }
    end

    context 'w/o namespace' do
      before do
        @project = create(:project, name: 'gitlab-ci')
      end

      it { @project.to_param.should == "gitlab-ci" }
    end
  end

  describe :repository do
    let(:project) { create(:project) }

    it "should return valid repo" do
      project.repository.should be_kind_of(Repository)
    end
  end

  describe :issue_exists? do
    let(:project) { create(:project) }
    let(:existed_issue) { create(:issue, project: project) }
    let(:not_existed_issue) { create(:issue) }
    let(:ext_project) { create(:redmine_project) }

    it "should be true or if used internal tracker and issue exists" do
      project.issue_exists?(existed_issue.id).should be_true
    end

    it "should be false or if used internal tracker and issue not exists" do
      project.issue_exists?(not_existed_issue.id).should be_false
    end

    it "should always be true if used other tracker" do
      ext_project.issue_exists?(rand(100)).should be_true
    end
  end

  describe :used_default_issues_tracker? do
    let(:project) { create(:project) }
    let(:ext_project) { create(:redmine_project) }

    it "should be true if used internal tracker" do
      project.used_default_issues_tracker?.should be_true
    end

    it "should be false if used other tracker" do
      ext_project.used_default_issues_tracker?.should be_false
    end
  end

  describe :can_have_issues_tracker_id? do
    let(:project) { create(:project) }
    let(:ext_project) { create(:redmine_project) }

    it "should be true for projects with external issues tracker if issues enabled" do
      ext_project.can_have_issues_tracker_id?.should be_true
    end

    it "should be false for projects with internal issue tracker if issues enabled" do
      project.can_have_issues_tracker_id?.should be_false
    end

    it "should be always false if issues disbled" do
      project.issues_enabled = false
      ext_project.issues_enabled = false

      project.can_have_issues_tracker_id?.should be_false
      ext_project.can_have_issues_tracker_id?.should be_false
    end
  end

  describe :open_branches do
    let(:project) { create(:project_with_code) }

    before do
      project.protected_branches.create(name: 'master')
    end

    it { project.open_branches.map(&:name).should include('bootstrap') }
    it { project.open_branches.map(&:name).should_not include('master') }
  end
end
