# == Schema Information
#
# Table name: notes
#
#  id            :integer          not null, primary key
#  note          :text
#  noteable_type :string(255)
#  author_id     :integer
#  created_at    :datetime         not null
#  updated_at    :datetime         not null
#  project_id    :integer
#  attachment    :string(255)
#  line_code     :string(255)
#  commit_id     :string(255)
#  noteable_id   :integer
#

require 'spec_helper'

describe Note do
  describe "Associations" do
    it { should belong_to(:project) }
    it { should belong_to(:noteable) }
    it { should belong_to(:author).class_name('User') }
  end

  describe "Mass assignment" do
    it { should_not allow_mass_assignment_of(:author) }
    it { should_not allow_mass_assignment_of(:author_id) }
  end

  describe "Validation" do
    it { should validate_presence_of(:note) }
    it { should validate_presence_of(:project) }
  end

  describe "Voting score" do
    let(:project) { create(:project) }

    it "recognizes a neutral note" do
      note = create(:votable_note, note: "This is not a +1 note")
      note.should_not be_upvote
      note.should_not be_downvote
    end

    it "recognizes a neutral emoji note" do
      note = build(:votable_note, note: "I would :+1: this, but I don't want to")
      note.should_not be_upvote
      note.should_not be_downvote
    end

    it "recognizes a +1 note" do
      note = create(:votable_note, note: "+1 for this")
      note.should be_upvote
    end

    it "recognizes a +1 emoji as a vote" do
      note = build(:votable_note, note: ":+1: for this")
      note.should be_upvote
    end

    it "recognizes a -1 note" do
      note = create(:votable_note, note: "-1 for this")
      note.should be_downvote
    end

    it "recognizes a -1 emoji as a vote" do
      note = build(:votable_note, note: ":-1: for this")
      note.should be_downvote
    end
  end

  let(:project) { create(:project) }
  let(:commit) { project.repository.commit }

  describe "Commit notes" do
    let!(:note) { create(:note_on_commit, note: "+1 from me") }
    let!(:commit) { note.noteable }

    it "should be accessible through #noteable" do
      note.commit_id.should == commit.id
      note.noteable.should be_a(Commit)
      note.noteable.should == commit
    end

    it "should save a valid note" do
      note.commit_id.should == commit.id
      note.noteable == commit
    end

    it "should be recognized by #for_commit?" do
      note.should be_for_commit
    end

    it "should not be votable" do
      note.should_not be_votable
    end
  end

  describe "Commit diff line notes" do
    let!(:note) { create(:note_on_commit_diff, note: "+1 from me") }
    let!(:commit) { note.noteable }

    it "should save a valid note" do
      note.commit_id.should == commit.id
      note.noteable.id.should == commit.id
    end

    it "should be recognized by #for_diff_line?" do
      note.should be_for_diff_line
    end

    it "should be recognized by #for_commit_diff_line?" do
      note.should be_for_commit_diff_line
    end

    it "should not be votable" do
      note.should_not be_votable
    end
  end

  describe "Issue notes" do
    let!(:note) { create(:note_on_issue, note: "+1 from me") }

    it "should not be votable" do
      note.should be_votable
    end
  end

  describe "Merge request notes" do
    let!(:note) { create(:note_on_merge_request, note: "+1 from me") }

    it "should not be votable" do
      note.should be_votable
    end
  end

  describe "Merge request diff line notes" do
    let!(:note) { create(:note_on_merge_request_diff, note: "+1 from me") }

    it "should not be votable" do
      note.should_not be_votable
    end
  end

  describe '#create_status_change_note' do
    let(:project)  { create(:project) }
    let(:thing)    { create(:issue, project: project) }
    let(:author)   { create(:user) }
    let(:status)   { 'new_status' }

    subject { Note.create_status_change_note(thing, author, status) }

    it 'creates and saves a Note' do
      should be_a Note
      subject.id.should_not be_nil
    end

    its(:noteable) { should == thing }
    its(:project)  { should == thing.project }
    its(:author)   { should == author }
    its(:note)     { should =~ /Status changed to #{status}/ }
  end

  describe :authorization do
    before do
      @p1 = create(:project)
      @p2 = create(:project)
      @u1 = create(:user)
      @u2 = create(:user)
      @u3 = create(:user)
      @abilities = Six.new
      @abilities << Ability
    end

    describe :read do
      before do
        @p1.users_projects.create(user: @u2, project_access: UsersProject::GUEST)
        @p2.users_projects.create(user: @u3, project_access: UsersProject::GUEST)
      end

      it { @abilities.allowed?(@u1, :read_note, @p1).should be_false }
      it { @abilities.allowed?(@u2, :read_note, @p1).should be_true }
      it { @abilities.allowed?(@u3, :read_note, @p1).should be_false }
    end

    describe :write do
      before do
        @p1.users_projects.create(user: @u2, project_access: UsersProject::DEVELOPER)
        @p2.users_projects.create(user: @u3, project_access: UsersProject::DEVELOPER)
      end

      it { @abilities.allowed?(@u1, :write_note, @p1).should be_false }
      it { @abilities.allowed?(@u2, :write_note, @p1).should be_true }
      it { @abilities.allowed?(@u3, :write_note, @p1).should be_false }
    end

    describe :admin do
      before do
        @p1.users_projects.create(user: @u1, project_access: UsersProject::REPORTER)
        @p1.users_projects.create(user: @u2, project_access: UsersProject::MASTER)
        @p2.users_projects.create(user: @u3, project_access: UsersProject::MASTER)
      end

      it { @abilities.allowed?(@u1, :admin_note, @p1).should be_false }
      it { @abilities.allowed?(@u2, :admin_note, @p1).should be_true }
      it { @abilities.allowed?(@u3, :admin_note, @p1).should be_false }
    end
  end
end
