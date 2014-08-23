module Emails
  module Notes
    def note_commit_email(recipient_id, note_id)
      @note = Note.find(note_id)
      @commit = @note.noteable
      @project = @note.project
      mail(to: recipient(recipient_id), subject: subject("note for commit #{@commit.short_id}", @commit.title))
    end

    def note_issue_email(recipient_id, note_id)
      @note = Note.find(note_id)
      @issue = @note.noteable
      @project = @note.project
      mail(to: recipient(recipient_id), subject: subject("note for issue ##{@issue.id}"))
    end

    def note_merge_request_email(recipient_id, note_id)
      @note = Note.find(note_id)
      @merge_request = @note.noteable
      @project = @note.project
      mail(to: recipient(recipient_id), subject: subject("note for merge request !#{@merge_request.id}"))
    end

    def note_wall_email(recipient_id, note_id)
      @note = Note.find(note_id)
      @project = @note.project
      mail(to: recipient(recipient_id), subject: subject("note on wall"))
    end
  end
end
