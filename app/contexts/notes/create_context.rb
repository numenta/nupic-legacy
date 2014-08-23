module Notes
  class CreateContext < BaseContext
    def execute
      note = project.notes.new(params[:note])
      note.author = current_user
      note.save
      note
    end
  end
end
