class SnippetsController < ApplicationController
  before_filter :snippet, only: [:show, :edit, :destroy, :update, :raw]

  # Allow modify snippet
  before_filter :authorize_modify_snippet!, only: [:edit, :update]

  # Allow destroy snippet
  before_filter :authorize_admin_snippet!, only: [:destroy]

  respond_to :html

  def index
    @snippets = Snippet.public.fresh.non_expired.page(params[:page]).per(20)
  end

  def user_index
    @user = User.find_by_username(params[:username])
    @snippets = @user.snippets.fresh.non_expired

    if @user == current_user
      @snippets = case params[:scope]
                  when 'public' then
                    @snippets.public
                  when 'private' then
                    @snippets.private
                  else
                    @snippets
                  end
    else
      @snippets = @snippets.public
    end

    @snippets = @snippets.page(params[:page]).per(20)

    if @user == current_user
      render 'current_user_index'
    else
      render 'user_index'
    end
  end

  def new
    @snippet = PersonalSnippet.new
  end

  def create
    @snippet = PersonalSnippet.new(params[:personal_snippet])
    @snippet.author = current_user

    if @snippet.save
      redirect_to snippet_path(@snippet)
    else
      respond_with @snippet
    end
  end

  def edit
  end

  def update
    if @snippet.update_attributes(params[:personal_snippet])
      redirect_to snippet_path(@snippet)
    else
      respond_with @snippet
    end
  end

  def show
  end

  def destroy
    return access_denied! unless can?(current_user, :admin_personal_snippet, @snippet)

    @snippet.destroy

    redirect_to snippets_path
  end

  def raw
    send_data(
      @snippet.content,
      type: "text/plain",
      disposition: 'inline',
      filename: @snippet.file_name
    )
  end

  protected

  def snippet
    @snippet ||= PersonalSnippet.where('author_id = :user_id or private is false', user_id: current_user.id).find(params[:id])
  end

  def authorize_modify_snippet!
    return render_404 unless can?(current_user, :modify_personal_snippet, @snippet)
  end

  def authorize_admin_snippet!
    return render_404 unless can?(current_user, :admin_personal_snippet, @snippet)
  end
end
