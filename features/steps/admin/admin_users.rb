class AdminUsers < Spinach::FeatureSteps
  include SharedAuthentication
  include SharedPaths
  include SharedAdmin

  Then 'I should see all users' do
    User.all.each do |user|
      page.should have_content user.name
    end
  end

  And 'Click edit' do
    @user = User.first
    find("#edit_user_#{@user.id}").click
  end

  And 'Input non ascii char in username' do
    fill_in 'user_username', with: "\u3042\u3044"
  end

  And 'Click save' do
    click_button("Save")
  end

  Then 'See username error message' do
    within "#error_explanation" do
      page.should have_content "Username"
    end
  end

  And 'Not chenged form action url' do
    page.should have_selector %(form[action="/admin/users/#{@user.username}"])
  end
end
