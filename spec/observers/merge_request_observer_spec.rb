require 'spec_helper'

describe MergeRequestObserver do
  let(:some_user)      { create :user }
  let(:assignee)       { create :user }
  let(:author)         { create :user }
  let(:mr_mock)    { double(:merge_request, id: 42, assignee: assignee, author: author) }
  let(:assigned_mr)   { create(:merge_request, assignee: assignee, author: author) }
  let(:unassigned_mr) { create(:merge_request, author: author) }
  let(:closed_assigned_mr)   { create(:closed_merge_request, assignee: assignee, author: author) }
  let(:closed_unassigned_mr) { create(:closed_merge_request, author: author) }

  before { subject.stub(:current_user).and_return(some_user) }
  before { subject.stub(notification: mock('NotificationService').as_null_object) }
  before(:each) { enable_observers }


  subject { MergeRequestObserver.instance }

  describe '#after_create' do
    it 'trigger notification service' do
      subject.should_receive(:notification)
      subject.after_create(mr_mock)
    end
  end

  context '#after_update' do
    before(:each) do
      mr_mock.stub(:is_being_reassigned?).and_return(false)
    end

    it 'is called when a merge request is changed' do
      changed = create(:merge_request, project: create(:project))
      subject.should_receive(:after_update)

      MergeRequest.observers.enable :merge_request_observer do
        changed.title = 'I changed'
        changed.save
      end
    end

    context 'a notification' do
      it 'is sent if the merge request is being reassigned' do
        mr_mock.should_receive(:is_being_reassigned?).and_return(true)
        subject.should_receive(:notification)

        subject.after_update(mr_mock)
      end

      it 'is not sent if the merge request is not being reassigned' do
        mr_mock.should_receive(:is_being_reassigned?).and_return(false)
        subject.should_not_receive(:notification)

        subject.after_update(mr_mock)
      end
    end
  end

  context '#after_close' do
    context 'a status "closed"' do
      it 'note is created if the merge request is being closed' do
        Note.should_receive(:create_status_change_note).with(assigned_mr, some_user, 'closed')

        assigned_mr.close
      end

      it 'notification is delivered only to author if the merge request is being closed' do
        Note.should_receive(:create_status_change_note).with(unassigned_mr, some_user, 'closed')

        unassigned_mr.close
      end
    end
  end

  context '#after_reopen' do
    context 'a status "reopened"' do
      it 'note is created if the merge request is being reopened' do
        Note.should_receive(:create_status_change_note).with(closed_assigned_mr, some_user, 'reopened')

        closed_assigned_mr.reopen
      end

      it 'notification is delivered only to author if the merge request is being reopened' do
        Note.should_receive(:create_status_change_note).with(closed_unassigned_mr, some_user, 'reopened')

        closed_unassigned_mr.reopen
      end
    end
  end
end
